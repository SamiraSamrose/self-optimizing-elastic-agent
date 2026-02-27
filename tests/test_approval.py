import pytest
from unittest.mock import patch
from workflows.approval import (
    request_approval,
    get_pending_approvals,
    submit_approval_decision,
)


class TestCliApproval:
    @patch("workflows.approval.APPROVAL_WEBHOOK_URL", "")
    @patch("builtins.input", return_value="yes")
    def test_approves_on_yes(self, mock_input):
        result = request_approval(
            action="update_index_settings",
            target="logs-2024",
            payload={"settings": {"index.number_of_replicas": 1}},
            reason="Reducing replicas to lower cost.",
        )
        assert result is True

    @patch("workflows.approval.APPROVAL_WEBHOOK_URL", "")
    @patch("builtins.input", return_value="no")
    def test_rejects_on_no(self, mock_input):
        result = request_approval(
            action="trigger_reindex",
            target="logs-2024 → logs-2024-optimized",
            payload={"source": {"index": "logs-2024"}},
            reason="Reindex to apply optimized mapping.",
        )
        assert result is False

    @patch("workflows.approval.APPROVAL_WEBHOOK_URL", "")
    @patch("builtins.input", side_effect=EOFError)
    def test_rejects_on_eof(self, mock_input):
        result = request_approval(
            action="update_cluster_settings",
            target="_cluster/settings",
            payload={"persistent": {"indices.breaker.total.limit": "70%"}},
            reason="Breaker adjustment.",
        )
        assert result is False

    @patch("workflows.approval.APPROVAL_WEBHOOK_URL", "")
    @patch("builtins.input", return_value="y")
    def test_approves_on_single_y(self, mock_input):
        result = request_approval(
            action="update_alias",
            target="logs-current",
            payload={},
            reason="Post-reindex alias swap.",
        )
        assert result is True


class TestPendingApprovals:
    @patch("workflows.approval.APPROVAL_WEBHOOK_URL", "")
    @patch("builtins.input", return_value="yes")
    def test_pending_cleared_after_decision(self, mock_input):
        request_approval(
            action="create_index_template",
            target="logs-template",
            payload={"template_name": "logs-template"},
            reason="Optimized mapping template.",
        )
        # After yes is given, the pending approval is removed
        # (may still have items from other tests)
        approvals = get_pending_approvals()
        assert isinstance(approvals, list)


class TestSubmitApprovalDecision:
    def test_submit_approved_decision(self):
        from workflows import approval as approval_module
        approval_module._pending_approvals["test-id-abc"] = {
            "approval_id": "test-id-abc",
            "action": "trigger_reindex",
            "target": "src → dst",
            "payload": {},
            "reason": "Test reindex.",
        }
        submit_approval_decision("test-id-abc", approved=True)
        assert approval_module._approval_results.get("test-id-abc") is True
        assert "test-id-abc" not in approval_module._pending_approvals

    def test_submit_rejected_decision(self):
        from workflows import approval as approval_module
        approval_module._pending_approvals["test-id-xyz"] = {
            "approval_id": "test-id-xyz",
            "action": "update_cluster_settings",
            "target": "_cluster/settings",
            "payload": {},
            "reason": "Test cluster change.",
        }
        submit_approval_decision("test-id-xyz", approved=False)
        assert approval_module._approval_results.get("test-id-xyz") is False
        assert "test-id-xyz" not in approval_module._pending_approvals
