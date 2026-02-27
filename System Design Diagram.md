## System Design Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SELF-OPTIMIZING ELASTIC INFRA AGENT                         │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐        ┌──────────────────────────────────────────────────────┐
  │   main.py    │        │                  config/                             │
  │  CLI Entry   │───────▶│  settings.py (env vars)  tool_schemas.py (7 tools)   │
  └──────┬───────┘        └──────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                         SETUP LAYER                                          │
  │                                                                              │
  │  setup/bootstrap.py                    setup/docs_indexer.py                 │
  │  ├─ enable_stack_monitoring()          ├─ discover_docs_urls()               │
  │  ├─ verify_required_indices()          │    └─ _fetch_xml() → sitemap parse  │
  │  ├─ _create_index_metadata_index()     └─ build_knowledge_base()             │
  │  ├─ _flatten_mappings()                     ├─ crawl_and_index_elastic_docs()│
  │  └─ refresh_index_metadata()               ├─ _strip_html()                  │
  │                                             └─ _split_text()                 │
  └──────────────────────────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
  ┌──────────────────────┐              ┌───────────────────────────┐
  │  MONITORING CLUSTER  │              │  FAISS VECTOR INDEX       │
  │  .slowlog-* index    │              │  all-MiniLM-L6-v2 dim=384 │
  │  metrics-es.node-*   │              │  faiss_docs.index (file)  │
  │  index-metadata      │              └───────────────────────────┘
  └──────────┬───────────┘                        │
             │                                    │
             ▼                                    ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                         TOOLSET LAYER                                        │
  │                                                                              │
  │  tools/esql_tool.py             tools/search_tool.py                         │
  │  ├─ build_slowest_queries_esql()├─ search_elastic_docs()  ◀── FAISS query    │
  │  ├─ fetch_slowest_queries()     └─ build_docs_index()                        │
  │  ├─ fetch_node_metrics()                                                     │
  │  ├─ fetch_circuit_breaker_stats()   tools/execution_tool.py                  │
  │  ├─ fetch_index_metadata()          ├─ update_index_settings()               │
  │  └─ run_esql_query()                ├─ update_cluster_settings()             │
  │          │                          ├─ create_index_template()               │
  │          │ ES|QL REST               ├─ trigger_reindex()                     │
  │          ▼                          ├─ update_alias()                        │
  │  [Elasticsearch /_esql]             └─ get_reindex_task_status()             │
  └──────────────────────────────────────────────────────────────────────────────┘
             │                                    │
             ▼                                    ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                         AGENT LAYER                                          │
  │                                                                              │
  │  agent/loop.py                     agent/orchestrator.py                     │
  │  └─ start_scheduler()              ├─ run_optimization_cycle()               │
  │       └─ _cycle_job() ────────────▶├─ _dispatch_tool()                       │
  │          APScheduler interval      └─ sequencer                              │
  │                                              │                               │
  │  agent/diagnosis.py                          │                               │
  │  ├─ _detect_wildcard_anti_patterns()         │                               │
  │  ├─ _detect_circuit_breaker()                │                               │
  │  ├─ _detect_unbounded_aggregations()         ▼                               │
  │  ├─ _detect_deep_nesting()         agent/reasoning.py                        │
  │  ├─ _detect_script_queries()       ├─ SYSTEM_PROMPT                          │
  │  ├─ _detect_regexp_queries()       ├─ build_initial_message()                │
  │  ├─ _estimate_cardinality()        ├─ _call_anthropic()                      │
  │  ├─ _fetch_field_type_from_metadata│ └─ Claude 3.5 Sonnet                    │
  │  ├─ _compute_severity()            └─ _call_openai()                         │
  │  ├─ diagnose_slow_queries()              └─ GPT-4o                           │
  │  └─ build_diagnosis_context()                                                │
  └──────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                      WORKFLOW + SAFETY LAYER                                 │
  │                                                                              │
  │  workflows/approval.py                  workflows/reindex_workflow.py        │
  │  ├─ request_approval()                  └─ run_reindex_workflow()            │
  │  ├─ _cli_approval()    ◀── stdin             ├─ Plan Step A (create template)│
  │  ├─ _webhook_approval()◀── HTTP POST         ├─ Plan Step B (reindex)        │
  │  ├─ submit_approval_decision()               └─ Plan Step C (update alias)   │
  │  └─ get_pending_approvals()                                                  │
  └──────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                      ADVANCED LAYER                                          │
  │                                                                              │
  │  cost/cost_reasoner.py                  simulation/ephemeral_cluster.py      │
  │  ├─ evaluate_cost_tradeoff()            ├─ run_simulation()                  │
  │  ├─ get_billing_data()                  ├─ simulate_cluster_settings_change()│
  │  │   └─ _fetch_aws/gcp/azure_billing()  ├─ _start_ephemeral_cluster()        │
  │  └─ get_current_monthly_node_cost()     ├─ _wait_for_cluster()               │
  │                                         ├─ _benchmark_query()                │
  │                                         ├─ _seed_test_data()                 │
  │                                         └─ _stop_ephemeral_cluster()         │
  │                                              Docker: elasticsearch:8.13.0    │
  └──────────────────────────────────────────────────────────────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                              UI LAYER                                        │
  │  React JSX — 24 panels — Anthropic API (claude-sonnet-4-20250514)            │
  │  Every panel calls callAgent() with the exact system prompt and              │
  │  telemetry context its corresponding backend module would use.               │
  └──────────────────────────────────────────────────────────────────────────────┘
```

---