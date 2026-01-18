"""Unit tests for NLP extraction with Transformers."""

import pytest
from unittest.mock import MagicMock, patch
from src.processing.extraction.nlp import TransformerExtractor

# Mock data simulating REBEL output
# Format: <triplet> subject <subj> object <obj> relation
SAMPLE_REBEL_OUTPUT = "<triplet> Napoleon <subj> France <obj> emperor of <triplet> Paris <subj> France <obj> capital of"

class TestTransformerExtractor:
    
    @patch("src.processing.extraction.nlp.TRANSFORMERS_AVAILABLE", True)
    @patch("src.processing.extraction.nlp.pipeline")
    def test_rebel_extraction(self, mock_pipeline):
        """Test relation extraction with mocked pipeline."""
        
        # Setup mock
        mock_pipe_instance = MagicMock()
        mock_pipeline.return_value = mock_pipe_instance
        
        # Mock return value of the pipeline call
        # pipeline returns a list of dicts with 'generated_text'
        mock_pipe_instance.return_value = [
            {"generated_text": SAMPLE_REBEL_OUTPUT}
        ]
        
        extractor = TransformerExtractor()
        results = extractor.extract_relations("Napoleon was the emperor of France and Paris is its capital.")
        
        assert len(results) == 2
        
        # Verify first relation
        r1 = next(r for r in results if r['head'] == 'Napoleon')
        assert r1['tail'] == 'France'
        assert r1['type'] == 'emperor of'
        
        # Verify second relation
        r2 = next(r for r in results if r['head'] == 'Paris')
        assert r2['tail'] == 'France'
        assert r2['type'] == 'capital of'

    @patch("src.processing.extraction.nlp.TRANSFORMERS_AVAILABLE", True)
    @patch("src.processing.extraction.nlp.pipeline")
    def test_parsing_logic_edge_cases(self, mock_pipeline):
        """Test parsing logic with messy output."""
        extractor = TransformerExtractor()
        
        # Case: Missing tags
        bad_text = "Just some text without tags"
        assert extractor._parse_rebel_output(bad_text) == []
        
        # Case: Partial tags
        partial_text = "<triplet> Subject <subj> Object" # Missing obj and relation
        assert extractor._parse_rebel_output(partial_text) == []
        
        # Case: Extra whitespace
        messy_text = "<triplet>  A  <subj>  B  <obj>  C "
        results = extractor._parse_rebel_output(messy_text)
        assert len(results) == 1
        assert results[0]['head'] == "A"
        assert results[0]['tail'] == "B"
        assert results[0]['type'] == "C"

