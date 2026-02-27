import os
from dotenv import load_dotenv

load_dotenv()

#Elasticsearch cluster connection
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", "")
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "")

# Dedicated monitoring cluster 
MONITORING_CLUSTER_URL = os.getenv("MONITORING_CLUSTER_URL", ELASTICSEARCH_URL)
MONITORING_API_KEY = os.getenv("MONITORING_API_KEY", ELASTICSEARCH_API_KEY)

# Required indices the agent reads from
SLOWLOG_INDEX_PATTERN = os.getenv("SLOWLOG_INDEX_PATTERN", ".ds-elasticsearch.slowlog-*")
NODE_METRICS_INDEX_PATTERN = os.getenv("NODE_METRICS_INDEX_PATTERN", "metrics-elasticsearch.node-*")
INDEX_METADATA_INDEX = os.getenv("INDEX_METADATA_INDEX", "index-metadata")

# Reasoning model configuration
REASONING_PROVIDER = os.getenv("REASONING_PROVIDER", "anthropic")  # "anthropic" or "openai"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Vector search / knowledge tool config
DOCS_VECTOR_INDEX = os.getenv("DOCS_VECTOR_INDEX", "elastic-docs-vectors")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DOCS_SOURCE_URL = os.getenv("DOCS_SOURCE_URL", "https://www.elastic.co/docs")

# Optimization loop scheduling
LOOP_INTERVAL_SECONDS = int(os.getenv("LOOP_INTERVAL_SECONDS", "3600"))  # every hour
TOP_SLOW_QUERIES_LIMIT = int(os.getenv("TOP_SLOW_QUERIES_LIMIT", "5"))
SLOW_QUERY_MIN_COUNT = int(os.getenv("SLOW_QUERY_MIN_COUNT", "100"))

#Workflow approval
APPROVAL_WEBHOOK_URL = os.getenv("APPROVAL_WEBHOOK_URL", "")
APPROVAL_TIMEOUT_SECONDS = int(os.getenv("APPROVAL_TIMEOUT_SECONDS", "300"))

#Cost-aware reasoning
CLOUD_COST_PER_NODE_MONTHLY = float(os.getenv("CLOUD_COST_PER_NODE_MONTHLY", "200.0"))
CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws")  # aws, gcp, azure
BILLING_API_KEY = os.getenv("BILLING_API_KEY", "")

#Simulation / ephemeral cluster
EPHEMERAL_CLUSTER_URL = os.getenv("EPHEMERAL_CLUSTER_URL", "")
SIMULATION_ENABLED = os.getenv("SIMULATION_ENABLED", "false").lower() == "true"
BENCHMARK_ITERATIONS = int(os.getenv("BENCHMARK_ITERATIONS", "10"))
