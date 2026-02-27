import pytest
from unittest.mock import patch, MagicMock, call
from agent.orchestrator import run_optimization_cycle, _dispatch_tool


class TestDispatchTool:
    #Verifies every tool name routes to the correct function

    @patch("agent.orchestrator.run_esql_query")
    def test_dispatches_run_esql_query(self, mock_fn):
        mock_fn.return_value = {"columns": [], "rows": [], "meta": {}}
        result = _dispatch_tool("run_esql_query", {
            "query": "FROM .slowlog-* | LIMIT 5",
            "index_pattern": ".slowlog-*",
            "time_range_hours": 1,
        })
        mock_fn.assert_called_once()

    @patch("agent.orchestrator.search_elastic_docs")
    def test_dispatches_search_elastic_docs(self, mock_fn):
        mock_fn.return_value = [{"score": 0.9, "title": "Wildcards", "url": "", "text": ""}]
        result = _dispatch_tool("search_elastic_docs", {"query": "wildcard optimization"})
        assert result["status"] == "ok"
        mock_fn.assert_called_once_with(query="wildcard optimization", top_k=5)

    @patch("agent.orchestrator.update_index_settings")
    def test_dispatches_update_index_settings(self, mock_fn):
        mock_fn.return_value = {"status": "applied"}
        _dispatch_tool("update_index_settings", {
            "index_name": "logs-2024",
            "settings": {"settings": {}},
            "reason": "test",
        })
        mock_fn.assert_called_once()

    @patch("agent.orchestrator.update_cluster_settings")
    def test_dispatches_update_cluster_settings(self, mock_fn):
        mock_fn.return_value = {"status": "applied"}
        _dispatch_tool("update_cluster_settings", {
            "persistent": {"indices.breaker.total.limit": "70%"},
            "reason": "Breaker fix.",
        })
        mock_fn.assert_called_once()

    @patch("agent.orchestrator.create_index_template")
    def test_dispatches_create_index_template(self, mock_fn):
        mock_fn.return_value = {"status": "applied"}
        _dispatch_tool("create_index_template", {
            "template_name": "t",
            "index_patterns": ["t-*"],
            "mappings": {},
            "reason": "Mapping optimization.",
        })
        mock_fn.assert_called_once()

    @patch("agent.orchestrator.update_alias")
    def test_dispatches_update_alias(self, mock_fn):
        mock_fn.return_value = {"status": "applied"}
        _dispatch_tool("update_alias", {
            "alias_name": "logs-current",
            "remove_index": "logs-2024",
            "add_index": "logs-2024-opt",
            "reason": "Post-reindex alias swap.",
        })
        mock_fn.assert_called_once()

    def test_unknown_tool_returns_error(self):
        result = _dispatch_tool("nonexistent_tool", {})
        assert result["status"] == "error"
        assert "Unknown tool" in result["message"]


class TestRunOptimizationCycle:
    #full cycle

    @patch("agent.orchestrator.fetch_circuit_breaker_stats", return_value={"columns": [], "rows": [], "meta": {}})
    @patch("agent.orchestrator.fetch_node_metrics", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.fetch_slowest_queries", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.call_reasoning_model")
    def test_cycle_completes_on_text_response(
        self, mock_llm, mock_slow, mock_metrics, mock_breaker
    ):
        mock_llm.return_value = {
            "type": "text",
            "content": "No critical bottlenecks detected in this interval.",
        }
        result = run_optimization_cycle(time_range_hours=1)
        assert result["status"] == "completed"
        assert any(s["step"] == "identify" for s in result["steps"])
        assert any(s["step"] == "conclusion" for s in result["steps"])

    @patch("agent.orchestrator.fetch_circuit_breaker_stats", return_value={"columns": [], "rows": [], "meta": {}})
    @patch("agent.orchestrator.fetch_node_metrics", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.fetch_slowest_queries", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.search_elastic_docs", return_value=[])
    @patch("agent.orchestrator.call_reasoning_model")
    def test_cycle_dispatches_tool_call_then_concludes(
        self, mock_llm, mock_search, mock_slow, mock_metrics, mock_breaker
    ):
        # First call returns a tool call, second text
        mock_llm.side_effect = [
            {"type": "tool_call", "tool_name": "search_elastic_docs", "tool_args": {"query": "wildcard optimization"}},
            {"type": "text", "content": "Use wildcard field type instead of keyword."},
        ]
        result = run_optimization_cycle(time_range_hours=1)
        assert result["status"] == "completed"
        assert len(result["actions_taken"]) == 1
        assert result["actions_taken"][0]["tool"] == "search_elastic_docs"

    @patch("agent.orchestrator.fetch_circuit_breaker_stats", return_value={"columns": [], "rows": [], "meta": {}})
    @patch("agent.orchestrator.fetch_node_metrics", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.fetch_slowest_queries", return_value={"columns": [], "rows": [], "meta": {"row_count": 0}})
    @patch("agent.orchestrator.call_reasoning_model")
    def test_max_rounds_guard(self, mock_llm, mock_slow, mock_metrics, mock_breaker):
        # Always returns a tool call — should hit MAX_TOOL_ROUNDS
        mock_llm.return_value = {
            "type": "tool_call",
            "tool_name": "run_esql_query",
            "tool_args": {"query": "FROM test", "index_pattern": "test-*"},
        }
        with patch("agent.orchestrator.run_esql_query", return_value={"columns": [], "rows": [], "meta": {}}):
            result = run_optimization_cycle(time_range_hours=1)
        assert result["status"] == "max_rounds_reached"
