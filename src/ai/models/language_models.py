"""Language model clients and interfaces."""


class LanguageModel:
    """Base interface for language models.
    
    Provides abstraction over different LLM implementations (Ollama, OpenAI, etc.)
    """
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional model parameters
            
        Returns:
            Generated text
        """
        raise NotImplementedError
    
    def embed(self, text: str) -> list:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        raise NotImplementedError
