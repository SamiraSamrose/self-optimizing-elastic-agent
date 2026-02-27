## System Design Diagram-short

```
┌───────────────────────────────────────────────────────────────────┐
│               SELF-OPTIMIZING ELASTIC INFRA AGENT                 │
│                                                                   │
│  CLI (main.py) ──▶ config/ (settings + tool schemas)              │
│                                                                   │
│  SETUP                                                            │
│  bootstrap.py ──▶ Monitoring Cluster (slowlog / node / metadata)  │
│  docs_indexer.py ──▶ FAISS Index (elastic.co docs vectors)        │
│                                                                   │
│  TOOLS                                                            │
│  esql_tool ──▶ ES|QL /_esql    search_tool ──▶ FAISS              │
│  execution_tool ──▶ Elasticsearch REST API                        │
│                                                                   │
│  AGENT LOOP (APScheduler)                                         │
│  loop ──▶ orchestrator ──▶ [Identify → Diagnose → Research        │
│                              → Propose → Execute]                 │
│  diagnosis.py (6 detectors + cardinality check)                   │
│  reasoning.py (Claude 3.5 Sonnet / GPT-4o)                        │
│                                                                   │
│  SAFETY GATE                                                      │
│  approval.py (CLI stdin / webhook) ──▶ execution_tool             │
│                                                                   │
│  ADVANCED                                                         │
│  cost_reasoner ──▶ billing API    sim ──▶ Docker ephemeral ES     │
│                                                                   │
│  UI: React 24 panels ──▶ Anthropic API (live agent reasoning)     │
└───────────────────────────────────────────────────────────────────┘
```

---