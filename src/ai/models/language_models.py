"""Language model clients and interfaces."""

from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


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
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        raise NotImplementedError


class SentenceTransformerModel(LanguageModel):
    """Local embedding model using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the model.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Run 'pip install sentence-transformers'.")
        self.model = SentenceTransformer(model_name)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generation is not supported for this model."""
        raise NotImplementedError("SentenceTransformerModel only supports embeddings.")
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as a list of floats
        """
        embedding = self.model.encode(text)
        if isinstance(embedding, np.ndarray):
            return embedding.tolist()
        return embedding


class OllamaModel(LanguageModel):
    """LLM implementation using Ollama."""

    def __init__(self, model_name: str = "llama3"):
        """Initialize the model.

        Args:
            model_name: Name of the Ollama model to use
        """
        try:
            import ollama
            self.client = ollama.Client()
        except ImportError:
            raise ImportError("ollama is not installed. Run 'pip install ollama'.")
        
        self.model_name = model_name

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (e.g., system prompt)

        Returns:
            Generated text
        """
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                **kwargs
            )
            return response['response']
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")

    def embed(self, text: str) -> List[float]:
        """Generate embeddings using Ollama (optional)."""
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            raise RuntimeError(f"Ollama embedding failed: {str(e)}")
