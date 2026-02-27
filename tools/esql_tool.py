from datetime import datetime, timezone, timedelta
from elasticsearch import Elasticsearch
from config.settings import (
    MONITORING_CLUSTER_URL,
    MONITORING_API_KEY,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
    SLOWLOG_INDEX_PATTERN,
    NODE_METRICS_INDEX_PATTERN,
    INDEX_METADATA_INDEX,
    TOP_SLOW_QUERIES_LIMIT,
    SLOW_QUERY_MIN_COUNT,
)


def _get_monitoring_client() -> Elasticsearch:
    """Creates an Elasticsearch client pointed at the monitoring cluster."""
    if MONITORING_API_KEY:
        return Elasticsearch(
            MONITORING_CLUSTER_URL,
            api_key=MONITORING_API_KEY,
        )
    return Elasticsearch(
        MONITORING_CLUSTER_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


def run_esql_query(query: str, index_pattern: str, time_range_hours: int = 1) -> dict:
    """
    Executes an ES|QL query against the monitoring cluster.

    Args:
        query: The ES|QL query string.
        index_pattern: The index pattern to scope the query to.
        time_range_hours: How many hours back to look.

    Returns:
        A dict with 'columns', 'rows', and 'meta' keys.
    """
    client = _get_monitoring_client()
    result = client.esql.query(body={"query": query})
    columns = [col["name"] for col in result.get("columns", [])]
    rows = result.get("values", [])
    return {
        "columns": columns,
        "rows": rows,
        "meta": {
            "index_pattern": index_pattern,
            "time_range_hours": time_range_hours,
            "row_count": len(rows),
        }
    }


def build_slowest_queries_esql(time_range_hours: int = 1) -> str:
    """
    Builds the ES|QL query that finds the top N slowest query
    statements from the slowlog in the last `time_range_hours`.

    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=time_range_hours)).isoformat()

    query = f"""
FROM {SLOWLOG_INDEX_PATTERN}
| WHERE @timestamp >= "{cutoff}"
| STATS avg_duration = AVG(event.duration), count = COUNT() BY statement
| WHERE count > {SLOW_QUERY_MIN_COUNT}
| SORT avg_duration DESC
| LIMIT {TOP_SLOW_QUERIES_LIMIT}
""".strip()
    return query


def fetch_slowest_queries(time_range_hours: int = 1) -> dict:
    """
    Fetches the top N slowest queries from the slowlog index.
    Called by the orchestrator at the start of each optimization cycle.
    """
    query = build_slowest_queries_esql(time_range_hours)
    return run_esql_query(query, SLOWLOG_INDEX_PATTERN, time_range_hours)


def fetch_node_metrics(time_range_hours: int = 1) -> dict:
    """
    Fetches CPU, Memory and Disk I/O metrics from the node metrics index.
    Used by the orchestrator to enrich the reasoning context.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=time_range_hours)).isoformat()

    query = f"""
FROM {NODE_METRICS_INDEX_PATTERN}
| WHERE @timestamp >= "{cutoff}"
| STATS
    avg_cpu = AVG(elasticsearch.node.stats.os.cpu.percent),
    avg_mem_used = AVG(elasticsearch.node.stats.os.mem.used_percent),
    avg_disk_io_read = AVG(elasticsearch.node.stats.fs.io_stats.total.read_kilobytes),
    avg_disk_io_write = AVG(elasticsearch.node.stats.fs.io_stats.total.write_kilobytes)
  BY elasticsearch.node.name
| SORT avg_cpu DESC
""".strip()
    return run_esql_query(query, NODE_METRICS_INDEX_PATTERN, time_range_hours)


def fetch_index_metadata(index_name: str = "*") -> dict:
    """
    Fetches current mappings and settings from the index-metadata index.
    The agent uses this to understand field types before proposing mapping changes.
    """
    query = f"""
FROM {INDEX_METADATA_INDEX}
| WHERE index_name LIKE "{index_name}"
| KEEP index_name, field_name, field_type, settings
""".strip()
    return run_esql_query(query, INDEX_METADATA_INDEX)


def fetch_circuit_breaker_stats() -> dict:
    """
    Fetches current circuit breaker statistics so the agent can
    detect CircuitBreakerExceptions and correlate with docs search results.
    """
    query = f"""
FROM {NODE_METRICS_INDEX_PATTERN}
| STATS
    avg_used = AVG(elasticsearch.node.stats.breakers.parent.estimated_size_in_bytes),
    avg_limit = AVG(elasticsearch.node.stats.breakers.parent.limit_size_in_bytes)
  BY elasticsearch.node.name
| EVAL used_pct = avg_used / avg_limit * 100
| WHERE used_pct > 70
| SORT used_pct DESC
""".strip()
    return run_esql_query(query, NODE_METRICS_INDEX_PATTERN)
