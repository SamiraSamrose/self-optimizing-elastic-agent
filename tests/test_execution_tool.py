import pytest
from unittest.mock import patch, MagicMock
from tools.execution_tool import (
    update_index_settings,
    update_cluster_settings,
    create_index_template,
    trigger_reindex,
    update_alias,
    get_reindex_task_status,
)


def _mock_es_client():
    client = MagicMock()
    client.indices.put_settings.return_value = MagicMock(body={"acknowledged": True})
    client.indices.put_mapping.return_value = MagicMock(body={"acknowledged": True})
    client.cluster.put_settings.return_value = MagicMock(body={"acknowledged": True})
    client.indices.put_index_template.return_value = MagicMock(body={"acknowledged": True})
    client.reindex.return_value = MagicMock(body={"task": "node:123456"})
    client.indices.update_aliases.return_value = MagicMock(body={"acknowledged": True})
    client.tasks.get.return_value = MagicMock(body={"completed": True, "response": {}})
    return client


class TestUpdateIndexSettings:
    #Implementation schema

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_applies_settings_when_approved(self, mock_approval, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = update_index_settings(
            index_name="logs-2024",
            settings={"settings": {"index.number_of_replicas": 1}},
            reason="Reducing replicas to lower storage cost.",
        )
        assert result["status"] == "applied"

    @patch("tools.execution_tool.request_approval", return_value=False)
    def test_rejects_when_not_approved(self, mock_approval):
        result = update_index_settings(
            index_name="logs-2024",
            settings={"settings": {"index.number_of_replicas": 1}},
            reason="Reducing replicas.",
        )
        assert result["status"] == "rejected"

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_applies_mappings_when_present(self, mock_approval, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        update_index_settings(
            index_name="logs-2024",
            settings={"mappings": {"properties": {"user_id": {"type": "wildcard"}}}},
            reason="Switching user_id to wildcard field type.",
        )
        client.indices.put_mapping.assert_called_once()

    @patch("tools.execution_tool.request_approval", return_value=True)
    @patch("tools.execution_tool._get_client")
    def test_approval_receives_reason(self, mock_get_client, mock_approval):
        mock_get_client.return_value = _mock_es_client()
        update_index_settings("idx", {"settings": {}}, reason="my reason")
        call_kwargs = mock_approval.call_args[1]
        assert call_kwargs["reason"] == "my reason"


class TestUpdateClusterSettings:
    # _cluster/settings, e.g., indices.breaker.total.limit

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_applies_persistent_settings(self, mock_approval, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = update_cluster_settings(
            persistent={"indices.breaker.total.limit": "70%"},
            reason="CircuitBreakerException detected. Raising breaker limit.",
        )
        assert result["status"] == "applied"

    @patch("tools.execution_tool.request_approval", return_value=False)
    def test_rejected_returns_rejected_status(self, mock_approval):
        result = update_cluster_settings(
            persistent={"indices.breaker.total.limit": "70%"},
            reason="Breaker adjustment.",
        )
        assert result["status"] == "rejected"


class TestCreateIndexTemplate:
    #Plan Step A

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_creates_template_when_approved(self, mock_approval, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = create_index_template(
            template_name="logs-optimized-template",
            index_patterns=["logs-optimized-*"],
            mappings={"properties": {"message": {"type": "wildcard"}}},
            settings={"number_of_shards": 1},
            reason="Switching message field to wildcard for faster partial matches.",
        )
        assert result["status"] == "applied"

    @patch("tools.execution_tool.request_approval", return_value=False)
    def test_not_created_when_rejected(self, mock_approval):
        result = create_index_template(
            template_name="t",
            index_patterns=["t-*"],
            mappings={},
            reason="Test.",
        )
        assert result["status"] == "rejected"


class TestTriggerReindex:
    #Plan Step B /Execute

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_starts_reindex_when_approved(self, mock_approval, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = trigger_reindex(
            source_index="logs-2024",
            destination_index="logs-2024-optimized",
            reason="Reindexing to apply optimized wildcard mapping.",
        )
        assert result["status"] == "started"
        assert "task_id" in result

    @patch("tools.execution_tool.request_approval", return_value=False)
    def test_not_started_when_rejected(self, mock_approval):
        result = trigger_reindex(
            source_index="logs-2024",
            destination_index="logs-2024-optimized",
            reason="Reindex.",
        )
        assert result["status"] == "rejected"

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_default_query_is_match_all(self, mock_approval, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        trigger_reindex("src", "dst", reason="reason")
        call_body = client.reindex.call_args[1]["body"]
        assert call_body["source"]["query"] == {"match_all": {}}


class TestUpdateAlias:
    #Plan Step C

    @patch("tools.execution_tool._get_client")
    @patch("tools.execution_tool.request_approval", return_value=True)
    def test_updates_alias_when_approved(self, mock_approval, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = update_alias(
            alias_name="logs-current",
            remove_index="logs-2024",
            add_index="logs-2024-optimized",
            reason="Pointing alias to reindexed index.",
        )
        assert result["status"] == "applied"

    @patch("tools.execution_tool.request_approval", return_value=False)
    def test_rejected_when_not_approved(self, mock_approval):
        result = update_alias("alias", "old", "new", reason="reason")
        assert result["status"] == "rejected"


class TestGetReindexTaskStatus:
    @patch("tools.execution_tool._get_client")
    def test_returns_task_body(self, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        result = get_reindex_task_status("node:123456")
        assert result["completed"] is True
