import xml.etree.ElementTree as ET
import httpx
import logging
from tools.search_tool import crawl_and_index_elastic_docs

logger = logging.getLogger(__name__)

# Elastic publishes a sitemap index that links to per-section sitemaps
_SITEMAP_INDEX_URL = "https://www.elastic.co/sitemap.xml"

# Sections of the docs we care about for SRE / performance tuning
_RELEVANT_URL_PREFIXES = (
    "https://www.elastic.co/guide/en/elasticsearch/reference",
    "https://www.elastic.co/guide/en/elasticsearch/client",
    "https://www.elastic.co/guide/en/kibana",
    "https://www.elastic.co/docs",
)

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _fetch_xml(url: str, client: httpx.Client) -> ET.Element | None:
    """Fetches a URL and parses it as XML. Returns None on any error."""
    try:
        resp = client.get(url, timeout=30.0)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as exc:
        logger.warning("Failed to fetch XML from %s: %s", url, exc)
        return None


def discover_docs_urls(max_urls: int = 2000) -> list[str]:
    """
    Parses the elastic.co sitemap index to discover all documentation
    page URLs. Filters to only the Elasticsearch reference and docs sections
    that contain SRE-relevant content.

    Args:
        max_urls: Maximum number of URLs to return (keeps memory bounded).

    Returns:
        A deduplicated list of documentation page URLs.
    """
    client = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "ElasticSREAgent-DocsIndexer/1.0"},
    )

    discovered_urls: list[str] = []

    #Fetch the sitemap index to get child sitemap URLs
    root = _fetch_xml(_SITEMAP_INDEX_URL, client)
    if root is None:
        logger.error("Could not fetch sitemap index from %s", _SITEMAP_INDEX_URL)
        client.close()
        return []

    # The sitemap index contains <sitemap><loc>child_sitemap_url</loc></sitemap> entries
    child_sitemap_urls = []
    for sitemap_elem in root.findall("sm:sitemap", _SITEMAP_NS):
        loc = sitemap_elem.find("sm:loc", _SITEMAP_NS)
        if loc is not None and loc.text:
            child_sitemap_urls.append(loc.text.strip())

    logger.info("Found %d child sitemaps in sitemap index.", len(child_sitemap_urls))

    #Parse each child sitemap and collect relevant doc URLs
    for child_url in child_sitemap_urls:
        if len(discovered_urls) >= max_urls:
            break

        child_root = _fetch_xml(child_url, client)
        if child_root is None:
            continue

        for url_elem in child_root.findall("sm:url", _SITEMAP_NS):
            loc = url_elem.find("sm:loc", _SITEMAP_NS)
            if loc is not None and loc.text:
                page_url = loc.text.strip()
                if page_url.startswith(_RELEVANT_URL_PREFIXES):
                    discovered_urls.append(page_url)
                    if len(discovered_urls) >= max_urls:
                        break

    client.close()

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in discovered_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    logger.info("Discovered %d unique documentation URLs.", len(unique_urls))
    return unique_urls


def build_knowledge_base(
    max_urls: int = 2000,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict:
    """
    Full pipeline — discover Elastic docs URLs from the sitemap,
    crawl each page, chunk the text, embed it, and write the FAISS index.

    This populates the Knowledge Tool that the agent uses to look up best
    practices for any detected exception or performance pattern.

    Args:
        max_urls: Cap on the number of pages to index.
        chunk_size: Character length of each embedding chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        A summary dict with url_count and chunk_count.
    """
    urls = discover_docs_urls(max_urls=max_urls)

    if not urls:
        return {"url_count": 0, "chunk_count": 0, "status": "no_urls_discovered"}

    logger.info("Starting crawl and indexing of %d URLs.", len(urls))

    chunk_count = crawl_and_index_elastic_docs(
        sitemap_urls=urls,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return {
        "url_count": len(urls),
        "chunk_count": chunk_count,
        "status": "indexed",
    }
