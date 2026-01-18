"""NLP extraction pipeline."""

import logging
from typing import List, Dict, Any

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pipeline = None
    TRANSFORMERS_AVAILABLE = False

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


class TransformerExtractor(NLPExtractor):
    """Advanced NLP extraction using Hugging Face Transformers (REBEL)."""
    
    def __init__(self, model_name: str = "Babelscape/rebel-large", use_gpu: bool = False):
        """Initialize the REBEL model pipeline.
        
        Args:
            model_name: HF model name for REBEL
            use_gpu: Whether to use GPU if available
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers library is not available. Install it to use TransformerExtractor.")
        
        device = 0 if use_gpu else -1
        try:
            self.pipe = pipeline("text2text-generation", model=model_name, tokenizer=model_name, device=device)
            self.tokenizer = self.pipe.tokenizer
            logger.info(f"Loaded REBEL model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load transformer model '{model_name}': {e}")
            self.pipe = None

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities.
        
        Note: REBEL is primarily for relations. This method returns entities involved in relations.
        For pure NER, SpacyExtractor is recommended.
        """
        relations = self.extract_relations(text)
        entities = set()
        for r in relations:
            entities.add(r['head'])
            entities.add(r['tail'])
            
        return [{"text": e, "label": "ENTITY", "start": 0, "end": 0} for e in entities]

    def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """Extract relations using REBEL.
        
        Returns:
            List of dicts: {'head': str, 'type': str, 'tail': str}
        """
        if not self.pipe:
            return []

        # REBEL generation parameters
        gen_kwargs = {
            "max_length": 256,
            "length_penalty": 0,
            "num_beams": 3,
            "num_return_sequences": 3,
        }

        generated_results = self.pipe(text, **gen_kwargs)
        
        triplets = []
        for result in generated_results:
            generated_text = result['generated_text']
            extracted = self._parse_rebel_output(generated_text)
            triplets.extend(extracted)
            
        # Deduplicate
        unique_triplets = []
        seen = set()
        for t in triplets:
            key = (t['head'], t['type'], t['tail'])
            if key not in seen:
                seen.add(key)
                unique_triplets.append(t)
                
        return unique_triplets

    def _parse_rebel_output(self, text: str) -> List[Dict[str, str]]:
        """Parse the custom token format of REBEL."""
        triplets = []
        relation, subject, relation, object_ = '', '', '', ''
        text = text.strip()
        current = 'x'
        text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")
        token_parts = text_replaced.split("<triplet>")
        
        for part in token_parts:
            if not part:
                continue
                
            # REBEL format: <triplet> subject <subj> object <obj> relation
            # Note: The raw output often needs careful splitting
            # A common reliable decoding pattern for REBEL:
            
            try:
                # Split by <subj> and <obj>
                # Expected format in part: " Subject Name <subj> Object Name <obj> Relation Name "
                if "<subj>" in part and "<obj>" in part:
                    sub_split = part.split("<subj>")
                    subj = sub_split[0].strip()
                    rest = sub_split[1]
                    
                    obj_split = rest.split("<obj>")
                    obj = obj_split[0].strip()
                    rel = obj_split[1].strip()
                    
                    if subj and obj and rel:
                        triplets.append({
                            "head": subj,
                            "type": rel,
                            "tail": obj
                        })
            except Exception:
                continue
                
        return triplets
