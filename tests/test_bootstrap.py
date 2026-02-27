import pytest
from unittest.mock import patch, MagicMock, call
from setup.bootstrap import (
    enable_stack_monitoring,
    verify_required_indices,
    refresh_index_metadata,
    _flatten_mappings,
    run_bootstrap,
)


def _mock_es_client():
    client = MagicMock()
    client.cluster.put_settings.return_value = MagicMock(body={"acknowledged": True})
    client.indices.put_settings.return_value = MagicMock(body={"acknowledged": True})
    client.indices.exists.return_value = True
    client.indices.create.return_value = MagicMock(body={"acknowledged": True})
    client.indices.get_mapping.return_value = {
        "logs-2024": {
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "message": {"type": "text"},
                    "event": {
                        "properties": {
                            "duration": {"type": "long"}
                        }
                    }
                }
            }
        }
    }
    client.indices.get_settings.return_value = {
        "logs-2024": {
            "settings": {
                "index": {
                    "number_of_shards": "1",
                    "number_of_replicas": "1"
                }
            }
        }
    }
    client.indices.stats.return_value = {
        "indices": {
            "logs-2024": {
                "primaries": {
                    "docs": {"count": 1000000},
                    "store": {"size_in_bytes": 50000000},
                }
            }
        }
    }
    client.indices.get_alias.return_value = {
        "logs-2024": {"aliases": {"logs-current": {}}}
    }
    client.bulk.return_value = MagicMock(body={"errors": False})
    return client


class TestEnableStackMonitoring:

    @patch("setup.bootstrap._get_production_client")
    def test_enables_xpack_monitoring_collection(self, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        result = enable_stack_monitoring()

        calls = client.cluster.put_settings.call_args_list
        all_payloads = [str(c) for c in calls]
        assert any("xpack.monitoring" in p for p in all_payloads)
        assert "monitoring_enabled" in result

    @patch("setup.bootstrap._get_production_client")
    def test_enables_slowlog_on_all_indices(self, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        enable_stack_monitoring()

        #called indices.put_settings with slowlog thresholds
        client.indices.put_settings.assert_called_once()
        call_body = client.indices.put_settings.call_args[1]["body"]
        assert "slowlog" in str(call_body).lower()

    @patch("setup.bootstrap._get_production_client")
    def test_returns_dict_with_all_keys(self, mock_get_client):
        mock_get_client.return_value = _mock_es_client()
        result = enable_stack_monitoring()
        assert "monitoring_enabled" in result
        assert "slowlog_enabled" in result


class TestVerifyRequiredIndices:

    @patch("setup.bootstrap._get_monitoring_client")
    def test_all_indices_exist(self, mock_get_client):
        client = _mock_es_client()
        mock_get_client.return_value = client
        status = verify_required_indices()
        assert isinstance(status, dict)
        assert len(status) == 3  # slowlog, node metrics, index-metadata

    @patch("setup.bootstrap._get_monitoring_client")
    def test_reports_missing_index(self, mock_get_client):
        client = _mock_es_client()
        client.indices.exists.return_value = False
        mock_get_client.return_value = client
        status = verify_required_indices()
        assert all(v is False for v in status.values())


class TestFlattenMappings:
    def test_flattens_simple_properties(self):
        mappings = {
            "properties": {
                "user_id": {"type": "keyword"},
                "message": {"type": "text"},
            }
        }
        records = _flatten_mappings(mappings)
        field_names = [r["field_name"] for r in records]
        field_types = {r["field_name"]: r["field_type"] for r in records}
        assert "user_id" in field_names
        assert "message" in field_names
        assert field_types["user_id"] == "keyword"
        assert field_types["message"] == "text"

    def test_flattens_nested_properties(self):
        mappings = {
            "properties": {
                "event": {
                    "properties": {
                        "duration": {"type": "long"},
                        "type": {"type": "keyword"},
                    }
                }
            }
        }
        records = _flatten_mappings(mappings)
        field_names = [r["field_name"] for r in records]
        assert "event.duration" in field_names
        assert "event.type" in field_names

    def test_returns_empty_on_no_properties(self):
        records = _flatten_mappings({})
        assert records == []


class TestRefreshIndexMetadata:
    #crawls production mappings and writes to index-metadata

    @patch("setup.bootstrap._get_monitoring_client")
    @patch("setup.bootstrap._get_production_client")
    def test_writes_field_records_to_index_metadata(self, mock_prod, mock_mon):
        prod_client = _mock_es_client()
        mon_client = _mock_es_client()
        mock_prod.return_value = prod_client
        mock_mon.return_value = mon_client

        result = refresh_index_metadata()

        assert result["indices_indexed"] >= 1
        assert result["fields_indexed"] >= 3  # user_id, message, event.duration
        mon_client.bulk.assert_called()

    @patch("setup.bootstrap._get_monitoring_client")
    @patch("setup.bootstrap._get_production_client")
    def test_skips_internal_system_indices(self, mock_prod, mock_mon):
        prod_client = _mock_es_client()
        # Add a system index
        prod_client.indices.get_mapping.return_value = {
            ".kibana": {"mappings": {"properties": {"x": {"type": "keyword"}}}},
            "logs-2024": {"mappings": {"properties": {"user_id": {"type": "keyword"}}}},
        }
        prod_client.indices.get_settings.return_value = {
            ".kibana": {"settings": {"index": {"number_of_shards": "1", "number_of_replicas": "0"}}},
            "logs-2024": {"settings": {"index": {"number_of_shards": "1", "number_of_replicas": "1"}}},
        }
        prod_client.indices.stats.return_value = {
            "indices": {
                ".kibana": {"primaries": {"docs": {"count": 100}, "store": {"size_in_bytes": 1000}}},
                "logs-2024": {"primaries": {"docs": {"count": 1000000}, "store": {"size_in_bytes": 50000000}}},
            }
        }
        mon_client = _mock_es_client()
        mock_prod.return_value = prod_client
        mock_mon.return_value = mon_client

        result = refresh_index_metadata()
        # Only logs-2024 should be indexed, not .kibana
        assert result["indices_indexed"] == 1


class TestRunBootstrap:
    @patch("setup.bootstrap.refresh_index_metadata", return_value={"indices_indexed": 1, "fields_indexed": 3, "refreshed_at": "2024-01-01"})
    @patch("setup.bootstrap.verify_required_indices", return_value={".slowlog-*": True, "metrics-*": True, "index-metadata": True})
    @patch("setup.bootstrap.enable_stack_monitoring", return_value={"monitoring_enabled": True, "slowlog_enabled": True})
    def test_run_bootstrap_calls_all_three_steps(self, mock_mon, mock_verify, mock_refresh):
        result = run_bootstrap()
        mock_mon.assert_called_once()
        mock_verify.assert_called_once()
        mock_refresh.assert_called_once()
        assert "monitoring" in result
        assert "index_verification" in result
        assert "index_metadata_refresh" in result
