"""NLP extraction pipeline."""


class NLPExtractor:
    """Base class for NLP extraction operations.
    
    Responsible for extracting entities, relations, and features from text.
    """
    
    def extract_entities(self, text: str):
        """Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entities
        """
        raise NotImplementedError
    
    def extract_relations(self, text: str):
        """Extract relations from text.
        
        Args:
            text: Input text
            
        Returns:
            List of relations
        """
        raise NotImplementedError
