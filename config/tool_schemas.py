#Analytical Tool: ES|QL query runner
ESQL_TOOL_SCHEMA = {
    "name": "run_esql_query",
    "description": (
        "Runs an ES|QL query against the Elasticsearch monitoring cluster to aggregate "
        "telemetry data across slowlogs, node metrics, and index metadata."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The ES|QL query string to execute."
            },
            "index_pattern": {
                "type": "string",
                "description": "The index pattern to query (e.g., .ds-elasticsearch.slowlog-*)."
            },
            "time_range_hours": {
                "type": "integer",
                "description": "How many hours back to scope the query. Defaults to 1.",
                "default": 1
            }
        },
        "required": ["query", "index_pattern"]
    }
}

# Knowledge Tool: vector search over Elastic documentation
SEARCH_TOOL_SCHEMA = {
    "name": "search_elastic_docs",
    "description": (
        "Searches the indexed Elastic documentation using vector similarity to retrieve "
        "best-practice guidance for a given error, exception, or performance pattern."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language query to search the docs for."
            },
            "top_k": {
                "type": "integer",
                "description": "Number of documentation chunks to return. Defaults to 5.",
                "default": 5
            }
        },
        "required": ["query"]
    }
}

# Execution Tool: update_index_settings — exact schema from the spec's
UPDATE_INDEX_SETTINGS_SCHEMA = {
    "name": "update_index_settings",
    "description": "Updates the settings or mappings of an existing index.",
    "parameters": {
        "type": "object",
        "properties": {
            "index_name": {
                "type": "string",
                "description": "The index whose settings or mappings will be updated."
            },
            "settings": {
                "type": "object",
                "description": "Object containing 'settings' and/or 'mappings' sub-keys."
            },
            "reason": {
                "type": "string",
                "description": "Mandatory explanation of why this change is being proposed."
            }
        },
        "required": ["index_name", "settings", "reason"]
    }
}

#Execution Tool: _reindex endpoint
REINDEX_SCHEMA = {
    "name": "trigger_reindex",
    "description": (
        "Triggers an Elasticsearch _reindex operation from a source index to a destination index. "
        "Requires approval before execution."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "source_index": {
                "type": "string",
                "description": "The source index to reindex from."
            },
            "destination_index": {
                "type": "string",
                "description": "The destination index to reindex into."
            },
            "query": {
                "type": "object",
                "description": "Optional query to filter documents during reindex.",
                "default": {"match_all": {}}
            },
            "reason": {
                "type": "string",
                "description": "Mandatory explanation of why a reindex is being proposed."
            }
        },
        "required": ["source_index", "destination_index", "reason"]
    }
}

# Plan C — alias swap schema
UPDATE_ALIAS_SCHEMA = {
    "name": "update_alias",
    "description": "Updates an index alias to point to a new index after reindexing.",
    "parameters": {
        "type": "object",
        "properties": {
            "alias_name": {"type": "string"},
            "remove_index": {"type": "string"},
            "add_index": {"type": "string"},
            "reason": {
                "type": "string",
                "description": "Mandatory explanation of why the alias is being updated."
            }
        },
        "required": ["alias_name", "remove_index", "add_index", "reason"]
    }
}

#PlanA — create index template schema
CREATE_INDEX_TEMPLATE_SCHEMA = {
    "name": "create_index_template",
    "description": "Creates a new index template with optimized field mappings.",
    "parameters": {
        "type": "object",
        "properties": {
            "template_name": {"type": "string"},
            "index_patterns": {
                "type": "array",
                "items": {"type": "string"}
            },
            "mappings": {"type": "object"},
            "settings": {"type": "object"},
            "reason": {
                "type": "string",
                "description": "Mandatory explanation of the mapping optimization being applied."
            }
        },
        "required": ["template_name", "index_patterns", "mappings", "reason"]
    }
}

# cluster-level settings schema (e.g., indices.breaker.total.limit)
UPDATE_CLUSTER_SETTINGS_SCHEMA = {
    "name": "update_cluster_settings",
    "description": (
        "Updates Elasticsearch cluster-level settings via the _cluster/settings endpoint. "
        "Use for breaker limits, allocation settings, etc."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "persistent": {
                "type": "object",
                "description": "Persistent settings that survive cluster restart."
            },
            "transient": {
                "type": "object",
                "description": "Transient settings reset on cluster restart."
            },
            "reason": {
                "type": "string",
                "description": "Mandatory explanation of why this cluster setting is being changed."
            }
        },
        "required": ["reason"]
    }
}

# All schemas exposed to the reasoning model
ALL_TOOL_SCHEMAS = [
    ESQL_TOOL_SCHEMA,
    SEARCH_TOOL_SCHEMA,
    UPDATE_INDEX_SETTINGS_SCHEMA,
    REINDEX_SCHEMA,
    UPDATE_ALIAS_SCHEMA,
    CREATE_INDEX_TEMPLATE_SCHEMA,
    UPDATE_CLUSTER_SETTINGS_SCHEMA,
]
