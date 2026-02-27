import pytest
from unittest.mock import patch, MagicMock
from setup.docs_indexer import discover_docs_urls, build_knowledge_base


_SITEMAP_INDEX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.elastic.co/sitemap-elasticsearch.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.elastic.co/sitemap-marketing.xml</loc>
  </sitemap>
</sitemapindex>"""

_ELASTICSEARCH_SITEMAP_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html</loc>
  </url>
  <url>
    <loc>https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html</loc>
  </url>
  <url>
    <loc>https://www.elastic.co/guide/en/elasticsearch/reference/current/circuit-breaker.html</loc>
  </url>
  <url>
    <loc>https://www.elastic.co/blog/some-marketing-post</loc>
  </url>
</urlset>"""

_MARKETING_SITEMAP_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.elastic.co/pricing</loc>
  </url>
</urlset>"""


class TestDiscoverDocsUrls:
    #sitemap parsing and URL filtering

    def _make_mock_client(self):
        mock_client = MagicMock()

        def get_side_effect(url, **kwargs):
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            if "sitemap.xml" in url and "elasticsearch" not in url and "marketing" not in url:
                resp.content = _SITEMAP_INDEX_XML
            elif "elasticsearch" in url:
                resp.content = _ELASTICSEARCH_SITEMAP_XML
            elif "marketing" in url:
                resp.content = _MARKETING_SITEMAP_XML
            else:
                resp.content = b"<urlset></urlset>"
            return resp

        mock_client.get.side_effect = get_side_effect
        return mock_client

    @patch("setup.docs_indexer.httpx.Client")
    def test_discovers_elasticsearch_reference_urls(self, mock_client_class):
        mock_client_class.return_value.__enter__ = MagicMock()
        mock_client_class.return_value.__exit__ = MagicMock()
        mock_client_instance = self._make_mock_client()
        mock_client_class.return_value = mock_client_instance

        urls = discover_docs_urls(max_urls=100)

        #elasticsearch reference URLs
        es_urls = [u for u in urls if "elasticsearch/reference" in u]
        assert len(es_urls) >= 1

    @patch("setup.docs_indexer.httpx.Client")
    def test_excludes_non_docs_urls(self, mock_client_class):
        mock_client_instance = self._make_mock_client()
        mock_client_class.return_value = mock_client_instance

        urls = discover_docs_urls(max_urls=100)

        # Marketing / pricing pages should not be included
        non_docs = [u for u in urls if "pricing" in u or "blog" in u]
        assert non_docs == []

    @patch("setup.docs_indexer.httpx.Client")
    def test_deduplicates_urls(self, mock_client_class):
        mock_client_instance = self._make_mock_client()
        mock_client_class.return_value = mock_client_instance

        urls = discover_docs_urls(max_urls=100)
        assert len(urls) == len(set(urls))

    @patch("setup.docs_indexer.httpx.Client")
    def test_respects_max_urls_cap(self, mock_client_class):
        mock_client_instance = self._make_mock_client()
        mock_client_class.return_value = mock_client_instance

        urls = discover_docs_urls(max_urls=2)
        assert len(urls) <= 2

    @patch("setup.docs_indexer.httpx.Client")
    def test_returns_empty_on_sitemap_failure(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        urls = discover_docs_urls(max_urls=100)
        assert urls == []


class TestBuildKnowledgeBase:
    @patch("setup.docs_indexer.crawl_and_index_elastic_docs", return_value=150)
    @patch("setup.docs_indexer.discover_docs_urls", return_value=[
        "https://www.elastic.co/guide/en/elasticsearch/reference/current/wildcard.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/current/circuit-breaker.html",
    ])
    def test_calls_crawl_and_returns_summary(self, mock_discover, mock_crawl):
        result = build_knowledge_base(max_urls=10)
        assert result["url_count"] == 2
        assert result["chunk_count"] == 150
        assert result["status"] == "indexed"

    @patch("setup.docs_indexer.discover_docs_urls", return_value=[])
    def test_returns_no_urls_status_when_none_discovered(self, mock_discover):
        result = build_knowledge_base(max_urls=10)
        assert result["status"] == "no_urls_discovered"
        assert result["url_count"] == 0
