from elasticsearch import Elasticsearch, NotFoundError
from config.settings import (
    ELASTICSEARCH_URL,
    ELASTICSEARCH_API_KEY,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
    MONITORING_CLUSTER_URL,
    MONITORING_API_KEY,
    SLOWLOG_INDEX_PATTERN,
    NODE_METRICS_INDEX_PATTERN,
    INDEX_METADATA_INDEX,
)


def _get_production_client() -> Elasticsearch:
    if ELASTICSEARCH_API_KEY:
        return Elasticsearch(ELASTICSEARCH_URL, api_key=ELASTICSEARCH_API_KEY)
    return Elasticsearch(
        ELASTICSEARCH_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


def _get_monitoring_client() -> Elasticsearch:
    if MONITORING_API_KEY:
        return Elasticsearch(MONITORING_CLUSTER_URL, api_key=MONITORING_API_KEY)
    return Elasticsearch(
        MONITORING_CLUSTER_URL,
        basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    )


# ──Enable Stack Monitoring ─────────────────────────────────────────

def enable_stack_monitoring() -> dict:
    """
    Configures the production Elasticsearch cluster to enable xpack
    Stack Monitoring and ships metrics to the dedicated monitoring cluster.

    Sets persistent cluster settings:
      - xpack.monitoring.elasticsearch.collection.enabled = true
      - xpack.monitoring.elasticsearch.collection.interval = 10s
      - cluster.monitoring.history.duration (retention window)

    enables slowlog thresholds on every index (query level WARN at 2s,
    fetch level WARN at 1s) so that .slowlog-* indices are populated.
    """
    client = _get_production_client()
    results = {}

    # Enable xpack monitoring collection
    monitoring_settings = {
        "persistent": {
            "xpack.monitoring.elasticsearch.collection.enabled": True,
            "xpack.monitoring.elasticsearch.collection.interval": "10s",
            "xpack.monitoring.history.duration": "7d",
        }
    }
    resp = client.cluster.put_settings(body=monitoring_settings)
    results["monitoring_enabled"] = resp.body

    # Enable slowlog on all existing indices so .slowlog-* gets populated
    slowlog_settings = {
        "index.search.slowlog.threshold.query.warn": "2s",
        "index.search.slowlog.threshold.query.info": "1s",
        "index.search.slowlog.threshold.fetch.warn": "1s",
        "index.search.slowlog.threshold.fetch.info": "500ms",
        "index.search.slowlog.level": "WARN",
    }
    resp = client.indices.put_settings(index="*", body=slowlog_settings)
    results["slowlog_enabled"] = resp.body

    # Configure the monitoring cluster as the remote exporter target
    exporter_settings = {
        "persistent": {
            "xpack.monitoring.exporters.remote_monitoring_cluster": {
                "type": "http",
                "host": [MONITORING_CLUSTER_URL],
            }
        }
    }
    try:
        resp = client.cluster.put_settings(body=exporter_settings)
        results["exporter_configured"] = resp.body
    except Exception as exc:
        # Remote exporter requires Platinum/Enterprise license; record but don't fail
        results["exporter_configured"] = {"warning": str(exc)}

    return results


# ──Verify Required Indices and Bootstrap index-metadata ─────────────

def verify_required_indices() -> dict:
    """
    Confirms that the three required index patterns exist and are
    accessible on the monitoring cluster. Returns a dict of pattern → exists bool.
    """
    monitoring_client = _get_monitoring_client()
    required_patterns = [
        SLOWLOG_INDEX_PATTERN,
        NODE_METRICS_INDEX_PATTERN,
        INDEX_METADATA_INDEX,
    ]
    status = {}
    for pattern in required_patterns:
        try:
            resp = monitoring_client.indices.exists(index=pattern)
            status[pattern] = bool(resp)
        except Exception as exc:
            status[pattern] = False
    return status


def _create_index_metadata_index(monitoring_client: Elasticsearch) -> None:
    """
    Creates the index-metadata index on the monitoring cluster if it does
    not already exist. Defines an explicit mapping so ES|QL queries against
    index_name, field_name, field_type, and settings work correctly.
    """
    body = {
        "mappings": {
            "properties": {
                "index_name":   {"type": "keyword"},
                "field_name":   {"type": "keyword"},
                "field_type":   {"type": "keyword"},
                "settings":     {"type": "object", "enabled": False},
                "aliases":      {"type": "keyword"},
                "shard_count":  {"type": "integer"},
                "replica_count": {"type": "integer"},
                "doc_count":    {"type": "long"},
                "store_size_bytes": {"type": "long"},
                "refreshed_at": {"type": "date"},
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
        }
    }
    try:
        monitoring_client.indices.create(index=INDEX_METADATA_INDEX, body=body)
    except Exception:
        # Index already exists — ignore
        pass


def _flatten_mappings(mappings: dict, prefix: str = "") -> list[dict]:
    """
    Recursively flattens nested ES mapping properties into a flat list of
    {field_name, field_type} dicts for storage in index-metadata.
    """
    records = []
    properties = mappings.get("properties", {})
    for field_name, field_def in properties.items():
        full_name = f"{prefix}{field_name}" if not prefix else f"{prefix}.{field_name}"
        field_type = field_def.get("type", "object")
        records.append({"field_name": full_name, "field_type": field_type})
        if "properties" in field_def:
            records.extend(_flatten_mappings(field_def, prefix=full_name))
    return records


def refresh_index_metadata() -> dict:
    """
    Reads all index mappings and settings from the production cluster
    and writes one document per field per index into the index-metadata index on
    the monitoring cluster. The agent queries this index via ES|QL instead of
    hitting the production _mapping API on every cycle.

    Returns a summary of how many indices and fields were indexed.
    """
    prod_client = _get_production_client()
    monitoring_client = _get_monitoring_client()

    _create_index_metadata_index(monitoring_client)

    # Fetch all mappings and settings from the production cluster in one call
    all_mappings = prod_client.indices.get_mapping(index="*")
    all_settings = prod_client.indices.get_settings(index="*")
    all_stats = prod_client.indices.stats(index="*", metric="docs,store")

    from datetime import datetime, timezone
    refreshed_at = datetime.now(timezone.utc).isoformat()

    bulk_ops = []
    total_indices = 0
    total_fields = 0

    for index_name, mapping_body in all_mappings.items():
        if index_name.startswith("."):
            # Skip internal system indices
            continue

        total_indices += 1
        settings = all_settings.get(index_name, {}).get("settings", {}).get("index", {})
        shard_count = int(settings.get("number_of_shards", 1))
        replica_count = int(settings.get("number_of_replicas", 1))

        stats = all_stats.get("indices", {}).get(index_name, {})
        doc_count = stats.get("primaries", {}).get("docs", {}).get("count", 0)
        store_bytes = stats.get("primaries", {}).get("store", {}).get("size_in_bytes", 0)

        aliases = list(
            prod_client.indices.get_alias(index=index_name).get(index_name, {}).get("aliases", {}).keys()
        )

        index_mappings = mapping_body.get("mappings", {})
        field_records = _flatten_mappings(index_mappings)

        if not field_records:
            field_records = [{"field_name": "_doc", "field_type": "unknown"}]

        for field_record in field_records:
            doc = {
                "index_name": index_name,
                "field_name": field_record["field_name"],
                "field_type": field_record["field_type"],
                "settings": settings,
                "aliases": aliases,
                "shard_count": shard_count,
                "replica_count": replica_count,
                "doc_count": doc_count,
                "store_size_bytes": store_bytes,
                "refreshed_at": refreshed_at,
            }
            bulk_ops.append({"index": {"_index": INDEX_METADATA_INDEX}})
            bulk_ops.append(doc)
            total_fields += 1

        # Flush in batches of 500 to avoid oversized bulk requests
        if len(bulk_ops) >= 1000:
            monitoring_client.bulk(body=bulk_ops, refresh=False)
            bulk_ops = []

    if bulk_ops:
        monitoring_client.bulk(body=bulk_ops, refresh=True)

    return {
        "indices_indexed": total_indices,
        "fields_indexed": total_fields,
        "refreshed_at": refreshed_at,
    }


def run_bootstrap() -> dict:
    """
    bootstrap sequence.
    1. Enable Stack Monitoring on the production cluster.
    2. Verify required indices exist on the monitoring cluster.
    3. Crawl all production mappings and populate index-metadata.
    """
    results = {}

    results["monitoring"] = enable_stack_monitoring()
    results["index_verification"] = verify_required_indices()
    results["index_metadata_refresh"] = refresh_index_metadata()

    return results
