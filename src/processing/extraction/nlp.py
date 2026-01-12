"""NLP extraction pipeline."""

import logging
from typing import List, Dict, Any, Tuple

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class NLPExtractor:
    """Base class for NLP extraction operations.
    
    Responsible for extracting entities, relations, and features from text.
    """
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entities with 'text', 'label', 'start', 'end'
        """
        raise NotImplementedError
    
    def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """Extract relations from text.
        
        Args:
            text: Input text
            
        Returns:
            List of relations with 'head', 'type', 'tail'
        """
        raise NotImplementedError


class SpacyExtractor(NLPExtractor):
    """NLP extraction using spaCy."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize spaCy model.
        
        Args:
            model_name: Name of the spaCy model to load
        """
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                if not spacy.util.is_package(model_name):
                    logger.warning(f"spaCy model '{model_name}' not found. Attempting to download...")
                    spacy.cli.download(model_name)
                self.nlp = spacy.load(model_name)
            except Exception as e:
                logger.error(f"Failed to load spaCy model '{model_name}': {e}")
        else:
            logger.warning("spaCy not installed. NLP features will be limited.")

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text.
        
        Returns:
            List of dicts: {'text': str, 'label': str, 'start': int, 'end': int}
        """
        if not self.nlp:
            logger.warning("No NLP model loaded. Returning empty entities.")
            return []
            
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        return entities

    def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """Extract simple Subject-Verb-Object relations.
        
        Note: This is a rule-based approximation using dependency parsing.
        
        Returns:
            List of dicts: {'head': str, 'type': str, 'tail': str}
        """
        if not self.nlp:
            return []
            
        doc = self.nlp(text)
        relations = []
        
        # Simple heuristic: Find verb with subject and object children
        for token in doc:
            if token.pos_ == "VERB":
                subj = None
                obj = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subj = child
                    if child.dep_ in ("dobj", "pobj", "attr"):
                        obj = child
                
                if subj and obj:
                    relations.append({
                        "head": subj.text,
                        "type": token.lemma_,  # Use lemma for the relation type (e.g., "extracted" -> "extract")
                        "tail": obj.text
                    })
                    
        return relations
