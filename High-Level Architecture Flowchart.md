## High-Level Architecture Flowchart

```
         ┌─────────────┐
         │  Scheduler  │  APScheduler IntervalTrigger (LOOP_INTERVAL_SECONDS)
         └──────┬──────┘
                │ every N seconds
                ▼
         ┌─────────────┐
         │  Identify   │  ES|QL → slowlog + node metrics + circuit breakers
         └──────┬──────┘
                │ top-N slow queries
                ▼
         ┌─────────────┐
         │  Diagnose   │  6 anti-pattern detectors + cardinality check
         └──────┬──────┘
                │ severity + affected fields + recommended searches
                ▼
         ┌─────────────┐
         │  Research   │  FAISS vector search → elastic.co docs
         └──────┬──────┘
                │ best-practice documentation chunks
                ▼
         ┌─────────────┐
         │   Propose   │  Reasoning model (Claude/GPT-4o) → Plan A→B→C
         └──────┬──────┘
                │ structured optimization plan
                ▼
         ┌─────────────────────┐
         │   Cost Gate         │  evaluate_cost_tradeoff() vs node scaling cost
         └──────┬──────────────┘
                │ proceed / reject
                ▼
         ┌─────────────────────┐
         │   Simulation Gate   │  Docker ephemeral ES → benchmark before/after
         └──────┬──────────────┘
                │ improvement_confirmed = True / False
                ▼
         ┌─────────────────────┐
         │   Approval Gate     │  CLI stdin OR webhook POST → operator decision
         └──────┬──────────────┘
                │ approved
                ▼
         ┌─────────────┐
         │   Execute   │  execution_tool → Elasticsearch REST API
         └──────┬──────┘
                │ reindex / alias swap / settings / template
                ▼
         ┌─────────────┐
         │  Verify     │  get_reindex_task_status() → task polling
         └─────────────┘
```

---