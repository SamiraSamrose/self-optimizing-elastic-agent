# Self-Optimizing Elastic Infra Agent

> An autonomous SRE system that monitors Elasticsearch clusters, diagnoses query performance bottlenecks, researches documentation-backed fixes, validates proposed changes through cost and simulation gates and executes approved changes through a gated pipeline — without manual SRE intervention per cycle.

---

## Links
- **Source Code**: https://github.com/SamiraSamrose/self-optimizing-elastic-agent
- **Video Demo**: https://youtu.be/6l29SX8ex5c

---

## Overview

Elasticsearch clusters at scale develop query performance issues that accumulate silently in slowlogs until they cause production incidents. SRE teams spend repetitive hours diagnosing the same anti-patterns — wildcard queries, unbounded aggregations, circuit breaker saturation — and manually writing reindex plans. The project exists to automate that entire detection-to-execution cycle.

The agent monitors an Elasticsearch cluster's slowlog on a schedule, runs six structural anti-pattern detectors against the slowest queries, searches a vector index of Elastic documentation for the relevant fix, generates a three-step optimization plan using an LLM, validates it through cost and simulation gates, and executes the approved changes against the production cluster.

Elasticsearch clusters degrade silently. Wildcard queries, regexp filters, Painless scripts and unbounded aggregations accumulate in slowlogs while engineers investigate manually and apply fixes reactively. This agent automates the full detection-to-execution cycle on a configurable schedule.

**What the agent does per cycle:**

1. Queries the monitoring cluster slowlog via ES|QL to surface the top-N slowest queries
2. Runs six structural anti-pattern detectors against each query's JSON body
3. Estimates field cardinality via live aggregation to confirm severity
4. Retrieves best-practice documentation from a FAISS vector index of elastic.co
5. Composes a structured telemetry context and sends it to a reasoning LLM (Claude or GPT-4o)
6. Evaluates the proposed plan against real cloud billing cost before proceeding
7. Benchmarks the proposed change on a Docker ephemeral Elasticsearch cluster
8. Routes every destructive action through an operator approval gate
9. Executes approved changes against the production cluster via the Elasticsearch REST API

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│             SELF-OPTIMIZING ELASTIC INFRA AGENT                     │
└─────────────────────────────────────────────────────────────────────┘

  main.py (CLI) ──▶ config/settings.py + config/tool_schemas.py

  ┌────────────────────────────────────────────────────────────────┐
  │  SETUP LAYER                                                   │
  │  setup/bootstrap.py                setup/docs_indexer.py       │
  │  ├─ enable_stack_monitoring()      ├─ discover_docs_urls()     │
  │  ├─ verify_required_indices()      ├─ build_knowledge_base()   │
  │  └─ refresh_index_metadata()       └─ _strip_html()            │
  │       └─ _flatten_mappings()           _split_text()           │
  └────────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
  Monitoring Cluster                     FAISS IndexFlatIP
  .slowlog-* / node-metrics              all-MiniLM-L6-v2 (dim=384)
  index-metadata                         faiss_docs.index

  ┌────────────────────────────────────────────────────────────────┐
  │  TOOLSET LAYER                                                 │
  │  tools/esql_tool.py       tools/search_tool.py                 │
  │  tools/execution_tool.py  ← all actions gated by approval.py   │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │  AGENT LAYER                                                   │
  │  agent/loop.py (APScheduler)                                   │
  │  └─▶ agent/orchestrator.py :: run_optimization_cycle()         │
  │                 Identify ──▶ esql_tool                         │
  │                 Diagnose ──▶ agent/diagnosis.py (6 detectors)  │
  │                 Research ──▶ search_tool (FAISS)               │
  │                 Propose  ──▶ agent/reasoning.py (Claude/GPT)   │
  │                 Execute  ──▶ approval gate ──▶ execution_tool  │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │  SAFETY LAYER                                                  │
  │  workflows/approval.py    workflows/reindex_workflow.py        │
  │  ├─ _cli_approval()       └─ run_reindex_workflow()            │
  │  └─ _webhook_approval()        Plan A → B → C (sequenced)      │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │  ADVANCED LAYER                                                │
  │  cost/cost_reasoner.py          simulation/ephemeral_cluster.py│
  │  ├─ evaluate_cost_tradeoff()    ├─ run_simulation()            │
  │  ├─ get_billing_data()          └─ simulate_cluster_settings_  │
  │  └─ get_current_monthly_        change()                       │
  │     node_cost()                 Docker elasticsearch:8.13.0    │
  └────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Step 1 — Bootstrap (`setup/bootstrap.py`)

`enable_stack_monitoring()` activates xpack Stack Monitoring on the production cluster and sets slowlog thresholds (`warn: 2s`, `info: 1s`) on all data indices. `refresh_index_metadata()` crawls all production index mappings via the Elasticsearch `_mapping` API, flattens nested field hierarchies with `_flatten_mappings()` and bulk-writes field records to a custom `index-metadata` index in the monitoring cluster. This index serves as a low-cost mapping cache used by the diagnosis layer on every cycle.

### Step 2B — Knowledge Base (`setup/docs_indexer.py`)

`discover_docs_urls()` fetches elastic.co sitemap XML, parses child sitemaps and filters discovered URLs to documentation sections matching `_RELEVANT_URL_PREFIXES`. `build_knowledge_base()` crawls each URL, strips HTML tags with `_strip_html()`, splits text into overlapping chunks with `_split_text()`, encodes each chunk using `SentenceTransformer('all-MiniLM-L6-v2')` and stores the resulting `(N, 384)` tensor in a FAISS `IndexFlatIP`. The index is persisted to `faiss_docs.index`.

### Step 3 — Reasoning Engine (`agent/reasoning.py`)

`SYSTEM_PROMPT` defines the agent's role, constraints and decision principles. `build_initial_message()` composes a structured user-role message containing the top-N slow queries, node metrics per node (CPU/heap/disk), circuit breaker stats, structured diagnosis findings and recommended knowledge search queries. This message is passed to `call_reasoning_model()`, which routes to `_call_anthropic()` or `_call_openai()` depending on `REASONING_PROVIDER`.

### Step 4 — Optimization Loop (`agent/orchestrator.py`)

`run_optimization_cycle()` executes five sequential steps by dispatching tool calls via `_dispatch_tool()`:

|--------------|--------------------------------------------------------------------------------------|-----------------------|
|      Step    |                              Function                                                |        Tool           |
|--------------|--------------------------------------------------------------------------------------|-----------------------|
| 4.1 Identify | `fetch_slowest_queries()` + `fetch_node_metrics()` + `fetch_circuit_breaker_stats()` | `run_esql_query`      |
| 4.2 Diagnose | `diagnose_slow_queries()` — 6 detectors + `_estimate_cardinality()`                  | internal              |
| 4.3 Research | `search_elastic_docs()` — FAISS vector search                                        | `search_elastic_docs` |
| 4.4 Propose  | `call_reasoning_model()` — Plan A → B → C                                            | LLM                   |
| 4.5 Execute  | `_dispatch_tool()` → `request_approval()`                                            | `trigger_reindex`     |
|--------------|--------------------------------------------------------------------------------------|-----------------------|

### Step 5 — Advanced Gates

**Cost Gate** (`cost/cost_reasoner.py`): `evaluate_cost_tradeoff()` compares the proposed action cost against `get_current_monthly_node_cost()` using real billing data from `get_billing_data()` (AWS/GCP/Azure billing APIs). Actions with zero recurring cost proceed; node-scaling recommendations are rejected unless no optimization path exists.

**Simulation Gate** (`simulation/ephemeral_cluster.py`): `_start_ephemeral_cluster()` provisions a Docker single-node Elasticsearch 8.13.0 container on port 9299. `_seed_test_data()` bulk-indexes 500 representative documents. `_benchmark_query()` measures query latency over `BENCHMARK_ITERATIONS` before and after the proposed change. `_stop_ephemeral_cluster()` removes the container. `improvement_confirmed` must be `True` for the action to proceed to the approval gate.

---

## Technology Stack

|-----------------|---------------------------------------------------------------------------|
|     Category    |                           Technology                                      |
|-----------------|---------------------------------------------------------------------------|
| Language        | Python 3.11+                                                              |
| Frontend        | React (JSX), IBM Plex Mono, Barlow Condensed                              |
| LLM Providers   | Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`), OpenAI GPT-4o |
| Vector Search   | FAISS `IndexFlatIP`                                                       |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` (dim=384)                        |
| Database        | Elasticsearch 8.13+ (production cluster, monitoring cluster)              |
| Custom Indices  | `index-metadata`, `faiss_docs.index` (file)                               |
| Query Engine    | Elasticsearch ES\|QL (`/_esql`)                                           |
| Scheduler       | APScheduler 3.10+ `IntervalTrigger`                                       |
| Simulation      | Docker SDK (`elasticsearch:8.13.0`)                                       |
| HTTP Client     | `elasticsearch-py`, `requests`                                            |
| HTML Parsing    | BeautifulSoup4                                                            |
| Testing         | pytest                                                                    |
| APIs            | Anthropic Messages API, OpenAI Chat Completions API,                      |
|                 | AWS/GCP/Azure Billing APIs, Elasticsearch REST API                        |
|-----------------|---------------------------------------------------------------------------|

---

## Installation

### Prerequisites

- Python 3.11+
- Docker (for simulation gate)
- Access to an Elasticsearch 8.x cluster
- A separate monitoring Elasticsearch cluster (can be the same cluster in development)
- Anthropic API key or OpenAI API key

### Install

```bash
git clone https://github.com/SamiraSamrose/self-optimizing-elastic-agent.git
cd self-optimizing-elastic-agent

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### requirements.txt

```
elasticsearch>=8.13.0
anthropic>=0.25.0
openai>=1.30.0
sentence-transformers>=2.7.0
faiss-cpu>=1.8.0
apscheduler>=3.10.4
requests>=2.32.0
beautifulsoup4>=4.12.0
docker>=7.1.0
python-dotenv>=1.0.0
pytest>=8.2.0
```

---

## Configuration

Copy `.env.example` to `.env` and populate all required values.

```bash
cp .env.example .env
```

### All 23 Settings

|-------------------------------|---------------|-----------------------------------------------------------|
|          Setting              |     Source    |                      Description                          |
|-------------------------------|---------------|-----------------------------------------------------------|
| `ELASTICSEARCH_URL`           | `.env`        | Production cluster URL                                    |
| `ELASTICSEARCH_API_KEY`       | `.env`        | Production cluster API key                                |
| `MONITORING_CLUSTER_URL`      | `.env`        | Monitoring cluster URL (must be separate from production) |
| `MONITORING_API_KEY`          | `.env`        | Monitoring cluster API key                                |
| `SLOWLOG_INDEX_PATTERN`       | `settings.py` | `.ds-elasticsearch.slowlog-*`                             |
| `NODE_METRICS_INDEX_PATTERN`  | `settings.py` | `metrics-elasticsearch.node-*`                            |
| `INDEX_METADATA_INDEX`        | `settings.py` | `index-metadata`                                          |
| `REASONING_PROVIDER`          | `.env`        | `anthropic` or `openai`                                   |
| `ANTHROPIC_MODEL`             | `settings.py` | `claude-3-5-sonnet-20241022`                              |
| `OPENAI_MODEL`                | `settings.py` | `gpt-4o`                                                  |
| `DOCS_VECTOR_INDEX`           | `.env`        | Path to `faiss_docs.index` file                           |
| `EMBEDDING_MODEL`             | `settings.py` | `all-MiniLM-L6-v2`                                        |
| `LOOP_INTERVAL_SECONDS`       | `.env`        | Scheduler interval (default: `3600`)                      |
| `TOP_SLOW_QUERIES_LIMIT`      | `settings.py` | Number of slow queries to analyze per cycle (default: `5`)|
| `APPROVAL_WEBHOOK_URL`        | `.env`        | Webhook URL for `_webhook_approval()`                     |
| `APPROVAL_TIMEOUT_SECONDS`    | `settings.py` | Webhook polling timeout (default: `300`)                  |
| `CLOUD_COST_PER_NODE_MONTHLY` | `.env`        | USD cost per node per month for cost gate                 |
| `BILLING_API_KEY`             | `.env`        | Cloud billing API key (AWS/GCP/Azure)                     |
| `SIMULATION_ENABLED`          | `.env`        | Enable Docker simulation gate (`true`/`false`)            |
| `BENCHMARK_ITERATIONS`        | `settings.py` | Benchmark iterations per run (default: `10`)              |
| `EPHEMERAL_CLUSTER_URL`       | `.env`        | Leave empty — agent provisions via Docker SDK             |
| `CLOUD_PROVIDER`              | `.env`        | `aws`, `gcp`, or `azure`                                  |
| `APPROVAL_MODE`               | `.env`        | `webhook` or `cli`                                        |
|-------------------------------|---------------|-----------------------------------------------------------|

---

## Usage

### Bootstrap

Run once before the first optimization cycle. Configures Stack Monitoring, slowlog thresholds and populates the `index-metadata` index.

```bash
python main.py bootstrap
```

### Build Knowledge Base

Crawls elastic.co documentation, chunks text, embeds using `all-MiniLM-L6-v2` and writes FAISS index to disk. Run once and re-run when Elastic releases major documentation updates.

```bash
python main.py build-kb --max-urls 2000 --chunk-size 500 --chunk-overlap 50
```

### Run a Single Optimization Cycle

```bash
python main.py run-cycle --hours 1
```

`--hours` sets the slowlog lookback window.

### Start the Scheduled Loop

```bash
python main.py start-loop
```

Starts APScheduler with `IntervalTrigger(seconds=LOOP_INTERVAL_SECONDS)`. The first cycle runs immediately. Use `Ctrl+C` to stop — the scheduler calls `scheduler.shutdown()` cleanly.

### Index Specific Documentation URLs

```bash
python main.py index-docs --urls-file docs_urls.txt
```

Crawls and indexes a user-supplied list of URLs into the existing FAISS index.

---

## Agent Pipeline — Step by Step

### Step 4.1 — Identify

`fetch_slowest_queries()` runs the following ES|QL against the monitoring cluster:

```esql
FROM .ds-elasticsearch.slowlog-*
| WHERE @timestamp >= "<now - time_range_hours>"
| STATS avg_duration = AVG(event.duration), count = COUNT() BY statement
| WHERE count > 100
| SORT avg_duration DESC
| LIMIT 5
```

`fetch_node_metrics()` and `fetch_circuit_breaker_stats()` query `metrics-elasticsearch.node-*` for CPU, heap, disk I/O and circuit breaker usage per node.

### Step 4.2 — Diagnose

`diagnose_slow_queries()` runs six structural detectors against each query's JSON body:

See [Anti-Pattern Detection](#anti-pattern-detection) for detector details.

`_estimate_cardinality()` runs a live cardinality aggregation on the detected field to confirm uniqueness before flagging the query. Fields with estimated cardinality below 1,000 are not flagged for wildcard anti-patterns.

`_compute_severity()` scores each finding `CRITICAL / HIGH / MEDIUM / LOW` based on average query duration and anti-pattern type.

`build_diagnosis_context()` assembles all findings into a structured dict passed to `build_initial_message()`.

### Step 4.3 — Research

`_dispatch_tool('search_elastic_docs')` encodes the recommended knowledge query using `all-MiniLM-L6-v2` and searches the FAISS `IndexFlatIP` by inner product similarity. Returns the top-k documentation chunks with score, title, URL and text.

### Step 4.4 — Propose

`call_reasoning_model()` passes the composed `build_initial_message()` context to the configured LLM with `SYSTEM_PROMPT`. The model returns a structured three-step plan:

- **Plan A** — `create_index_template()` with corrected field mappings
- **Plan B** — `trigger_reindex()` from source to destination index
- **Plan C** — `update_alias()` for zero-downtime cutover

### Step 4.5 — Execute

Each plan step dispatches through `_dispatch_tool()` → `request_approval()`. No Elasticsearch endpoint is called until the operator approves via `submit_approval_decision()`.

---

## Anti-Pattern Detection

`agent/diagnosis.py` implements six structural detectors. All detectors operate on the raw query JSON body — no execution required.

|------------------------------------|--------------------------------------------------------------|------------------|
|              Detector              |                   Condition                                  | Default Severity |
|------------------------------------|--------------------------------------------------------------|------------------|
| `_detect_wildcard_anti_patterns()` | `wildcard` query on `keyword` field with cardinality > 1,000 | CRITICAL         |
| `_detect_regexp_queries()`         | Any `regexp` query clause present                            | HIGH             |
| `_detect_script_queries()`         | Any `script` query or `script_score` present                 | HIGH             |
| `_detect_unbounded_aggregations()` | `terms` aggregation without explicit `size` limit            | HIGH             |
| `_detect_deep_nesting()`           | `nested` query nesting depth > 2 levels                      | MEDIUM           |
| `_detect_circuit_breaker()`        | Circuit breaker utilization > 70% on any data node           | HIGH             |
|------------------------------------|--------------------------------------------------------------|------------------|

`_fetch_field_type_from_metadata()` resolves the field type from the `index-metadata` index before firing wildcard and regexp detectors, preventing false positives on `text` and `wildcard` typed fields.

---

## Safety Gates

Every action that modifies the production cluster passes through three mandatory gates in sequence:

```
LLM Proposal
     │
     ▼
┌─────────────┐
│  Cost Gate  │  evaluate_cost_tradeoff()
│             │  action_cost < node_scaling_cost → PROCEED
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Simulation Gate │  run_simulation() / simulate_cluster_settings_change()
│                  │  improvement_confirmed = True → PROCEED
└──────┬───────────┘
       │
       ▼
┌───────────────────┐
│  Approval Gate    │  request_approval() → operator decision
│                   │  _webhook_approval() or _cli_approval()
└──────┬────────────┘
       │ approved
       ▼
  execution_tool.py → Elasticsearch REST API
```

The execution tool never calls any Elasticsearch endpoint without a recorded `submit_approval_decision()` result.

---

## Tool Schemas

`config/tool_schemas.py` defines `ALL_TOOL_SCHEMAS` — the 7 tool definitions passed to the reasoning model. The orchestrator's `_dispatch_tool()` routes on `name`.

|---------------------------|--------------------------------------------|
|          Tool             |       Elasticsearch Endpoint               |
|---------------------------|--------------------------------------------|
| `run_esql_query`          | `POST /_esql`                              |
| `search_elastic_docs`     | FAISS (local)                              |
| `update_index_settings`   | `PUT /{index}/_settings`                   |
| `update_cluster_settings` | `PUT /_cluster/settings`                   |
| `create_index_template`   | `PUT /_index_template/{name}`              |
| `trigger_reindex`         | `POST /_reindex?wait_for_completion=false` |
| `update_alias`            | `POST /_aliases`                           |
|---------------------------|--------------------------------------------|

`get_reindex_task_status()` polls `GET /_tasks/{task_id}` to monitor active reindex operations.

---

## Approval System

### Webhook Mode (`APPROVAL_MODE=webhook`)

`_webhook_approval()` POSTs the following payload to `APPROVAL_WEBHOOK_URL`:

```json
{
  "approval_id": "appr_<uuid>",
  "action": "trigger_reindex",
  "target": "logs-2024 → logs-2024-optimized",
  "reason": "Switching user_id to wildcard field type.",
  "payload": { "source_index": "logs-2024", "destination_index": "logs-2024-optimized" },
  "expires_at": "<ISO 8601 timestamp>"
}
```

The agent polls for a decision every 5 seconds up to `APPROVAL_TIMEOUT_SECONDS`. On timeout, the action is rejected.

### CLI Mode (`APPROVAL_MODE=cli`)

`_cli_approval()` prints the approval request to stdout and blocks on `input()` until the operator enters `yes` or `no`.

### Decision Recording

`submit_approval_decision(approval_id, approved, reason="")` records the decision with timestamp into the in-memory approval store. The execution tool checks this store before calling any Elasticsearch endpoint.

---

## Cost Reasoning

`cost/cost_reasoner.py` implements two independent cost functions:

**`get_current_monthly_node_cost()`** — reads `CLOUD_COST_PER_NODE_MONTHLY` from `config/settings.py`. This is the baseline cost reference.

**`get_billing_data()`** — calls `_fetch_aws_billing()`, `_fetch_gcp_billing()`, or `_fetch_azure_billing()` depending on `CLOUD_PROVIDER` to retrieve month-to-date spend and projected monthly cost.

**`evaluate_cost_tradeoff(action)`** — compares the action's recurring cost against `get_current_monthly_node_cost()`. The decision matrix:

|------------------|-------------------------------|---------------------------------|
|      Action      |        Recurring Cost         |           Decision              |
|------------------|-------------------------------|---------------------------------|
| `reindex`        | $0/mo                         | PROCEED                         |
| `mapping_change` | $0/mo                         | PROCEED                         |
| `query_rewrite`  | $0/mo                         | PROCEED                         |
| `scale_node`     | `CLOUD_COST_PER_NODE_MONTHLY` | REJECT — optimize queries first |
| `new_node`       | `CLOUD_COST_PER_NODE_MONTHLY` | REJECT — optimize queries first |
|------------------|-------------------------------|---------------------------------|

---

## Simulation

`simulation/ephemeral_cluster.py` provisions a throwaway Elasticsearch cluster to validate changes before production execution.

### `run_simulation()`

Benchmarks a mapping-level change (e.g., `keyword` → `wildcard` field type):

1. `_start_ephemeral_cluster()` — `docker run elasticsearch:8.13.0` on port 9299, single-node, `xpack.security=false`, `-Xms512m -Xmx512m`
2. `_wait_for_cluster()` — polls `/_cluster/health` every 3s until status is `green` or `yellow`, timeout 120s
3. `_seed_test_data()` — bulk-indexes 500 representative documents derived from the slowlog query corpus
4. `_benchmark_query()` — runs `BENCHMARK_ITERATIONS` queries against baseline index (original mapping)
5. `_benchmark_query()` — runs `BENCHMARK_ITERATIONS` queries against optimized index (proposed mapping)
6. `_stop_ephemeral_cluster()` — `docker rm -f sre-agent-simulation`, releases port 9299

Returns `{baseline: {avg_ms, p95_ms, min_ms, max_ms}, optimized: {avg_ms, p95_ms, min_ms, max_ms}, improvement_confirmed: bool}`.

### `simulate_cluster_settings_change()`

Same lifecycle, but benchmarks before and after calling `cluster.put_settings()` with the proposed settings change. Returns `improvement_confirmed`.

**Note:** Ephemeral cluster benchmarks are directionally valid but do not replicate production-level shard routing, replica overhead, or resource contention. The simulation gate confirms the change is not a regression; production performance will vary.

---

## Testing

```bash
pytest tests/ -v
```

### Test Coverage

|----------------------------|---------------------------------|--------|
|           File             |           Module                | Tests  |
|----------------------------|---------------------------------|--------|
| `test_esql_tool.py`        | `tools/esql_tool.py`            |    4   |
| `test_search_tool.py`      | `tools/search_tool.py`          |    4   |
| `test_execution_tool.py`   | `tools/execution_tool.py`       |    6   |
| `test_approval.py`         | `workflows/approval.py`         |    5   |
| `test_cost_reasoner.py`    | `cost/cost_reasoner.py`         |    4   |
| `test_reindex_workflow.py` | `workflows/reindex_workflow.py` |    5   |
| `test_orchestrator.py`     | `agent/orchestrator.py`         |    5   |
| `test_reasoning.py`        | `agent/reasoning.py`            |    4   |
| `test_diagnosis.py`        | `agent/diagnosis.py`            |   10   |
| `test_bootstrap.py`        | `setup/bootstrap.py`            |    6   |
| `test_docs_indexer.py`     | `setup/docs_indexer.py`         |    5   |
|----------------------------|---------------------------------|--------|
| **Total**                  |                                 | **58** |
|----------------------------|---------------------------------|--------|

All tests mock the Elasticsearch client and LLM API clients. No live cluster or API key is required to run the test suite.

---

## Comprehensive Project Description

The Self-Optimizing Elastic Infra Agent is an autonomous SRE system that monitors Elasticsearch clusters, identifies query performance bottlenecks, diagnoses their structural causes, researches documentation-backed fixes, proposes and validates optimization plans, and executes approved changes through a gated pipeline — all without requiring manual SRE intervention per cycle.

The setup layer uses `bootstrap.py` to enable xpack Stack Monitoring, configure slowlog thresholds on all production indices, and populate a custom `index-metadata` Elasticsearch index by crawling all production index mappings. `docs_indexer.py` discovers and crawls elastic.co documentation via sitemap XML, strips HTML, chunks text, embeds using `all-MiniLM-L6-v2`, and stores vectors in a FAISS IndexFlatIP for retrieval.

The toolset provides three instruments to the agent: an ES|QL tool that queries the monitoring cluster for slowlog events, node metrics, and circuit breaker stats; a knowledge tool that performs vector similarity search against the FAISS documentation index; and an execution tool that wraps all Elasticsearch mutation endpoints (reindex, settings, templates, aliases) behind an approval gate.

The agent loop runs on an APScheduler interval. Each cycle calls `run_optimization_cycle()` in the orchestrator, which sequences five steps: Identify (ES|QL query), Diagnose (six structural anti-pattern detectors + cardinality estimation), Research (FAISS search), Propose (LLM-generated Plan A→B→C), and Execute (gated dispatch). The reasoning model receives a composed context message containing all telemetry, diagnosis findings, and recommended documentation queries, then produces the structured plan.

Before any destructive action is dispatched, two automated gates run: the cost reasoner compares the action cost against the current node scaling cost using cloud billing API data; the simulation engine provisions a Docker ephemeral Elasticsearch cluster, seeds data, and benchmarks the proposed change before/after to confirm improvement. Only after both gates pass does the action enter the approval queue, where the operator decides via CLI or webhook. The React UI exposes all 24 functional panels, each calling the Anthropic API with the exact telemetry and system prompt its corresponding backend module uses, making every agent decision visible and interactive.

**Slowlog-based query identification** — Runs ES|QL against the monitoring cluster to surface the top-N slowest queries by average duration and execution count.

**Structural query diagnosis** — Six detectors analyze each slow query's JSON body for wildcard on high-cardinality fields, leading wildcards, unbounded term aggregations, deep nested queries, Painless script queries, and regexp queries. Cardinality estimation runs a live aggregation to confirm field uniqueness before flagging.

**Documentation-backed research** — A FAISS vector index of elastic.co documentation is searched using sentence embeddings. The agent retrieves the relevant documentation chunks before proposing any fix.

**LLM-driven optimization planning** — The reasoning model (Claude 3.5 Sonnet or GPT-4o) receives the composed telemetry context, diagnosis, and documentation findings, then produces a structured three-step plan: create index template → trigger reindex → update alias.

**Cost gate** — Before any action is dispatched, the cost reasoner compares the action cost against the cost of scaling a node using real cloud billing data.

**Simulation gate** — A Docker ephemeral single-node Elasticsearch cluster is provisioned, test data is seeded, and the proposed change is benchmarked before/after to confirm latency improvement.

**Approval gate** — Every destructive action is blocked until an operator approves via CLI stdin prompt or HTTP webhook. The execution tool does not call any Elasticsearch endpoint without a recorded decision.

**Scheduled loop** — APScheduler runs the full Identify→Diagnose→Research→Propose→Execute cycle at a configurable interval automatically.

**Reindex workflow** — A three-step workflow (create template, reindex, swap alias) is executed as a sequenced plan where each step generates its own approval request.

**Full observability UI** — A React interface with 24 panels surfaces every backend function, showing real agent reasoning output by calling the Anthropic API with the exact context each module uses.

---

## Target audience and operation overview

The target users are platform engineers, SREs, and Elasticsearch cluster administrators managing production clusters with active query workloads. The agent runs as a scheduled Python process connected to a monitoring Elasticsearch cluster. It requires no manual trigger once deployed — the scheduler runs the full optimization cycle at the configured interval, escalating to the operator only at the approval gate.

**Manual SRE toil elimination** — SRE teams spend significant time manually reading slowlogs, identifying query anti-patterns, writing reindex plans, and executing index changes. This project automates that entire cycle.

**Query performance degradation at scale** — As Elasticsearch indices grow to tens or hundreds of millions of documents, wildcard and regexp queries on keyword fields cause cluster-wide latency spikes. The agent detects and resolves these before they breach SLAs.

**Circuit breaker saturation** — Unbounded aggregations and fielddata cache overuse trigger circuit breaker exceptions. The diagnosis layer detects these patterns and proposes heap or mapping-level fixes.

**Operational risk from undocumented changes** — Reindexing at scale without a structured plan, cost check, benchmark, and approval gate is a common source of production incidents. This project enforces a structured, gated pipeline for every change.

**Documentation gap between engineers and best practices** — Elastic documentation is extensive and frequently updated. The vector knowledge base ensures the agent always references current best-practice documentation before proposing any change.

**Cloud cost accountability** — Teams scaling nodes to compensate for query inefficiency waste cloud budget. The cost gate forces a comparison between optimization (often free) and scaling (monthly recurring cost).

**Industry:** Platform engineering, site reliability engineering, search infrastructure, cloud-native operations, FinTech/eCommerce/media platforms running Elasticsearch at scale.

---

## Uniqueness 

Most Elasticsearch monitoring tools detect slow queries and alert. This project detects, diagnoses the structural cause using static analysis of the query JSON, retrieves best-practice documentation via vector search, validates the fix with a live benchmark on an ephemeral cluster before human approval, and executes the full mapping migration as a sequenced, reversible workflow. The combination of structural query analysis, RAG-backed documentation research, LLM planning, simulation, and gated execution in a single automated loop is not present in existing Elasticsearch tooling.

---

## Impacts on traditional development practices

Traditionally, Elasticsearch performance optimization is tribal knowledge — senior engineers know the anti-patterns, junior engineers do not, and there is no systematic process for catching them before they cause incidents. This project encodes that knowledge as detectors and retrieves current best practices from documentation automatically. Reindex operations, which currently require careful manual planning to avoid downtime, are reduced to an approved three-step workflow with a simulation-confirmed outcome. The cost gate changes how infrastructure teams justify optimization work — instead of arguing for engineering time, the cost comparison between a free query fix and a recurring node scaling cost makes the business case automatically. Teams running multiple Elasticsearch clusters can apply the same agent across all of them with different configuration, scaling the optimization process without scaling the team. The approval webhook integration means the optimization pipeline fits into existing incident management and change control workflows rather than requiring a new process.

---

## Known Limitations

- **Slowlog threshold dependency** — Queries below the configured slowlog threshold are not detected. Adjust `index.search.slowlog.threshold.query.warn` to match operational requirements.
- **Static anti-pattern detectors** — Detectors analyze query JSON structure. Performance issues caused by data skew, shard imbalance, or hardware-level resource contention are not detectable by structural analysis alone.
- **Simulation fidelity** — The Docker ephemeral cluster is a single-node, minimal-memory instance. Benchmark results are directionally valid but do not replicate multi-node replica overhead or production query concurrency.
- **FAISS index staleness** — The knowledge base reflects elastic.co documentation at the time of the last `build-kb` run. Re-run periodically after major Elasticsearch releases.
- **No automatic rollback** — If an approved change degrades production performance post-deployment, reversal requires a manual operator action. A future version will add regression detection with automated rollback routing through the same approval gate.
- **Billing API dependency** — The cost gate requires a valid `BILLING_API_KEY` and correctly configured `CLOUD_COST_PER_NODE_MONTHLY`. An incorrect cost reference produces incorrect gate decisions.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Run the test suite: `pytest tests/ -v`
4. Submit a pull request with a description of the change and its effect on the agent pipeline

All changes to `agent/diagnosis.py`, `tools/execution_tool.py`, or `workflows/approval.py` require corresponding test coverage updates.

---

## License

MIT License. See `LICENSE` for details.