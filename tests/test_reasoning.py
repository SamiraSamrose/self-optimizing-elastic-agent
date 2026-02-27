import json
import pytest
from unittest.mock import patch, MagicMock
from agent.reasoning import (
    SYSTEM_PROMPT,
    build_initial_message,
    call_reasoning_model,
)


class TestSystemPrompt:
    #Verify the system prompt matches the spec

    def test_contains_sre_persona(self):
        assert "SRE" in SYSTEM_PROMPT or "Site Reliability" in SYSTEM_PROMPT.replace("SRE", "Site Reliability Engineer")

    def test_contains_latency_goal(self):
        assert "latency" in SYSTEM_PROMPT.lower()

    def test_contains_approval_requirement(self):
        assert "approval" in SYSTEM_PROMPT.lower() or "seeking approval" in SYSTEM_PROMPT.lower()

    def test_contains_destructive_change_warning(self):
        assert "destructive" in SYSTEM_PROMPT.lower()

    def test_contains_documentation_search_instruction(self):
        assert "documentation" in SYSTEM_PROMPT.lower() or "search" in SYSTEM_PROMPT.lower()


class TestBuildInitialMessage:
    def test_returns_list_with_user_message(self):
        context = {
            "slow_queries": {"columns": [], "rows": [], "meta": {}},
            "node_metrics": {"columns": [], "rows": [], "meta": {}},
            "circuit_breakers": {"columns": [], "rows": [], "meta": {}},
        }
        messages = build_initial_message(context)
        assert isinstance(messages, list)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_message_contains_slowest_queries(self):
        context = {
            "slow_queries": {"rows": [["SELECT 1", 5000, 200]], "meta": {}},
            "node_metrics": {},
            "circuit_breakers": {},
        }
        messages = build_initial_message(context)
        assert "slow" in messages[0]["content"].lower() or "query" in messages[0]["content"].lower()

    def test_message_contains_optimization_instruction(self):
        context = {"slow_queries": {}, "node_metrics": {}, "circuit_breakers": {}}
        messages = build_initial_message(context)
        assert "optimization" in messages[0]["content"].lower() or "bottleneck" in messages[0]["content"].lower()


class TestCallReasoningModelAnthropic:
    @patch("agent.reasoning.REASONING_PROVIDER", "anthropic")
    @patch("agent.reasoning.ANTHROPIC_API_KEY", "test-key")
    @patch("agent.reasoning._call_anthropic")
    def test_routes_to_anthropic(self, mock_anthropic):
        mock_anthropic.return_value = {"type": "text", "content": "Analysis complete."}
        result = call_reasoning_model([{"role": "user", "content": "Analyze this."}])
        mock_anthropic.assert_called_once()
        assert result["type"] == "text"

    @patch("agent.reasoning.REASONING_PROVIDER", "anthropic")
    def test_anthropic_text_response_parsed(self):
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "No bottleneck found."

        mock_response = MagicMock()
        mock_response.content = [mock_block]

        import anthropic as anthropic_module
        with patch("agent.reasoning.REASONING_PROVIDER", "anthropic"):
            with patch("anthropic.Anthropic") as mock_client_class:
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_client_class.return_value = mock_client

                result = call_reasoning_model([{"role": "user", "content": "test"}])
                assert result["type"] == "text"
                assert "bottleneck" in result["content"]

    @patch("agent.reasoning.REASONING_PROVIDER", "anthropic")
    def test_anthropic_tool_call_response_parsed(self):
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = "search_elastic_docs"
        mock_block.input = {"query": "wildcard optimization"}

        mock_response = MagicMock()
        mock_response.content = [mock_block]

        with patch("anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = call_reasoning_model([{"role": "user", "content": "test"}])
            assert result["type"] == "tool_call"
            assert result["tool_name"] == "search_elastic_docs"
            assert result["tool_args"]["query"] == "wildcard optimization"


class TestCallReasoningModelOpenAI:
    @patch("agent.reasoning.REASONING_PROVIDER", "openai")
    def test_openai_text_response_parsed(self):
        mock_message = MagicMock()
        mock_message.content = "Rewrite the wildcard query."
        mock_message.tool_calls = None

        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("openai.OpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = call_reasoning_model([{"role": "user", "content": "test"}])
            assert result["type"] == "text"
            assert "wildcard" in result["content"]

    @patch("agent.reasoning.REASONING_PROVIDER", "openai")
    def test_openai_tool_call_response_parsed(self):
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "run_esql_query"
        mock_tool_call.function.arguments = json.dumps({
            "query": "FROM .slowlog-* | LIMIT 5",
            "index_pattern": ".slowlog-*",
        })

        mock_message = MagicMock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = MagicMock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("openai.OpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = call_reasoning_model([{"role": "user", "content": "test"}])
            assert result["type"] == "tool_call"
            assert result["tool_name"] == "run_esql_query"

    @patch("agent.reasoning.REASONING_PROVIDER", "bad_provider")
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown reasoning provider"):
            call_reasoning_model([{"role": "user", "content": "test"}])
