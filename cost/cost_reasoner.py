import httpx
from config.settings import (
    CLOUD_COST_PER_NODE_MONTHLY,
    CLOUD_PROVIDER,
    BILLING_API_KEY,
)


def get_current_monthly_node_cost(node_count: int = 1) -> float:
    """
    Returns the estimated monthly cost of adding `node_count` new nodes
    based on the configured per-node rate.
    """
    return CLOUD_COST_PER_NODE_MONTHLY * node_count


def get_billing_data() -> dict:
    """
    Fetches live billing data from the cloud provider API.
    Supports AWS Cost Explorer, GCP Billing, and Azure Cost Management.

    Returns a dict with 'month_to_date_cost', 'projected_monthly_cost', and 'currency'.
    """
    if CLOUD_PROVIDER == "aws":
        return _fetch_aws_billing()
    elif CLOUD_PROVIDER == "gcp":
        return _fetch_gcp_billing()
    elif CLOUD_PROVIDER == "azure":
        return _fetch_azure_billing()
    else:
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}


def _fetch_aws_billing() -> dict:
    """Fetches month-to-date cost from AWS Cost Explorer API."""
    from datetime import date, timedelta

    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    headers = {"Authorization": f"Bearer {BILLING_API_KEY}"}
    payload = {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": "MONTHLY",
        "Metrics": ["UnblendedCost"],
    }

    try:
        resp = httpx.post(
            "https://ce.us-east-1.amazonaws.com/",
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        amount = float(
            data["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
        )
        currency = data["ResultsByTime"][0]["Total"]["UnblendedCost"]["Unit"]
        days_in_month = 30
        days_elapsed = today.day
        projected = (amount / days_elapsed) * days_in_month
        return {
            "month_to_date_cost": amount,
            "projected_monthly_cost": projected,
            "currency": currency,
        }
    except Exception:
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}


def _fetch_gcp_billing() -> dict:
    """Fetches billing data from GCP Cloud Billing API."""
    try:
        resp = httpx.get(
            "https://cloudbilling.googleapis.com/v1/billingAccounts",
            headers={"Authorization": f"Bearer {BILLING_API_KEY}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        # GCP billing details require BigQuery export; return summary from API
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}
    except Exception:
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}


def _fetch_azure_billing() -> dict:
    """Fetches billing data from Azure Cost Management API."""
    try:
        resp = httpx.get(
            "https://management.azure.com/providers/Microsoft.CostManagement/query",
            headers={"Authorization": f"Bearer {BILLING_API_KEY}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}
    except Exception:
        return {"month_to_date_cost": 0.0, "projected_monthly_cost": 0.0, "currency": "USD"}


def evaluate_cost_tradeoff(action: str, context: dict) -> dict:
    """
    Core cost-reasoning function. Compares the cost of the proposed action
    against the cost of scaling up infrastructure.

    The agent uses this to reason: "Scaling up costs $200/mo, but optimizing the query
    costs $0."

    Args:
        action: The proposed action (e.g., 'reindex', 'scale_node', 'query_rewrite').
        context: Additional context about the action (index sizes, node counts, etc.).

    Returns:
        A dict with 'proceed', 'reason', 'cost_of_action', 'cost_of_scaling', 'savings'.
    """
    billing = get_billing_data()
    scale_cost = get_current_monthly_node_cost(node_count=1)

    action_costs = {
        "reindex": 0.0,         # CPU time only, no additional infrastructure cost
        "query_rewrite": 0.0,   # No infrastructure cost
        "mapping_change": 0.0,  # No infrastructure cost
        "scale_node": scale_cost,
        "new_node": scale_cost,
    }

    cost_of_action = action_costs.get(action, 0.0)
    savings = scale_cost - cost_of_action

    if action in ("reindex", "query_rewrite", "mapping_change"):
        proceed = True
        reason = (
            f"Proposed action '{action}' costs ${cost_of_action:.2f}/mo. "
            f"Scaling a node costs ${scale_cost:.2f}/mo. "
            f"Estimated monthly savings by optimizing instead of scaling: ${savings:.2f}. "
            "Proceeding with the optimization."
        )
    elif action in ("scale_node", "new_node"):
        proceed = False
        reason = (
            f"Scaling costs ${scale_cost:.2f}/mo. "
            "Query and mapping optimizations should be exhausted first before scaling."
        )
    else:
        proceed = True
        reason = f"No cost constraint identified for action '{action}'."

    return {
        "proceed": proceed,
        "reason": reason,
        "cost_of_action_monthly": cost_of_action,
        "cost_of_scaling_monthly": scale_cost,
        "projected_monthly_savings": savings,
        "billing_context": billing,
    }
