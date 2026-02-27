import time
from tools.execution_tool import (
    create_index_template,
    trigger_reindex,
    update_alias,
    get_reindex_task_status,
)


def run_reindex_workflow(
    source_index: str,
    destination_index: str,
    alias_name: str,
    template_name: str,
    index_patterns: list[str],
    optimized_mappings: dict,
    optimized_settings: dict,
    reason: str,
    poll_interval_seconds: int = 30,
    max_wait_seconds: int = 3600,
) -> dict:
    """
    Executes the full three-step optimization plan proposed by the agent.

    Plan A — Create index template with optimized mappings.
    Plan B — Trigger reindex from source to destination.
    Plan C — Swap the alias to the new index.

    Each step requires approval via the approval workflow before execution.

    Args:
        source_index: Existing index with suboptimal mappings.
        destination_index: New index that will receive the reindexed data.
        alias_name: The alias currently pointing at source_index.
        template_name: Name for the new index template.
        index_patterns: Patterns the template applies to.
        optimized_mappings: The improved field mappings to apply.
        optimized_settings: Index settings for the new template.
        reason: Agent's explanation of why this workflow is being triggered.
        poll_interval_seconds: How often to poll the reindex task status.
        max_wait_seconds: Maximum time to wait for reindex to complete.

    Returns:
        A dict summarizing the outcome of each step.
    """
    results = {
        "plan_step_a": None,
        "plan_step_b": None,
        "plan_step_c": None,
        "overall_status": "incomplete",
    }

    # Plan A: Create the new index template with optimized mappings
    step_a_result = create_index_template(
        template_name=template_name,
        index_patterns=index_patterns,
        mappings=optimized_mappings,
        settings=optimized_settings,
        reason=f"[Step A] {reason}",
    )
    results["plan_step_a"] = step_a_result

    if step_a_result.get("status") != "applied":
        results["overall_status"] = "halted_at_step_a"
        return results

    # Plan step B: Trigger the reindex
    step_b_result = trigger_reindex(
        source_index=source_index,
        destination_index=destination_index,
        reason=f"[Step B] {reason}",
    )
    results["plan_step_b"] = step_b_result

    if step_b_result.get("status") != "started":
        results["overall_status"] = "halted_at_step_b"
        return results

    # Poll for reindex task completion
    task_id = step_b_result.get("task_id")
    if task_id:
        elapsed = 0
        while elapsed < max_wait_seconds:
            task_status = get_reindex_task_status(task_id)
            completed = task_status.get("completed", False)
            if completed:
                results["reindex_task_status"] = task_status
                break
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds
        else:
            results["overall_status"] = "reindex_timeout"
            return results

    # Plan step C: Update the alias to point at the new index
    step_c_result = update_alias(
        alias_name=alias_name,
        remove_index=source_index,
        add_index=destination_index,
        reason=f"[Step C] {reason}",
    )
    results["plan_step_c"] = step_c_result

    if step_c_result.get("status") == "applied":
        results["overall_status"] = "completed"
    else:
        results["overall_status"] = "halted_at_step_c"

    return results
