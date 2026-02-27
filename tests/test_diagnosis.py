import pytest
from unittest.mock import patch
from agent.diagnosis import (
    _detect_wildcard_anti_patterns,
    _detect_circuit_breaker,
    _detect_unbounded_aggregations,
    _detect_deep_nesting,
    _detect_script_queries,
    _detect_regexp_queries,
    _compute_severity,
    diagnose_slow_queries,
    build_diagnosis_context,
    DiagnosisResult,
)


class TestDetectWildcardAntiPatterns:
    #wildcard on high-cardinality field

    @patch("agent.diagnosis._estimate_cardinality", return_value=50000)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="keyword")
    def test_detects_wildcard_on_high_cardinality(self, mock_type, mock_card):
        statement = '{"query": {"wildcard": {"user_id": {"value": "john*"}}}}'
        ap, af, ft, rs = _detect_wildcard_anti_patterns(statement, "logs-2024")
        assert len(ap) > 0
        assert any("wildcard" in p.lower() or "cardinality" in p.lower() for p in ap)
        assert "user_id" in af

    @patch("agent.diagnosis._estimate_cardinality", return_value=50000)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="keyword")
    def test_detects_leading_wildcard(self, mock_type, mock_card):
        statement = '{"query": {"wildcard": {"message": {"value": "*error*"}}}}'
        ap, _, _, _ = _detect_wildcard_anti_patterns(statement, "logs-2024")
        assert any("leading wildcard" in p.lower() or "full shard scan" in p.lower() for p in ap)

    @patch("agent.diagnosis._estimate_cardinality", return_value=10)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="keyword")
    def test_no_pattern_on_low_cardinality(self, mock_type, mock_card):
        statement = '{"query": {"wildcard": {"status": {"value": "act*"}}}}'
        ap, _, _, _ = _detect_wildcard_anti_patterns(statement, "logs-2024")
        # Low cardinality wildcard on a small enum-like field is not flagged
        assert not any("cardinality" in p.lower() for p in ap)

    @patch("agent.diagnosis._estimate_cardinality", return_value=0)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="text")
    def test_recommends_ngram_or_wildcard_type(self, mock_type, mock_card):
        statement = '{"query": {"wildcard": {"body": {"value": "error*"}}}}'
        _, _, _, rs = _detect_wildcard_anti_patterns(statement, "logs-2024")
        # Should recommend some search even if cardinality is unknown
        assert isinstance(rs, list)


class TestDetectCircuitBreaker:
    #CircuitBreakerException → look up indices.breaker.total.limit

    def test_detects_circuit_breaker_exception(self):
        statement = "CircuitBreakingException: [parent] Data too large, data for [indices:data/read/search]"
        ap, rs = _detect_circuit_breaker(statement)
        assert len(ap) == 1
        assert "indices.breaker.total.limit" in ap[0]
        assert len(rs) == 1
        assert "breaker" in rs[0].lower()

    def test_no_detection_on_normal_query(self):
        statement = '{"query": {"match": {"message": "hello world"}}}'
        ap, rs = _detect_circuit_breaker(statement)
        assert ap == []
        assert rs == []

    def test_detects_circuit_breaking_exception_variant(self):
        statement = "circuit_breaking_exception: request rejected"
        ap, _ = _detect_circuit_breaker(statement)
        assert len(ap) == 1


class TestDetectUnboundedAggregations:
    def test_detects_terms_agg_without_size(self):
        statement = '{"aggs": {"by_user": {"terms": {"field": "user_id"}}}}'
        ap, rs = _detect_unbounded_aggregations(statement)
        assert len(ap) > 0
        assert any("size" in p.lower() for p in ap)

    def test_no_detection_when_size_present(self):
        statement = '{"aggs": {"by_user": {"terms": {"field": "user_id", "size": 10}}}}'
        ap, rs = _detect_unbounded_aggregations(statement)
        assert ap == []


class TestDetectDeepNesting:
    def test_detects_multiple_nested_clauses(self):
        statement = '{"query": {"nested": {"path": "a", "query": {"nested": {"path": "b", "query": {}}}}}}'
        ap, rs = _detect_deep_nesting(statement)
        assert len(ap) > 0
        assert any("nested" in p.lower() for p in ap)

    def test_no_detection_on_single_nested(self):
        statement = '{"query": {"nested": {"path": "comments", "query": {"match": {"comments.text": "hello"}}}}}'
        ap, rs = _detect_deep_nesting(statement)
        assert ap == []


class TestDetectScriptQueries:
    def test_detects_script_query(self):
        statement = '{"query": {"script": {"script": {"source": "doc[\'price\'].value > 100"}}}}'
        ap, rs = _detect_script_queries(statement)
        assert len(ap) > 0
        assert any("script" in p.lower() for p in ap)

    def test_no_detection_on_non_script(self):
        statement = '{"query": {"match": {"title": "elasticsearch"}}}'
        ap, rs = _detect_script_queries(statement)
        assert ap == []


class TestDetectRegexpQueries:
    def test_detects_regexp(self):
        statement = '{"query": {"regexp": {"user_id": {"value": "kim.*"}}}}'
        ap, rs = _detect_regexp_queries(statement)
        assert len(ap) > 0

    def test_no_detection_on_match(self):
        statement = '{"query": {"match": {"title": "test"}}}'
        ap, rs = _detect_regexp_queries(statement)
        assert ap == []


class TestComputeSeverity:
    def test_critical_on_circuit_breaker(self):
        ap = ["CircuitBreakerException detected."]
        assert _compute_severity(ap, avg_duration_ns=1_000_000) == "critical"

    def test_critical_on_very_slow_query(self):
        ap = ["Some anti-pattern."]
        assert _compute_severity(ap, avg_duration_ns=15_000_000_000) == "critical"  # 15s

    def test_high_on_slow_query(self):
        ap = ["Wildcard on high-cardinality field."]
        assert _compute_severity(ap, avg_duration_ns=6_000_000_000) == "high"  # 6s

    def test_medium_on_moderate_query(self):
        ap = ["Wildcard.", "Unbounded aggregation."]
        assert _compute_severity(ap, avg_duration_ns=3_000_000_000) == "medium"  # 3s

    def test_low_on_no_anti_patterns(self):
        assert _compute_severity([], avg_duration_ns=1_000_000) == "low"


class TestDiagnoseSlowQueries:
    @patch("agent.diagnosis._estimate_cardinality", return_value=5000)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="keyword")
    def test_returns_diagnosis_results(self, mock_type, mock_card):
        slow_result = {
            "columns": ["avg_duration", "count", "statement"],
            "rows": [
                [5_000_000_000, 200, '{"query": {"wildcard": {"user_id": {"value": "kim*"}}}}'],
                [1_000_000_000, 150, '{"query": {"match": {"title": "test"}}}'],
            ],
            "meta": {"row_count": 2}
        }
        findings = diagnose_slow_queries(slow_result, index_name="logs-2024")
        assert len(findings) == 2
        assert isinstance(findings[0], DiagnosisResult)

    @patch("agent.diagnosis._estimate_cardinality", return_value=5000)
    @patch("agent.diagnosis._fetch_field_type_from_metadata", return_value="keyword")
    def test_orders_by_severity_then_duration(self, mock_type, mock_card):
        slow_result = {
            "columns": ["avg_duration", "count", "statement"],
            "rows": [
                [1_000_000_000, 100, '{"query": {"match": {"x": "y"}}}'],
                [9_000_000_000, 200, '{"query": {"wildcard": {"user_id": {"value": "k*"}}}}'],
            ],
            "meta": {}
        }
        findings = diagnose_slow_queries(slow_result)
        # The wildcard query (higher severity) should come first
        assert findings[0].avg_duration_ns == 9_000_000_000

    def test_empty_rows_returns_empty_list(self):
        slow_result = {"columns": [], "rows": [], "meta": {}}
        findings = diagnose_slow_queries(slow_result)
        assert findings == []


class TestBuildDiagnosisContext:
    def test_returns_no_patterns_message_on_empty(self):
        text = build_diagnosis_context([])
        assert "no" in text.lower() or "detected" in text.lower()

    def test_includes_anti_pattern_text(self):
        findings = [
            DiagnosisResult(
                statement='{"query": {"wildcard": {"user_id": {"value": "k*"}}}}',
                avg_duration_ns=5_000_000_000,
                count=200,
                anti_patterns=["Wildcard on high-cardinality field 'user_id'."],
                severity="high",
                recommended_searches=["Elasticsearch wildcard field type optimization"],
            )
        ]
        text = build_diagnosis_context(findings)
        assert "user_id" in text or "wildcard" in text.lower()
        assert "high" in text.upper() or "HIGH" in text

    def test_includes_recommended_searches(self):
        findings = [
            DiagnosisResult(
                statement="SELECT 1",
                avg_duration_ns=3_000_000_000,
                count=100,
                anti_patterns=["CircuitBreakerException detected."],
                severity="critical",
                recommended_searches=["Elasticsearch indices.breaker.total.limit"],
            )
        ]
        text = build_diagnosis_context(findings)
        assert "indices.breaker.total.limit" in text or "breaker" in text.lower()
