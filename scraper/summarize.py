"""
Text summarization using Ollama (preferred) or TextRank (fallback).
"""

import subprocess
import tempfile
from typing import List, Optional
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer

from .config import Config
from .models import Listing
from .utils import setup_logging

logger = setup_logging()

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK stopwords...")
    nltk.download('stopwords', quiet=True)


class OllamaSummarizer:
    """Summarizer using Ollama local LLM."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available and the model exists."""
        try:
            # Check if ollama command exists
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.warning("Ollama not available")
                return False
            
            # Check if our model is available
            if self.model_name not in result.stdout:
                logger.warning(f"Model {self.model_name} not found in Ollama")
                return False
            
            logger.info(f"Ollama available with model {self.model_name}")
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            logger.warning("Ollama not available or not responding")
            return False
    
    def summarize(self, text: str, num_sentences: int = 2) -> Optional[str]:
        """Summarize text using Ollama."""
        if not text.strip():
            return None
        
        # Prepare prompt
        prompt = f"""Summarize the following text about an animated TV show and/or toy line in exactly {num_sentences} sentences. Focus on the key facts about the show and toys. Use only the provided text - do not invent facts.

Text:
{text[:Config.CHUNK_SIZE]}

Summary:"""
        
        try:
            # Run ollama generate command
            cmd = ['ollama', 'generate', '-m', self.model_name]
            
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            
            if result.returncode == 0:
                summary = result.stdout.strip()
                
                # Clean up the summary
                summary = self._clean_summary(summary)
                
                if summary:
                    logger.debug(f"Ollama summary: {summary[:100]}...")
                    return summary
                else:
                    logger.warning("Ollama returned empty summary")
                    return None
            else:
                logger.error(f"Ollama failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Ollama summarization timed out")
            return None
        except Exception as e:
            logger.error(f"Error running Ollama: {e}")
            return None
    
    def _clean_summary(self, summary: str) -> str:
        """Clean up Ollama output."""
        # Remove common artifacts
        lines = summary.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and common artifacts
            if line and not line.startswith('Summary:') and not line.startswith('Here'):
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()


class TextRankSummarizer:
    """Fallback summarizer using TextRank algorithm."""
    
    def __init__(self, language: str = "english"):
        self.language = language
        self.stemmer = Stemmer(language)
        self.summarizer = TextRankSummarizer(self.stemmer)
        
    def summarize(self, text: str, num_sentences: int = 2) -> Optional[str]:
        """Summarize text using TextRank."""
        if not text.strip():
            return None
        
        try:
            # Parse text
            parser = PlaintextParser.from_string(text, Tokenizer(self.language))
            
            # Generate summary
            sentences = self.summarizer(parser.document, num_sentences)
            
            # Convert to string
            summary = ' '.join(str(sentence) for sentence in sentences)
            
            if summary.strip():
                logger.debug(f"TextRank summary: {summary[:100]}...")
                return summary.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"TextRank summarization error: {e}")
            return None


class SummarizationPipeline:
    """Main summarization pipeline that tries Ollama first, then TextRank."""
    
    def __init__(self):
        self.ollama_summarizer = None
        self.textrank_summarizer = TextRankSummarizer()
        
        # Try to initialize Ollama if configured
        if Config.has_ollama():
            try:
                self.ollama_summarizer = OllamaSummarizer(Config.OLLAMA_MODEL)
            except Exception as e:
                logger.warning(f"Could not initialize Ollama: {e}")
    
    def summarize_text(self, text: str, num_sentences: int = None) -> Optional[str]:
        """Summarize text using the best available method."""
        if not text.strip():
            return None
        
        num_sentences = num_sentences or Config.SUMMARY_SENTENCES
        
        # Try Ollama first if available
        if self.ollama_summarizer:
            try:
                summary = self.ollama_summarizer.summarize(text, num_sentences)
                if summary:
                    return summary
                else:
                    logger.info("Ollama failed, falling back to TextRank")
            except Exception as e:
                logger.warning(f"Ollama error, falling back to TextRank: {e}")
        
        # Fall back to TextRank
        return self.textrank_summarizer.summarize(text, num_sentences)
    
    def summarize_long_text(self, text: str, num_sentences: int = None) -> Optional[str]:
        """Summarize very long text using chunking and map-reduce approach."""
        if not text.strip():
            return None
        
        num_sentences = num_sentences or Config.SUMMARY_SENTENCES
        
        # If text is short enough, summarize directly
        if len(text) <= Config.CHUNK_SIZE:
            return self.summarize_text(text, num_sentences)
        
        # Split into chunks
        chunks = self._chunk_text(text, Config.CHUNK_SIZE)
        
        if len(chunks) <= 1:
            return self.summarize_text(text, num_sentences)
        
        logger.info(f"Long text detected, using {len(chunks)} chunks")
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Summarizing chunk {i+1}/{len(chunks)}")
            summary = self.summarize_text(chunk, max(1, num_sentences // 2))
            if summary:
                chunk_summaries.append(summary)
        
        if not chunk_summaries:
            logger.warning("No chunk summaries generated")
            return None
        
        # Combine chunk summaries
        combined = ' '.join(chunk_summaries)
        
        # If combined summary is still too long, summarize it again
        if len(combined) > Config.CHUNK_SIZE:
            return self.summarize_text(combined, num_sentences)
        
        return combined
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Start new chunk
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add last chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks
    
    def enhance_listing_with_summary(self, listing: Listing, source_text: str) -> Listing:
        """Add summary to a listing based on source text."""
        if listing.description_summary:
            logger.debug(f"Listing already has summary: {listing.slug}")
            return listing
        
        # Extract relevant text for summarization
        text_to_summarize = self._extract_relevant_text(source_text, listing)
        
        if not text_to_summarize:
            logger.warning(f"No relevant text found for {listing.slug}")
            return listing
        
        # Generate summary
        summary = self.summarize_long_text(text_to_summarize)
        
        if summary:
            listing.description_summary = summary
            logger.info(f"Generated summary for {listing.slug}: {summary[:50]}...")
        else:
            logger.warning(f"Could not generate summary for {listing.slug}")
        
        return listing
    
    def _extract_relevant_text(self, full_text: str, listing: Listing) -> str:
        """Extract the most relevant portion of text for summarization."""
        # Start with full text, but prioritize sections that mention
        # the show title or toyline name
        
        relevant_text = full_text
        
        # If we have show or toyline names, try to find relevant sections
        search_terms = []
        if listing.show_title:
            search_terms.append(listing.show_title.lower())
        if listing.toyline_name and listing.toyline_name != listing.show_title:
            search_terms.append(listing.toyline_name.lower())
        
        if search_terms:
            # Find paragraphs that mention our terms
            paragraphs = full_text.split('\n\n')
            relevant_paragraphs = []
            
            for paragraph in paragraphs:
                paragraph_lower = paragraph.lower()
                if any(term in paragraph_lower for term in search_terms):
                    relevant_paragraphs.append(paragraph)
            
            if relevant_paragraphs:
                relevant_text = '\n\n'.join(relevant_paragraphs)
        
        return relevant_text[:Config.CHUNK_SIZE * 3]  # Limit to reasonable size