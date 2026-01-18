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
    @patch("src.processing.extraction.nlp.AutoTokenizer")
    @patch("src.processing.extraction.nlp.AutoModelForSeq2SeqLM")
    @patch("src.processing.extraction.nlp.torch") # Mock torch as well
    def test_rebel_extraction(self, mock_torch, mock_model_cls, mock_tokenizer_cls, mock_pipeline):
        """Test relation extraction with mocked pipeline."""
        
        # Setup mocks
        mock_pipe_instance = MagicMock()
        mock_pipeline.return_value = mock_pipe_instance
        
        # Mock model and tokenizer to avoid real downloads
        mock_model_cls.from_pretrained.return_value = MagicMock()
        mock_tokenizer_cls.from_pretrained.return_value = MagicMock()
        
        # Mock return value of the pipeline call for single item (batch of 1)
        mock_pipe_instance.return_value = [
            [{"generated_text": SAMPLE_REBEL_OUTPUT}]
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
    @patch("src.processing.extraction.nlp.AutoTokenizer")
    @patch("src.processing.extraction.nlp.AutoModelForSeq2SeqLM")
    @patch("src.processing.extraction.nlp.torch")
    def test_rebel_batch_extraction(self, mock_torch, mock_model_cls, mock_tokenizer_cls, mock_pipeline):
        """Test batch relation extraction."""
        
        # Setup mocks
        mock_pipe_instance = MagicMock()
        mock_pipeline.return_value = mock_pipe_instance
        mock_model_cls.from_pretrained.return_value = MagicMock()
        mock_tokenizer_cls.from_pretrained.return_value = MagicMock()
        
        # Mock return value for batch of 2 items
        mock_pipe_instance.return_value = [
            [{"generated_text": "<triplet> Apple <subj> Steve Jobs <obj> founded by"}], # Item 1
            [{"generated_text": "<triplet> Microsoft <subj> Bill Gates <obj> founded by"}] # Item 2
        ]
        
        # Enable sports mode to trigger logic, but mocked torch ensures no real GPU/Compile calls
        # mock_torch.cuda.is_available.return_value = True # Simulate GPU if needed
        
        extractor = TransformerExtractor(sports_mode=True)
        texts = ["Apple was founded by Steve Jobs.", "Microsoft was founded by Bill Gates."]
        results_batch = extractor.extract_relations_batch(texts)
        
        assert len(results_batch) == 2
        
        # Check Item 1
        assert results_batch[0][0]['head'] == 'Apple'
        assert results_batch[0][0]['tail'] == 'Steve Jobs'
        
        # Check Item 2
        assert results_batch[1][0]['head'] == 'Microsoft'
        assert results_batch[1][0]['tail'] == 'Bill Gates'

    @patch("src.processing.extraction.nlp.TRANSFORMERS_AVAILABLE", True)
    @patch("src.processing.extraction.nlp.pipeline") # still patch pipeline as it's used in __init__
    @patch("src.processing.extraction.nlp.AutoTokenizer")
    @patch("src.processing.extraction.nlp.AutoModelForSeq2SeqLM")
    @patch("src.processing.extraction.nlp.torch")
    def test_parsing_logic_edge_cases(self, mock_torch, mock_model, mock_tokenizer, mock_pipeline):
        """Test parsing logic with messy output."""
        # Setup minimal mocks for init
        mock_model.from_pretrained.return_value = MagicMock()
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        
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

