import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from tools.search_tool import (
    _strip_html,
    _extract_title,
    _split_text,
    search_elastic_docs,
    build_docs_index,
)


class TestStripHtml:
    def test_removes_basic_tags(self):
        html = "<p>Hello <b>world</b></p>"
        assert "Hello" in _strip_html(html)
        assert "<p>" not in _strip_html(html)
        assert "<b>" not in _strip_html(html)

    def test_removes_script_blocks(self):
        html = "<script>alert('x')</script><p>Content</p>"
        result = _strip_html(html)
        assert "alert" not in result
        assert "Content" in result

    def test_removes_style_blocks(self):
        html = "<style>body{color:red}</style><p>Text</p>"
        result = _strip_html(html)
        assert "color:red" not in result
        assert "Text" in result

    def test_collapses_whitespace(self):
        html = "<p>  Too   many   spaces  </p>"
        result = _strip_html(html)
        assert "  " not in result.strip()


class TestExtractTitle:
    def test_extracts_title_tag(self):
        html = "<html><head><title>Circuit Breaker Settings</title></head></html>"
        assert _extract_title(html) == "Circuit Breaker Settings"

    def test_returns_default_on_no_title(self):
        html = "<html><body>No title here</body></html>"
        assert _extract_title(html) == "Elastic Documentation"

    def test_case_insensitive(self):
        html = "<TITLE>Upper Case</TITLE>"
        assert _extract_title(html) == "Upper Case"


class TestSplitText:
    def test_returns_list_of_strings(self):
        text = "a" * 2000
        chunks = _split_text(text, chunk_size=500, overlap=50)
        assert all(isinstance(c, str) for c in chunks)

    def test_chunk_size_respected(self):
        text = "b" * 2000
        chunks = _split_text(text, chunk_size=500, overlap=0)
        for chunk in chunks:
            assert len(chunk) <= 500

    def test_filters_tiny_chunks(self):
        text = "short"
        chunks = _split_text(text, chunk_size=500, overlap=50)
        # "short" is < 50 chars so it should be filtered out
        assert len(chunks) == 0

    def test_overlap_creates_more_chunks_than_no_overlap(self):
        text = "x" * 1000
        chunks_no_overlap = _split_text(text, chunk_size=200, overlap=0)
        chunks_with_overlap = _split_text(text, chunk_size=200, overlap=50)
        assert len(chunks_with_overlap) >= len(chunks_no_overlap)


class TestBuildDocsIndex:
    @patch("tools.search_tool.faiss")
    @patch("tools.search_tool._load_embedding_model")
    def test_creates_faiss_index_and_metadata(self, mock_model_loader, mock_faiss):
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(3, 384).astype("float32")
        mock_model_loader.return_value = mock_model

        mock_index = MagicMock()
        mock_faiss.IndexFlatIP.return_value = mock_index

        chunks = [
            {"text": "Circuit breaker settings control memory usage.", "url": "http://elastic.co/1", "title": "Breakers"},
            {"text": "Wildcard queries can be slow on high cardinality fields.", "url": "http://elastic.co/2", "title": "Wildcards"},
            {"text": "Use n-grams for partial match optimization.", "url": "http://elastic.co/3", "title": "N-grams"},
        ]

        import json
        import builtins
        from unittest.mock import mock_open
        m = mock_open()
        with patch("builtins.open", m):
            build_docs_index(chunks)

        mock_index.add.assert_called_once()
        mock_faiss.write_index.assert_called_once()


class TestSearchElasticDocs:
    @patch("tools.search_tool._load_index_and_metadata")
    @patch("tools.search_tool._load_embedding_model")
    def test_returns_top_k_results(self, mock_model_loader, mock_load_index):
        import faiss as real_faiss
        import numpy as np

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_model_loader.return_value = mock_model

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.array([[0.95, 0.87, 0.80]]),
            np.array([[0, 1, 2]]),
        )
        mock_metadata = [
            {"text": "Breaker doc text", "url": "http://elastic.co/1", "title": "Breakers"},
            {"text": "Wildcard doc text", "url": "http://elastic.co/2", "title": "Wildcards"},
            {"text": "N-gram doc text", "url": "http://elastic.co/3", "title": "N-grams"},
        ]
        mock_load_index.return_value = (mock_index, mock_metadata)

        results = search_elastic_docs("CircuitBreakerException", top_k=3)
        assert len(results) == 3
        assert results[0]["title"] == "Breakers"
        assert results[0]["score"] == pytest.approx(0.95)

    @patch("tools.search_tool._load_index_and_metadata")
    @patch("tools.search_tool._load_embedding_model")
    def test_result_has_required_keys(self, mock_model_loader, mock_load_index):
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_model_loader.return_value = mock_model

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.array([[0.9]]),
            np.array([[0]]),
        )
        mock_load_index.return_value = (
            mock_index,
            [{"text": "doc text", "url": "http://x.com", "title": "Title"}],
        )

        results = search_elastic_docs("wildcard optimization")
        assert "score" in results[0]
        assert "title" in results[0]
        assert "url" in results[0]
        assert "text" in results[0]
