import pytest
from unittest.mock import patch, MagicMock, call
from workflows.reindex_workflow import run_reindex_workflow


def _make_applied():
    return {"status": "applied", "response": {"acknowledged": True}}


def _make_started():
    return {"status": "started", "task_id": "node:99999", "response": {}}


def _make_task_completed():
    return {"completed": True, "response": {}}


class TestRunReindexWorkflow:
    #Plan Step A: create template
    # Plan Step B: trigger reindex
    #Plan Step C: update alias

    @patch("workflows.reindex_workflow.update_alias", return_value=_make_applied())
    @patch("workflows.reindex_workflow.get_reindex_task_status", return_value=_make_task_completed())
    @patch("workflows.reindex_workflow.trigger_reindex", return_value=_make_started())
    @patch("workflows.reindex_workflow.create_index_template", return_value=_make_applied())
    def test_all_three_steps_complete(self, mock_a, mock_b, mock_status, mock_c):
        result = run_reindex_workflow(
            source_index="logs-2024",
            destination_index="logs-2024-optimized",
            alias_name="logs-current",
            template_name="logs-optimized-template",
            index_patterns=["logs-2024-optimized*"],
            optimized_mappings={"properties": {"message": {"type": "wildcard"}}},
            optimized_settings={"number_of_shards": 1},
            reason="Wildcard field optimization.",
        )
        assert result["overall_status"] == "completed"
        assert result["plan_step_a"]["status"] == "applied"
        assert result["plan_step_b"]["status"] == "started"
        assert result["plan_step_c"]["status"] == "applied"

    @patch("workflows.reindex_workflow.create_index_template", return_value={"status": "rejected"})
    def test_halts_at_step_a_if_rejected(self, mock_a):
        result = run_reindex_workflow(
            source_index="logs-2024",
            destination_index="logs-opt",
            alias_name="logs-current",
            template_name="t",
            index_patterns=["t-*"],
            optimized_mappings={},
            optimized_settings={},
            reason="Test halt.",
        )
        assert result["overall_status"] == "halted_at_step_a"
        assert result["plan_step_b"] is None
        assert result["plan_step_c"] is None

    @patch("workflows.reindex_workflow.trigger_reindex", return_value={"status": "rejected"})
    @patch("workflows.reindex_workflow.create_index_template", return_value=_make_applied())
    def test_halts_at_step_b_if_rejected(self, mock_a, mock_b):
        result = run_reindex_workflow(
            source_index="logs-2024",
            destination_index="logs-opt",
            alias_name="logs-current",
            template_name="t",
            index_patterns=["t-*"],
            optimized_mappings={},
            optimized_settings={},
            reason="Test halt B.",
        )
        assert result["overall_status"] == "halted_at_step_b"
        assert result["plan_step_c"] is None

    @patch("workflows.reindex_workflow.update_alias", return_value={"status": "rejected"})
    @patch("workflows.reindex_workflow.get_reindex_task_status", return_value=_make_task_completed())
    @patch("workflows.reindex_workflow.trigger_reindex", return_value=_make_started())
    @patch("workflows.reindex_workflow.create_index_template", return_value=_make_applied())
    def test_halts_at_step_c_if_rejected(self, mock_a, mock_b, mock_status, mock_c):
        result = run_reindex_workflow(
            source_index="logs-2024",
            destination_index="logs-opt",
            alias_name="logs-current",
            template_name="t",
            index_patterns=["t-*"],
            optimized_mappings={},
            optimized_settings={},
            reason="Test halt C.",
        )
        assert result["overall_status"] == "halted_at_step_c"

    @patch("workflows.reindex_workflow.update_alias", return_value=_make_applied())
    @patch("workflows.reindex_workflow.get_reindex_task_status", return_value=_make_task_completed())
    @patch("workflows.reindex_workflow.trigger_reindex", return_value=_make_started())
    @patch("workflows.reindex_workflow.create_index_template", return_value=_make_applied())
    def test_reason_propagates_to_all_steps(self, mock_a, mock_b, mock_status, mock_c):
        run_reindex_workflow(
            source_index="src", destination_index="dst", alias_name="alias",
            template_name="t", index_patterns=["t-*"],
            optimized_mappings={}, optimized_settings={},
            reason="Wildcard field optimization.",
        )
        assert "Step A" in mock_a.call_args[1]["reason"]
        assert "Step B" in mock_b.call_args[1]["reason"]
        assert "Step C" in mock_c.call_args[1]["reason"]
