import json
from tools.esql_tool import (
    fetch_slowest_queries,
    fetch_node_metrics,
    fetch_circuit_breaker_stats,
    run_esql_query,
)
from tools.search_tool import search_elastic_docs
from tools.execution_tool import (
    update_index_settings,
    update_cluster_settings,
    create_index_template,
    trigger_reindex,
    update_alias,
)
from workflows.reindex_workflow import run_reindex_workflow
from agent.reasoning import call_reasoning_model, build_initial_message
from agent.diagnosis import diagnose_slow_queries, build_diagnosis_context
from cost.cost_reasoner import evaluate_cost_tradeoff
from simulation.ephemeral_cluster import run_simulation, simulate_cluster_settings_change
from config.settings import SIMULATION_ENABLED

MAX_TOOL_ROUNDS = 15


def run_optimization_cycle(time_range_hours: int = 1) -> dict:
    """
    Runs one complete optimization cycle.
    """
    cycle_log = {"steps": [], "actions_taken": [], "status": "running"}

    # ──Identify ────────────────────────────────────────────────────
    slow_query_result    = fetch_slowest_queries(time_range_hours)
    node_metric_result   = fetch_node_metrics(time_range_hours)
    circuit_breaker_result = fetch_circuit_breaker_stats()

    cycle_log["steps"].append({
        "step": "identify",
        "slow_queries_found": slow_query_result.get("meta", {}).get("row_count", 0),
        "node_metrics_found": node_metric_result.get("meta", {}).get("row_count", 0),
    })

    # ── Diagnose ────────────────────────────────────────────────────
    # Parse query structure, detect wildcard anti-patterns on high-cardinality
    # fields, CircuitBreakerExceptions, unbounded aggregations, etc.
    findings = diagnose_slow_queries(slow_query_result, index_name="*")
    diagnosis_text = build_diagnosis_context(findings)

    cycle_log["steps"].append({
        "step": "diagnose",
        "findings_count": len(findings),
        "critical_count": sum(1 for f in findings if f.severity == "critical"),
        "high_count": sum(1 for f in findings if f.severity == "high"),
        "diagnosis_summary": diagnosis_text[:500],
    })

    # ── Build reasoning model context─────────────────
    context = {
        "slow_queries": slow_query_result,
        "node_metrics": node_metric_result,
        "circuit_breakers": circuit_breaker_result,
        "diagnosis": diagnosis_text,
        "top_recommended_searches": list({
            rs for f in findings for rs in f.recommended_searches
        }),
    }
    messages = build_initial_message(context)

    # ── Agentic loop:Research →Propose → Execute
    tool_round = 0
    while tool_round < MAX_TOOL_ROUNDS:
        response = call_reasoning_model(messages)

        if response["type"] == "text":
            cycle_log["steps"].append({
                "step": "conclusion",
                "text": response["content"],
            })
            cycle_log["status"] = "completed"
            break

        if response["type"] == "tool_call":
            tool_name = response["tool_name"]
            tool_args = response["tool_args"]

            cycle_log["steps"].append({
                "step": f"tool_call_round_{tool_round}",
                "tool": tool_name,
                "args": tool_args,
            })

            tool_result = _dispatch_tool(tool_name, tool_args)

            cycle_log["actions_taken"].append({
                "tool": tool_name,
                "result_status": tool_result.get("status", "unknown"),
            })

            messages.append({
                "role": "assistant",
                "content": json.dumps({"tool_call": tool_name, "args": tool_args}),
            })
            messages.append({
                "role": "user",
                "content": f"Tool result for '{tool_name}':\n{json.dumps(tool_result, indent=2)}",
            })

        tool_round += 1

    if tool_round >= MAX_TOOL_ROUNDS:
        cycle_log["status"] = "max_rounds_reached"

    return cycle_log


def _dispatch_tool(tool_name: str, tool_args: dict) -> dict:
    """
    Routes a tool call from the reasoning model to the correct implementation.

    run_esql_query
    search_elastic_docs
    update_index_settings, update_cluster_settings,
               create_index_template, trigger_reindex, update_alias
    cost gate on reindex and scale actions
    simulation for both mapping changes and cluster settings changes
    """

    #Analytical Tool
    if tool_name == "run_esql_query":
        return run_esql_query(
            query=tool_args["query"],
            index_pattern=tool_args["index_pattern"],
            time_range_hours=tool_args.get("time_range_hours", 1),
        )

    # Knowledge Tool
    elif tool_name == "search_elastic_docs":
        results = search_elastic_docs(
            query=tool_args["query"],
            top_k=tool_args.get("top_k", 5),
        )
        return {"status": "ok", "results": results}

    #update index settings
    elif tool_name == "update_index_settings":
        return update_index_settings(
            index_name=tool_args["index_name"],
            settings=tool_args["settings"],
            reason=tool_args["reason"],
        )

    # cluster-level settings
    elif tool_name == "update_cluster_settings":
        #Simulate cluster settings change before applying to production
        if SIMULATION_ENABLED:
            sim_result = simulate_cluster_settings_change(
                proposed_persistent=tool_args.get("persistent"),
                proposed_transient=tool_args.get("transient"),
            )
            if not sim_result.get("improvement_confirmed"):
                return {
                    "status": "simulation_no_improvement",
                    "simulation": sim_result,
                    "message": (
                        "Simulation did not confirm performance improvement for the proposed "
                        "cluster settings. Change not applied."
                    ),
                }
        return update_cluster_settings(
            persistent=tool_args.get("persistent"),
            transient=tool_args.get("transient"),
            reason=tool_args["reason"],
        )

    #Plan Step A
    elif tool_name == "create_index_template":
        return create_index_template(
            template_name=tool_args["template_name"],
            index_patterns=tool_args["index_patterns"],
            mappings=tool_args["mappings"],
            settings=tool_args.get("settings", {}),
            reason=tool_args["reason"],
        )

    #Plan Step B / Execute
    elif tool_name == "trigger_reindex":
        #Simulate mapping/reindex change before applying
        if SIMULATION_ENABLED:
            sim_result = run_simulation(
                proposed_mappings=tool_args.get("mappings", {}),
                proposed_settings=tool_args.get("settings", {}),
            )
            if not sim_result.get("improvement_confirmed"):
                return {
                    "status": "simulation_no_improvement",
                    "simulation": sim_result,
                    "message": "Simulation did not confirm performance improvement. Reindex not triggered.",
                }

        #Cost gate — prefer query/mapping fix over node scaling
        cost_decision = evaluate_cost_tradeoff(action="reindex", context=tool_args)
        if not cost_decision.get("proceed"):
            return {
                "status": "cost_rejected",
                "cost_analysis": cost_decision,
                "message": "Cost analysis determined this action is not cost-effective.",
            }

        return trigger_reindex(
            source_index=tool_args["source_index"],
            destination_index=tool_args["destination_index"],
            query=tool_args.get("query"),
            reason=tool_args["reason"],
        )

    #Plan Step C
    elif tool_name == "update_alias":
        return update_alias(
            alias_name=tool_args["alias_name"],
            remove_index=tool_args["remove_index"],
            add_index=tool_args["add_index"],
            reason=tool_args["reason"],
        )

    else:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}
