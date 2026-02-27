import argparse
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_bootstrap(args):
    """Enable monitoring and populate index-metadata."""
    from setup.bootstrap import run_bootstrap
    logger.info("Running cluster bootstrap.")
    result = run_bootstrap()
    print(json.dumps(result, indent=2, default=str))


def cmd_build_kb(args):
    """Autodiscover Elastic docs from sitemap and build the FAISS knowledge base."""
    from setup.docs_indexer import build_knowledge_base
    logger.info("Building Knowledge Tool index from Elastic documentation sitemap.")
    result = build_knowledge_base(
        max_urls=args.max_urls,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(json.dumps(result, indent=2))


def cmd_run_cycle(args):
    """Runs a single optimization cycle and prints the result."""
    from agent.orchestrator import run_optimization_cycle
    logger.info("Running a single optimization cycle.")
    result = run_optimization_cycle(time_range_hours=args.hours)
    print(json.dumps(result, indent=2, default=str))


def cmd_start_loop(args):
    """scheduled: Starts the continuous scheduled optimization loop."""
    from agent.loop import start_scheduler
    logger.info("Starting continuous optimization loop.")
    start_scheduler()


def cmd_index_docs(args):
    """Builds knowledge base from a user-supplied list of URLs."""
    from tools.search_tool import crawl_and_index_elastic_docs
    with open(args.urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]
    logger.info("Indexing %d documentation URLs from file.", len(urls))
    count = crawl_and_index_elastic_docs(
        sitemap_urls=urls,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    logger.info("Indexed %d documentation chunks.", count)


def main():
    parser = argparse.ArgumentParser(
        description="Self-Optimizing Elastic Infra Agent — AI SRE for Elasticsearch clusters."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    
    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Enable Stack Monitoring and populate the index-metadata index."
    )
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    #autodiscovery
    kb_parser = subparsers.add_parser(
        "build-kb",
        help="Autodiscover Elastic documentation from sitemap and build the FAISS knowledge base."
    )
    kb_parser.add_argument("--max-urls", type=int, default=2000)
    kb_parser.add_argument("--chunk-size", type=int, default=500)
    kb_parser.add_argument("--chunk-overlap", type=int, default=50)
    kb_parser.set_defaults(func=cmd_build_kb)

    #single cycle
    cycle_parser = subparsers.add_parser(
        "run-cycle",
        help="Run one optimization cycle."
    )
    cycle_parser.add_argument(
        "--hours", type=int, default=1,
        help="Look-back window in hours for slowlog analysis."
    )
    cycle_parser.set_defaults(func=cmd_run_cycle)

    #continuous
    loop_parser = subparsers.add_parser(
        "start-loop",
        help="Start the continuous optimization loop."
    )
    loop_parser.set_defaults(func=cmd_start_loop)

    #manual
    docs_parser = subparsers.add_parser(
        "index-docs",
        help="Build knowledge base from a text file of documentation URLs."
    )
    docs_parser.add_argument(
        "--urls-file", required=True,
        help="Path to a text file with one documentation URL per line."
    )
    docs_parser.add_argument("--chunk-size", type=int, default=500)
    docs_parser.add_argument("--chunk-overlap", type=int, default=50)
    docs_parser.set_defaults(func=cmd_index_docs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
