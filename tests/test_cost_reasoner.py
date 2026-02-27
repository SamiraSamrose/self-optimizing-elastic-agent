import pytest
from unittest.mock import patch
from cost.cost_reasoner import (
    get_current_monthly_node_cost,
    evaluate_cost_tradeoff,
)


class TestGetCurrentMonthlyNodeCost:
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_single_node_cost(self):
        assert get_current_monthly_node_cost(1) == 200.0

    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_multi_node_cost(self):
        assert get_current_monthly_node_cost(3) == 600.0

    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 150.0)
    def test_custom_rate(self):
        assert get_current_monthly_node_cost(2) == 300.0


class TestEvaluateCostTradeoff:
    #reindex costs $0, scaling costs $200 — agent must choose reindex

    @patch("cost.cost_reasoner.get_billing_data", return_value={"month_to_date_cost": 500.0, "projected_monthly_cost": 1000.0, "currency": "USD"})
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_reindex_proceeds(self, mock_billing):
        result = evaluate_cost_tradeoff("reindex", {})
        assert result["proceed"] is True
        assert result["cost_of_action_monthly"] == 0.0
        assert result["projected_monthly_savings"] == 200.0

    @patch("cost.cost_reasoner.get_billing_data", return_value={"month_to_date_cost": 500.0, "projected_monthly_cost": 1000.0, "currency": "USD"})
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_query_rewrite_proceeds(self, mock_billing):
        result = evaluate_cost_tradeoff("query_rewrite", {})
        assert result["proceed"] is True
        assert result["cost_of_action_monthly"] == 0.0

    @patch("cost.cost_reasoner.get_billing_data", return_value={"month_to_date_cost": 500.0, "projected_monthly_cost": 1000.0, "currency": "USD"})
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_mapping_change_proceeds(self, mock_billing):
        result = evaluate_cost_tradeoff("mapping_change", {})
        assert result["proceed"] is True

    @patch("cost.cost_reasoner.get_billing_data", return_value={"month_to_date_cost": 500.0, "projected_monthly_cost": 1000.0, "currency": "USD"})
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_scale_node_rejected(self, mock_billing):
        # Scaling costs $200/mo — agent rejects it in favour of optimizations
        result = evaluate_cost_tradeoff("scale_node", {})
        assert result["proceed"] is False
        assert result["cost_of_action_monthly"] == 200.0

    @patch("cost.cost_reasoner.get_billing_data", return_value={"month_to_date_cost": 500.0, "projected_monthly_cost": 1000.0, "currency": "USD"})
    @patch("cost.cost_reasoner.CLOUD_COST_PER_NODE_MONTHLY", 200.0)
    def test_result_has_all_keys(self, mock_billing):
        result = evaluate_cost_tradeoff("reindex", {})
        for key in ("proceed", "reason", "cost_of_action_monthly", "cost_of_scaling_monthly", "projected_monthly_savings", "billing_context"):
            assert key in result
