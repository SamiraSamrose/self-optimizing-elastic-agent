import re
import json
from dataclasses import dataclass, field
from elasticsearch import Elasticsearch
from config.settings import (
    ELASTICSEARCH_URL,
    ELASTICSEARCH_API_KEY,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
    MONITORING_CLUSTER_URL,
    MONITORING_API_KEY,
    INDEX_METADATA_INDEX,
)


@dataclass
class DiagnosisResult:
    """Structured finding for a single slow query statement."""
    statement: str
    avg_duration_ns: float
    count: int
    anti_patterns: list[str] = field(default_factory=list)
    affected_fields: list[str] = field(default_factory=list)
    field_types: dict[str, str] = field(default_factory=dict)
    severity: str = "low"           # low | medium | high | critical
    recommended_searches: list[str] = field(default_factory=list)
    raw_exception: str = ""

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "avg_duration_ns": self.avg_duration_ns,
            "count": self.count,
            "anti_patterns": self.anti_patterns,
            "affected_fields": self.affected_fields,
            "field_types": self.field_types,
            "severity": self.severity,
            "recommended_searches": self.recommended_searches,
            "raw_exception": self.raw_exception,
        }


def _get_monitoring_client() -> Elasticsearch:
    if MONITORING_API_KEY:
        return Elasticsearch(MONITORING_CLUSTER_URL, api_key=MONITORING_API_KEY)
    return Elasticsearch(
        MONITORING_CLUSTER_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


def _get_production_client() -> Elasticsearch:
    if ELASTICSEARCH_API_KEY:
        return Elasticsearch(ELASTICSEARCH_URL, api_key=ELASTICSEARCH_API_KEY)
    return Elasticsearch(
        ELASTICSEARCH_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


# ── Field cardinality helpers ──────────────────────────────────────────────────

def _fetch_field_type_from_metadata(index_name: str, field_name: str) -> str:
    """
    Looks up the field type from the index-metadata index so diagnosis
    does not need to hit the production _mapping API on every cycle.
    """
    monitoring_client = _get_monitoring_client()
    try:
        resp = monitoring_client.search(
            index=INDEX_METADATA_INDEX,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"index_name": index_name}},
                            {"term": {"field_name": field_name}},
                        ]
                    }
                },
                "size": 1,
                "_source": ["field_type"],
            }
        )
        hits = resp["hits"]["hits"]
        if hits:
            return hits[0]["_source"].get("field_type", "unknown")
    except Exception:
        pass
    return "unknown"


def _estimate_cardinality(index_name: str, field_name: str) -> int:
    """
    Runs a terms aggregation with size=1 to get the doc_count_error_upper_bound,
    which is a proxy for whether the field has high cardinality.
    High cardinality is defined as > 1000 unique values.
    """
    prod_client = _get_production_client()
    try:
        resp = prod_client.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "cardinality_check": {
                        "cardinality": {
                            "field": field_name,
                            "precision_threshold": 1000,
                        }
                    }
                }
            }
        )
        return resp["aggregations"]["cardinality_check"]["value"]
    except Exception:
        return 0


# ── Anti-pattern detectors ─────────────────────────────────────────────────────

_WILDCARD_PATTERN = re.compile(
    r'"wildcard"\s*:\s*\{[^}]*"([^"]+)"\s*:\s*\{?[^}]*"value"\s*:\s*"([^"]+)"',
    re.IGNORECASE,
)
_LEADING_WILDCARD_VALUE = re.compile(r'^\*|^\?')
_CIRCUIT_BREAKER_PATTERN = re.compile(
    r'CircuitBreakingException|circuit_breaking_exception|Data too large',
    re.IGNORECASE,
)
_UNBOUNDED_TERMS_AGG = re.compile(
    r'"terms"\s*:\s*\{(?:(?!"size").)*\}',
    re.DOTALL,
)
_NESTED_QUERY_DEPTH = re.compile(r'"nested"', re.IGNORECASE)
_SCRIPT_QUERY = re.compile(r'"script"\s*:\s*\{', re.IGNORECASE)
_FUZZY_ON_LARGE = re.compile(r'"fuzzy"\s*:\s*\{', re.IGNORECASE)
_REGEXP_QUERY = re.compile(r'"regexp"\s*:\s*\{', re.IGNORECASE)


def _detect_wildcard_anti_patterns(
    statement: str,
    index_name: str,
) -> tuple[list[str], list[str], dict[str, str], list[str]]:
    """
    Detects wildcard query anti-patterns in the query statement.
    Returns (anti_patterns, affected_fields, field_types, recommended_searches).
    """
    anti_patterns = []
    affected_fields = []
    field_types = {}
    recommended_searches = []

    # Try to parse the statement as JSON (ES query DSL)
    try:
        query_body = json.loads(statement)
        statement_str = json.dumps(query_body)
    except (json.JSONDecodeError, TypeError):
        statement_str = str(statement)

    # Detect wildcard clause
    for match in _WILDCARD_PATTERN.finditer(statement_str):
        field_name = match.group(1)
        value = match.group(2)

        field_type = _fetch_field_type_from_metadata(index_name, field_name)
        cardinality = _estimate_cardinality(index_name, field_name)

        affected_fields.append(field_name)
        field_types[field_name] = field_type

        if _LEADING_WILDCARD_VALUE.match(value):
            anti_patterns.append(
                f"Leading wildcard '*{value}' on field '{field_name}' "
                f"(type={field_type}) prevents index use and causes full shard scan."
            )
            recommended_searches.append(
                f"Optimizing leading wildcard queries in Elasticsearch field type {field_type}"
            )

        if cardinality > 1000:
            anti_patterns.append(
                f"Wildcard query on high-cardinality field '{field_name}' "
                f"(~{cardinality} unique values, type={field_type}). "
                f"Consider switching to 'wildcard' field type or n-gram tokenizer."
            )
            recommended_searches.append(
                "Optimizing wildcard queries in Elastic n-grams wildcard field type"
            )

        if field_type in ("keyword", "text") and cardinality > 10000:
            anti_patterns.append(
                f"Field '{field_name}' is type '{field_type}' with {cardinality} unique values. "
                "A dedicated 'wildcard' field type would store a trigram index for faster matching."
            )
            recommended_searches.append(
                "Elasticsearch wildcard field type trigram optimization"
            )

    return anti_patterns, affected_fields, field_types, recommended_searches


def _detect_circuit_breaker(statement: str) -> tuple[list[str], list[str]]:
    """
    Detects CircuitBreakerException references in slowlog entries.
    Returns (anti_patterns, recommended_searches).
    """
    anti_patterns = []
    recommended_searches = []
    if _CIRCUIT_BREAKER_PATTERN.search(statement):
        anti_patterns.append(
            "CircuitBreakerException detected. The JVM heap is exhausted during this query. "
            "The 'indices.breaker.total.limit' setting may need adjustment, or the query "
            "is fetching too much data into memory."
        )
        recommended_searches.append(
            "Elasticsearch indices.breaker.total.limit CircuitBreakerException configuration"
        )
    return anti_patterns, recommended_searches


def _detect_unbounded_aggregations(statement: str) -> tuple[list[str], list[str]]:
    """
    Detects terms aggregations without an explicit size cap, which can
    pull millions of bucket results into the JVM heap.
    """
    anti_patterns = []
    recommended_searches = []
    if _UNBOUNDED_TERMS_AGG.search(statement):
        anti_patterns.append(
            "Terms aggregation detected without an explicit 'size' limit. "
            "This can cause excessive heap usage and trigger circuit breakers."
        )
        recommended_searches.append(
            "Elasticsearch terms aggregation size limit performance best practices"
        )
    return anti_patterns, recommended_searches


def _detect_deep_nesting(statement: str) -> tuple[list[str], list[str]]:
    """
    Detects queries with multiple nested clauses, which require
    separate document joins and bypass the primary inverted index.
    """
    anti_patterns = []
    recommended_searches = []
    nesting_depth = len(_NESTED_QUERY_DEPTH.findall(statement))
    if nesting_depth >= 2:
        anti_patterns.append(
            f"Query contains {nesting_depth} nested clauses. Deep nesting triggers "
            "child document joins on each shard, causing significant latency."
        )
        recommended_searches.append(
            "Elasticsearch nested query performance alternatives flattened object"
        )
    return anti_patterns, recommended_searches


def _detect_script_queries(statement: str) -> tuple[list[str], list[str]]:
    """
    Detects Painless script queries, which run per-document and cannot
    use the inverted index.
    """
    anti_patterns = []
    recommended_searches = []
    if _SCRIPT_QUERY.search(statement):
        anti_patterns.append(
            "Script query detected. Script queries execute per document and bypass "
            "all index structures. Consider pre-computing the scripted value as a "
            "stored field or runtime field with caching."
        )
        recommended_searches.append(
            "Elasticsearch script query performance runtime field stored field alternative"
        )
    return anti_patterns, recommended_searches


def _detect_regexp_queries(statement: str) -> tuple[list[str], list[str]]:
    """
    Detects regexp queries, which like wildcards can cause full shard scans.
    """
    anti_patterns = []
    recommended_searches = []
    if _REGEXP_QUERY.search(statement):
        anti_patterns.append(
            "Regexp query detected. Regexp queries can match millions of terms in the "
            "inverted index. Consider switching to a dedicated 'wildcard' field type "
            "or indexing a pre-normalized keyword for filtering."
        )
        recommended_searches.append(
            "Elasticsearch regexp query performance wildcard field type alternative"
        )
    return anti_patterns, recommended_searches


def _compute_severity(anti_patterns: list[str], avg_duration_ns: float) -> str:
    """
    Assigns a severity level based on the number of anti-patterns
    found and the average query duration.
    """
    avg_ms = avg_duration_ns / 1_000_000
    if not anti_patterns:
        return "low"
    if "CircuitBreakerException" in " ".join(anti_patterns) or avg_ms > 10_000:
        return "critical"
    if avg_ms > 5_000 or len(anti_patterns) >= 3:
        return "high"
    if avg_ms > 2_000 or len(anti_patterns) >= 2:
        return "medium"
    return "low"


# ── Public API ─────────────────────────────────────────────────────────────────

def diagnose_slow_queries(
    slow_query_result: dict,
    index_name: str = "*",
) -> list[DiagnosisResult]:
    """
    Takes the output of fetch_slowest_queries and
    runs every anti-pattern detector against each query statement.

    Returns a list of DiagnosisResult objects ordered by severity (critical first).

    Args:
        slow_query_result: The dict returned by tools/esql_tool.py::fetch_slowest_queries.
        index_name: The index the queries were running against. Used for field type
                    and cardinality lookups.
    """
    columns = slow_query_result.get("columns", [])
    rows = slow_query_result.get("rows", [])

    # Map column names to positions
    col_idx = {name: i for i, name in enumerate(columns)}
    stmt_idx = col_idx.get("statement", 2)
    dur_idx = col_idx.get("avg_duration", 0)
    cnt_idx = col_idx.get("count", 1)

    findings: list[DiagnosisResult] = []

    for row in rows:
        statement = str(row[stmt_idx]) if stmt_idx < len(row) else ""
        avg_duration = float(row[dur_idx]) if dur_idx < len(row) else 0.0
        count = int(row[cnt_idx]) if cnt_idx < len(row) else 0

        all_anti_patterns: list[str] = []
        all_affected_fields: list[str] = []
        all_field_types: dict[str, str] = {}
        all_recommended_searches: list[str] = []

        # all detectors
        ap, af, ft, rs = _detect_wildcard_anti_patterns(statement, index_name)
        all_anti_patterns.extend(ap)
        all_affected_fields.extend(af)
        all_field_types.update(ft)
        all_recommended_searches.extend(rs)

        ap, rs = _detect_circuit_breaker(statement)
        all_anti_patterns.extend(ap)
        all_recommended_searches.extend(rs)

        ap, rs = _detect_unbounded_aggregations(statement)
        all_anti_patterns.extend(ap)
        all_recommended_searches.extend(rs)

        ap, rs = _detect_deep_nesting(statement)
        all_anti_patterns.extend(ap)
        all_recommended_searches.extend(rs)

        ap, rs = _detect_script_queries(statement)
        all_anti_patterns.extend(ap)
        all_recommended_searches.extend(rs)

        ap, rs = _detect_regexp_queries(statement)
        all_anti_patterns.extend(ap)
        all_recommended_searches.extend(rs)

        severity = _compute_severity(all_anti_patterns, avg_duration)

        findings.append(DiagnosisResult(
            statement=statement,
            avg_duration_ns=avg_duration,
            count=count,
            anti_patterns=all_anti_patterns,
            affected_fields=list(set(all_affected_fields)),
            field_types=all_field_types,
            severity=severity,
            recommended_searches=list(set(all_recommended_searches)),
        ))

    # Sort: critical first, then by avg_duration descending
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_rank[f.severity], -f.avg_duration_ns))

    return findings


def build_diagnosis_context(findings: list[DiagnosisResult]) -> str:
    """
    Formats the diagnosis results into a structured text block
    that is injected into the reasoning model's context so it can immediately
    research the most severe anti-pattern using the Knowledge Tool.
    """
    if not findings:
        return "Diagnosis complete. No performance anti-patterns detected in the sampled queries."

    lines = ["Diagnosis results (ordered by severity):"]
    for i, finding in enumerate(findings, start=1):
        lines.append(f"\n[{i}] Statement: {finding.statement[:200]}")
        lines.append(f"    Avg Duration: {finding.avg_duration_ns / 1_000_000:.1f}ms | Count: {finding.count} | Severity: {finding.severity.upper()}")
        if finding.anti_patterns:
            lines.append("    Anti-Patterns Detected:")
            for ap in finding.anti_patterns:
                lines.append(f"      - {ap}")
        if finding.affected_fields:
            lines.append(f"    Affected Fields: {', '.join(finding.affected_fields)}")
            for field, ftype in finding.field_types.items():
                lines.append(f"      {field} → type: {ftype}")
        if finding.recommended_searches:
            lines.append("    Recommended Knowledge Tool Queries:")
            for rs in finding.recommended_searches:
                lines.append(f"      - \"{rs}\"")

    return "\n".join(lines)
