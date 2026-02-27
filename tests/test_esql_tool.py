import pytest
from unittest.mock import patch, MagicMock
from tools.esql_tool import (
    build_slowest_queries_esql,
    fetch_slowest_queries,
    fetch_node_metrics,
    fetch_index_metadata,
    fetch_circuit_breaker_stats,
    run_esql_query,
)


class TestBuildSlowestQueriesEsql:
    #Verify the ES|QL query shape matches the spec

    def test_contains_from_slowlog_pattern(self):
        query = build_slowest_queries_esql(time_range_hours=1)
        assert "FROM" in query
        assert "slowlog" in query.lower() or ".ds-elasticsearch" in query

    def test_contains_stats_avg_duration(self):
        query = build_slowest_queries_esql(time_range_hours=1)
        assert "AVG(event.duration)" in query
        assert "avg_duration" in query

    def test_contains_count_and_where(self):
        query = build_slowest_queries_esql(time_range_hours=1)
        assert "COUNT()" in query
        assert "WHERE" in query

    def test_contains_sort_desc(self):
        query = build_slowest_queries_esql(time_range_hours=1)
        assert "SORT avg_duration DESC" in query

    def test_contains_limit(self):
        query = build_slowest_queries_esql(time_range_hours=1)
        assert "LIMIT" in query

    def test_timestamp_filter_present(self):
        query = build_slowest_queries_esql(time_range_hours=2)
        assert "@timestamp" in query

    def test_by_statement_group(self):
        query = build_slowest_queries_esql()
        assert "BY statement" in query


class TestRunEsqlQuery:
    #Verify run_esql_query correctly calls the ES client and returns structured data

    def _make_mock_client(self, columns, rows):
        mock_client = MagicMock()
        mock_client.esql.query.return_value = {
            "columns": [{"name": c} for c in columns],
            "values": rows,
        }
        return mock_client

    @patch("tools.esql_tool._get_monitoring_client")
    def test_returns_columns_and_rows(self, mock_get_client):
        columns = ["avg_duration", "count", "statement"]
        rows = [[5000, 200, "SELECT * FROM logs"]]
        mock_get_client.return_value = self._make_mock_client(columns, rows)

        result = run_esql_query("FROM test | STATS ...", ".slowlog-*")
        assert result["columns"] == columns
        assert result["rows"] == rows
        assert result["meta"]["row_count"] == 1

    @patch("tools.esql_tool._get_monitoring_client")
    def test_meta_includes_index_pattern(self, mock_get_client):
        mock_get_client.return_value = self._make_mock_client([], [])
        result = run_esql_query("FROM test", "metrics-*", time_range_hours=3)
        assert result["meta"]["index_pattern"] == "metrics-*"
        assert result["meta"]["time_range_hours"] == 3

    @patch("tools.esql_tool._get_monitoring_client")
    def test_empty_result(self, mock_get_client):
        mock_get_client.return_value = self._make_mock_client([], [])
        result = run_esql_query("FROM empty", "empty-*")
        assert result["rows"] == []
        assert result["meta"]["row_count"] == 0


class TestFetchSlowQueries:
    @patch("tools.esql_tool.run_esql_query")
    def test_calls_run_esql_with_slowlog_pattern(self, mock_run):
        mock_run.return_value = {"columns": [], "rows": [], "meta": {"row_count": 0}}
        fetch_slowest_queries(time_range_hours=1)
        call_args = mock_run.call_args
        assert "slowlog" in call_args[0][1].lower() or "elasticsearch" in call_args[0][1].lower()

    @patch("tools.esql_tool.run_esql_query")
    def test_returns_run_esql_result(self, mock_run):
        expected = {"columns": ["a"], "rows": [[1]], "meta": {"row_count": 1}}
        mock_run.return_value = expected
        result = fetch_slowest_queries()
        assert result == expected


class TestFetchNodeMetrics:
    @patch("tools.esql_tool.run_esql_query")
    def test_queries_node_metrics_index(self, mock_run):
        #Must query metrics-elasticsearch.node-*
        mock_run.return_value = {"columns": [], "rows": [], "meta": {}}
        fetch_node_metrics()
        call_args = mock_run.call_args
        assert "metrics-elasticsearch" in call_args[0][1] or "node" in call_args[0][0]

    @patch("tools.esql_tool.run_esql_query")
    def test_query_contains_cpu_and_mem(self, mock_run):
        mock_run.return_value = {"columns": [], "rows": [], "meta": {}}
        fetch_node_metrics()
        esql_query = mock_run.call_args[0][0]
        assert "cpu" in esql_query.lower()
        assert "mem" in esql_query.lower()


class TestFetchCircuitBreakerStats:
    @patch("tools.esql_tool.run_esql_query")
    def test_filters_high_usage(self, mock_run):
        mock_run.return_value = {"columns": [], "rows": [], "meta": {}}
        fetch_circuit_breaker_stats()
        esql_query = mock_run.call_args[0][0]
        assert "breaker" in esql_query.lower()
        assert "used_pct" in esql_query or "%" in esql_query or "70" in esql_query
