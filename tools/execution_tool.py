from elasticsearch import Elasticsearch
from config.settings import (
    ELASTICSEARCH_URL,
    ELASTICSEARCH_API_KEY,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
)
from workflows.approval import request_approval


def _get_client() -> Elasticsearch:
    if ELASTICSEARCH_API_KEY:
        return Elasticsearch(ELASTICSEARCH_URL, api_key=ELASTICSEARCH_API_KEY)
    return Elasticsearch(
        ELASTICSEARCH_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


def update_index_settings(index_name: str, settings: dict, reason: str) -> dict:
    """
    Implementation Example: Updates settings or mappings on an existing index.
    Requires approval before applying. 

    Args:
        index_name: Target index.
        settings: Dict with 'settings' and/or 'mappings' keys.
        reason: Agent's explanation of why this change is necessary.

    Returns:
        Result from Elasticsearch.
    """
    approved = request_approval(
        action="update_index_settings",
        target=index_name,
        payload=settings,
        reason=reason,
    )
    if not approved:
        return {"status": "rejected", "message": "Change was not approved."}

    client = _get_client()
    results = {}

    if "settings" in settings:
        resp = client.indices.put_settings(
            index=index_name,
            body=settings["settings"],
        )
        results["settings"] = resp.body

    if "mappings" in settings:
        resp = client.indices.put_mapping(
            index=index_name,
            body=settings["mappings"],
        )
        results["mappings"] = resp.body

    return {"status": "applied", "results": results}


def update_cluster_settings(persistent: dict = None, transient: dict = None, reason: str = "") -> dict:
    """
    Updates cluster-level settings via _cluster/settings.
    Used for breaker limit adjustments (e.g., indices.breaker.total.limit).

    Requires approval before applying.
    """
    payload = {}
    if persistent:
        payload["persistent"] = persistent
    if transient:
        payload["transient"] = transient

    approved = request_approval(
        action="update_cluster_settings",
        target="_cluster/settings",
        payload=payload,
        reason=reason,
    )
    if not approved:
        return {"status": "rejected", "message": "Change was not approved."}

    client = _get_client()
    resp = client.cluster.put_settings(body=payload)
    return {"status": "applied", "response": resp.body}


def create_index_template(
    template_name: str,
    index_patterns: list[str],
    mappings: dict,
    settings: dict = None,
    reason: str = "",
) -> dict:
    """
    PlanA: Creates a new index template with optimized field mappings.
    Called when the agent proposes a mapping change (e.g., keyword → wildcard field type).

    Requires approval.
    """
    body = {
        "index_patterns": index_patterns,
        "template": {
            "mappings": mappings,
        }
    }
    if settings:
        body["template"]["settings"] = settings

    approved = request_approval(
        action="create_index_template",
        target=template_name,
        payload=body,
        reason=reason,
    )
    if not approved:
        return {"status": "rejected", "message": "Change was not approved."}

    client = _get_client()
    resp = client.indices.put_index_template(name=template_name, body=body)
    return {"status": "applied", "response": resp.body}


def trigger_reindex(
    source_index: str,
    destination_index: str,
    query: dict = None,
    reason: str = "",
) -> dict:
    """
    PlanB/Execute: Triggers an Elasticsearch _reindex operation.
    This is a destructive action and always requires approval.

    Args:
        source_index: Source index name.
        destination_index: New index with optimized mappings.
        query: Optional filter query. Defaults to match_all.
        reason: The agent's explanation for why reindexing is needed.
    """
    if query is None:
        query = {"match_all": {}}

    body = {
        "source": {
            "index": source_index,
            "query": query,
        },
        "dest": {
            "index": destination_index,
        }
    }

    approved = request_approval(
        action="trigger_reindex",
        target=f"{source_index} → {destination_index}",
        payload=body,
        reason=reason,
    )
    if not approved:
        return {"status": "rejected", "message": "Reindex was not approved."}

    client = _get_client()
    resp = client.reindex(body=body, wait_for_completion=False)
    return {
        "status": "started",
        "task_id": resp.body.get("task"),
        "response": resp.body,
    }


def update_alias(
    alias_name: str,
    remove_index: str,
    add_index: str,
    reason: str = "",
) -> dict:
    """
    PlanC: Updates an index alias to point to the newly reindexed index.
    Requires approval.
    """
    actions = [
        {"remove": {"index": remove_index, "alias": alias_name}},
        {"add": {"index": add_index, "alias": alias_name}},
    ]

    approved = request_approval(
        action="update_alias",
        target=alias_name,
        payload={"actions": actions},
        reason=reason,
    )
    if not approved:
        return {"status": "rejected", "message": "Alias update was not approved."}

    client = _get_client()
    resp = client.indices.update_aliases(body={"actions": actions})
    return {"status": "applied", "response": resp.body}


def get_reindex_task_status(task_id: str) -> dict:
    """
    Polls the status of an async reindex task started by trigger_reindex.
    """
    client = _get_client()
    resp = client.tasks.get(task_id=task_id)
    return resp.body
