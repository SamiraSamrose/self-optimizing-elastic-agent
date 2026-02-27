import subprocess
import time
import statistics
import httpx
import json
from elasticsearch import Elasticsearch
from config.settings import (
    EPHEMERAL_CLUSTER_URL,
    BENCHMARK_ITERATIONS,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
)

_DOCKER_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch:8.13.0"
_EPHEMERAL_PORT = 9299
_EPHEMERAL_CONTAINER_NAME = "sre-agent-simulation"


def _start_ephemeral_cluster() -> str:
    """
    Starts a single-node ephemeral Elasticsearch cluster via Docker.
    Returns the cluster URL.
    """
    if EPHEMERAL_CLUSTER_URL:
        return EPHEMERAL_CLUSTER_URL

    subprocess.run(["docker", "rm", "-f", _EPHEMERAL_CONTAINER_NAME], capture_output=True)

    subprocess.run([
        "docker", "run", "-d",
        "--name", _EPHEMERAL_CONTAINER_NAME,
        "-p", f"{_EPHEMERAL_PORT}:9200",
        "-e", "discovery.type=single-node",
        "-e", "xpack.security.enabled=false",
        "-e", "ES_JAVA_OPTS=-Xms512m -Xmx512m",
        _DOCKER_IMAGE,
    ], check=True)

    url = f"http://localhost:{_EPHEMERAL_PORT}"
    _wait_for_cluster(url)
    return url


def _wait_for_cluster(url: str, timeout: int = 120) -> None:
    """Polls until the ephemeral cluster is green or yellow and accepting requests."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{url}/_cluster/health", timeout=5.0)
            status = resp.json().get("status")
            if status in ("green", "yellow"):
                return
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Ephemeral cluster at {url} did not become healthy within {timeout}s.")


def _stop_ephemeral_cluster() -> None:
    """Stops and removes the ephemeral Docker container."""
    if not EPHEMERAL_CLUSTER_URL:
        subprocess.run(
            ["docker", "rm", "-f", _EPHEMERAL_CONTAINER_NAME],
            capture_output=True,
        )


def _benchmark_query(client: Elasticsearch, index: str, query: dict, iterations: int) -> dict:
    """
    Runs a query `iterations` times and returns latency statistics in milliseconds.
    """
    durations = []
    for _ in range(iterations):
        start = time.perf_counter()
        client.search(index=index, body=query)
        elapsed_ms = (time.perf_counter() - start) * 1000
        durations.append(elapsed_ms)

    return {
        "min_ms": min(durations),
        "max_ms": max(durations),
        "avg_ms": statistics.mean(durations),
        "p95_ms": sorted(durations)[int(len(durations) * 0.95)],
        "iterations": iterations,
    }


def _seed_test_data(
    client: Elasticsearch,
    baseline_index: str,
    optimized_index: str,
    doc_count: int = 500,
) -> None:
    """
    Seeds both indices with the same set of representative documents
    drawn from the actual cluster's slowlog data to make the benchmark realistic.
    """
    from tools.esql_tool import fetch_slowest_queries

    try:
        slow_result = fetch_slowest_queries(time_range_hours=24)
        rows = slow_result.get("rows", [])
        statements = [row[2] if len(row) > 2 else "SELECT 1" for row in rows]
    except Exception:
        statements = [f"query-{i}" for i in range(min(doc_count, 50))]

    ops = []
    for i in range(doc_count):
        statement = statements[i % len(statements)] if statements else f"query-{i}"
        doc = {
            "statement": statement,
            "message": f"Log entry {i} for statement: {statement}",
            "event": {"duration": i * 1000},
        }
        for index in (baseline_index, optimized_index):
            ops.append({"index": {"_index": index}})
            ops.append(doc)

    if ops:
        client.bulk(body=ops, refresh=False)


def run_simulation(
    proposed_mappings: dict,
    proposed_settings: dict,
    benchmark_query: dict = None,
    test_index_name: str = "simulation-test-index",
) -> dict:
    """
    Mapping / Reindex Simulation — provisions an ephemeral cluster,
    creates baseline and optimized indices, seeds them with realistic data,
    benchmarks the same query against both, and reports improvement.

    Args:
        proposed_mappings: The new mappings the agent wants to apply.
        proposed_settings: The new index settings the agent wants to apply.
        benchmark_query: The query to benchmark. Defaults to match_all.
        test_index_name: Base name for the test indices.

    Returns:
        A dict with baseline and optimized latency stats and improvement_confirmed flag.
    """
    if benchmark_query is None:
        benchmark_query = {"query": {"match_all": {}}}

    cluster_url = _start_ephemeral_cluster()
    sim_client = Elasticsearch(cluster_url)
    baseline_index = f"{test_index_name}-baseline"
    optimized_index = f"{test_index_name}-optimized"

    results = {
        "simulation_type": "mapping",
        "cluster_url": cluster_url,
        "baseline": {},
        "optimized": {},
        "improvement_confirmed": False,
        "improvement_pct": 0.0,
    }

    try:
        sim_client.indices.create(
            index=baseline_index,
            body={
                "mappings": {
                    "properties": {
                        "statement": {"type": "keyword"},
                        "message":   {"type": "text"},
                    }
                }
            }
        )

        optimized_body = {"mappings": proposed_mappings}
        if proposed_settings:
            optimized_body["settings"] = proposed_settings
        sim_client.indices.create(index=optimized_index, body=optimized_body)

        _seed_test_data(sim_client, baseline_index, optimized_index)
        sim_client.indices.refresh(index=f"{baseline_index},{optimized_index}")

        baseline_stats  = _benchmark_query(sim_client, baseline_index, benchmark_query, BENCHMARK_ITERATIONS)
        optimized_stats = _benchmark_query(sim_client, optimized_index, benchmark_query, BENCHMARK_ITERATIONS)

        results["baseline"]  = baseline_stats
        results["optimized"] = optimized_stats

        if baseline_stats["avg_ms"] > 0:
            improvement_pct = (
                (baseline_stats["avg_ms"] - optimized_stats["avg_ms"])
                / baseline_stats["avg_ms"]
            ) * 100
            results["improvement_pct"] = round(improvement_pct, 2)
            results["improvement_confirmed"] = improvement_pct > 0

    finally:
        try:
            sim_client.indices.delete(index=baseline_index, ignore_unavailable=True)
            sim_client.indices.delete(index=optimized_index, ignore_unavailable=True)
        except Exception:
            pass
        _stop_ephemeral_cluster()

    return results


def simulate_cluster_settings_change(
    proposed_persistent: dict = None,
    proposed_transient: dict = None,
    benchmark_query: dict = None,
    test_index_name: str = "simulation-cluster-settings-test",
) -> dict:
    """
    imulates cluster-level settings changes on an ephemeral
    cluster before applying them to production. This covers non-reindex actions such
    as adjusting indices.breaker.total.limit or search thread pool sizes.

    Workflow:
      1. Start ephemeral cluster.
      2. Benchmark a query BEFORE applying the proposed cluster settings.
      3. Apply the proposed cluster settings.
      4. Benchmark the same query AFTER.
      5. Report whether performance improved.

    Args:
        proposed_persistent: Persistent cluster settings to test.
        proposed_transient: Transient cluster settings to test.
        benchmark_query: The query body to benchmark. Defaults to match_all.
        test_index_name: Name for the temporary test index.

    Returns:
        A dict with before/after latency stats and improvement_confirmed flag.
    """
    if benchmark_query is None:
        benchmark_query = {"query": {"match_all": {}}}

    cluster_url = _start_ephemeral_cluster()
    sim_client = Elasticsearch(cluster_url)

    results = {
        "simulation_type": "cluster_settings",
        "proposed_persistent": proposed_persistent,
        "proposed_transient": proposed_transient,
        "before_settings": {},
        "after_settings": {},
        "improvement_confirmed": False,
        "improvement_pct": 0.0,
    }

    try:
        # Create a test index and seed data so we have something to query
        sim_client.indices.create(
            index=test_index_name,
            body={
                "mappings": {
                    "properties": {
                        "message":  {"type": "text"},
                        "value":    {"type": "long"},
                    }
                },
                "settings": {"number_of_shards": 1}
            }
        )

        ops = []
        for i in range(200):
            ops.append({"index": {"_index": test_index_name}})
            ops.append({"message": f"test document number {i}", "value": i})
        if ops:
            sim_client.bulk(body=ops, refresh=True)

        # Benchmark BEFORE applying the proposed settings
        before_stats = _benchmark_query(
            sim_client, test_index_name, benchmark_query, BENCHMARK_ITERATIONS
        )
        results["before_settings"] = before_stats

        # Apply proposed cluster settings
        settings_payload = {}
        if proposed_persistent:
            settings_payload["persistent"] = proposed_persistent
        if proposed_transient:
            settings_payload["transient"] = proposed_transient

        if settings_payload:
            sim_client.cluster.put_settings(body=settings_payload)

        # Allow the cluster to stabilise after the settings change
        time.sleep(2)

        # Benchmark AFTER applying the proposed settings
        after_stats = _benchmark_query(
            sim_client, test_index_name, benchmark_query, BENCHMARK_ITERATIONS
        )
        results["after_settings"] = after_stats

        if before_stats["avg_ms"] > 0:
            improvement_pct = (
                (before_stats["avg_ms"] - after_stats["avg_ms"])
                / before_stats["avg_ms"]
            ) * 100
            results["improvement_pct"] = round(improvement_pct, 2)
            results["improvement_confirmed"] = improvement_pct > 0

    finally:
        try:
            sim_client.indices.delete(index=test_index_name, ignore_unavailable=True)
        except Exception:
            pass
        _stop_ephemeral_cluster()

    return results
