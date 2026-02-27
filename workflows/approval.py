import json
import time
import hashlib
import httpx
from datetime import datetime, timezone
from config.settings import (
    APPROVAL_WEBHOOK_URL,
    APPROVAL_TIMEOUT_SECONDS,
)

# In-memory approval state (future action- backed by Redis or a DB).
_pending_approvals: dict[str, dict] = {}
_approval_results: dict[str, bool] = {}


def request_approval(
    action: str,
    target: str,
    payload: dict,
    reason: str,
) -> bool:
    """
    Sends an approval request for a proposed change and blocks until
    the operator approves or rejects, or until the timeout elapses.

    The agent must explain *why* it is proposing the change (reason field).
    If no webhook is configured, defaults to a CLI prompt for local operation.

    Args:
        action: The tool action name (e.g., 'trigger_reindex').
        target: The index, alias, or cluster target being changed.
        payload: The full change payload to display to the approver.
        reason: The agent's explanation for why this change is needed.

    Returns:
        True if approved, False if rejected or timed out.
    """
    approval_id = hashlib.sha256(
        f"{action}{target}{json.dumps(payload, sort_keys=True)}".encode()
    ).hexdigest()[:12]

    request = {
        "approval_id": approval_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "target": target,
        "payload": payload,
        "reason": reason,
    }

    _pending_approvals[approval_id] = request

    if APPROVAL_WEBHOOK_URL:
        return _webhook_approval(approval_id, request)
    else:
        return _cli_approval(approval_id, request)


def _cli_approval(approval_id: str, request: dict) -> bool:
    """
    Fallback approval via CLI prompt. Used when no webhook is configured.
    """
    print("\n" + "=" * 70)
    print("APPROVAL REQUIRED")
    print("=" * 70)
    print(f"ID:     {approval_id}")
    print(f"Action: {request['action']}")
    print(f"Target: {request['target']}")
    print(f"Reason: {request['reason']}")
    print("Payload:")
    print(json.dumps(request['payload'], indent=2))
    print("=" * 70)

    try:
        answer = input("Approve this change? [yes/no]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("Approval timed out. Rejecting.")
        return False

    approved = answer in ("yes", "y")
    _approval_results[approval_id] = approved
    _pending_approvals.pop(approval_id, None)

    if approved:
        print(f"Approved: {approval_id}")
    else:
        print(f"Rejected: {approval_id}")

    return approved


def _webhook_approval(approval_id: str, request: dict) -> bool:
    """
    Sends the approval request to a configured webhook and polls for the response.
    The webhook endpoint is responsible for notifying an operator (Slack, PagerDuty, etc.)
    and writing back the decision.
    """
    try:
        client = httpx.Client(timeout=30.0)
        client.post(APPROVAL_WEBHOOK_URL, json=request)
        client.close()
    except httpx.HTTPError as exc:
        print(f"Webhook delivery failed: {exc}. Falling back to CLI approval.")
        return _cli_approval(approval_id, request)

    deadline = time.time() + APPROVAL_TIMEOUT_SECONDS
    poll_url = f"{APPROVAL_WEBHOOK_URL}/status/{approval_id}"

    while time.time() < deadline:
        try:
            poll_client = httpx.Client(timeout=10.0)
            resp = poll_client.get(poll_url)
            poll_client.close()
            if resp.status_code == 200:
                data = resp.json()
                if data.get("decision") in ("approved", "rejected"):
                    approved = data["decision"] == "approved"
                    _approval_results[approval_id] = approved
                    _pending_approvals.pop(approval_id, None)
                    return approved
        except httpx.HTTPError:
            pass
        time.sleep(5)

    print(f"Approval timed out after {APPROVAL_TIMEOUT_SECONDS}s. Rejecting.")
    _approval_results[approval_id] = False
    _pending_approvals.pop(approval_id, None)
    return False


def get_pending_approvals() -> list[dict]:
    """Returns all approvals currently awaiting a decision."""
    return list(_pending_approvals.values())


def submit_approval_decision(approval_id: str, approved: bool) -> None:
    """
    Allows an external system (REST API, UI) to programmatically record an approval
    decision that the polling loop in _webhook_approval is waiting for.
    """
    _approval_results[approval_id] = approved
    _pending_approvals.pop(approval_id, None)
