"""
Simple function to extract sentences and return the exact page location of paragraphs.
Supports PDF URLs only.
"""
import re
import io
import hashlib

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import requests
except ImportError:
    requests = None

# Import cache manager
try:
    from cache_manager import get_cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("Warning: Cache manager not available. Caching disabled.")


def _normalize_whitespace(text):
    """
    Normalize whitespace in text by replacing all whitespace characters 
    (spaces, newlines, tabs, etc.) with single spaces.
    
    Args:
        text (str): Text to normalize
    
    Returns:
        str: Normalized text with single spaces
    """
    if not text:
        return ""
    # Replace all whitespace characters (spaces, newlines, tabs, etc.) with single space
    normalized = re.sub(r'\s+', ' ', text)
    # Remove extra spaces around punctuation
    normalized = re.sub(r'\s+([.,;:!?])', r'\1', normalized)
    normalized = re.sub(r'([.,;:!?])\s+', r'\1 ', normalized)
    return normalized.strip()

def _normalize_text_for_search(text):
    """
    Normalize text for more flexible searching by:
    - Normalizing whitespace
    - Converting to lowercase
    
    Args:
        text (str): Text to normalize
    
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
    return _normalize_whitespace(text).lower()

def _extract_context(text_normalized, match_index, match_length, context_size=150):
    """
    Extract context around a matched text.
    
    Args:
        text_normalized (str): Normalized text to extract from
        match_index (int): Starting index of the match
        match_length (int): Length of the matched text
        context_size (int): Number of characters to include before/after
    
    Returns:
        str: Context around the match
    """
    context_start = max(0, match_index - context_size)
    context_end = min(len(text_normalized), match_index + match_length + context_size)
    return text_normalized[context_start:context_end].strip()

def _create_result(page_num, sentence_text, context):
    """
    Create a result dictionary.
    
    Args:
        page_num (int): Page number where match was found
        sentence_text (str): Original search text
        context (str): Context around the match
    
    Returns:
        dict: Result dictionary
    """
    return {
        'found': True,
        'page_number': page_num,
        'sentence': sentence_text,
        'context': context
    }


def _get_pdf_from_url(url):
    """
    Download PDF from URL and return as BytesIO object.
    
    Args:
        url (str): URL to the PDF file
    
    Returns:
        io.BytesIO: PDF content as BytesIO object
    
    Raises:
        ImportError: If requests library is not installed
        Exception: If download fails
    """
    if requests is None:
        raise ImportError("requests is required for URL support. Install it with: pip install requests")
    
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if content type is PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            # Still try to read as PDF even if content-type doesn't indicate PDF
            pass
        
        pdf_content = io.BytesIO(response.content)
        return pdf_content
    except Exception as e:
        raise Exception(f"Failed to download PDF from URL: {str(e)}")


def _get_pdf_from_filepath(filepath):
    """
    Get PDF from local file path.
    
    Args:
        filepath (str): Local file path to the PDF
    
    Returns:
        io.BytesIO or str: PDF content as BytesIO object or file path
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    from pathlib import Path
    pdf_path = Path(filepath)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {filepath}")
    
    # Return the path directly - pdfplumber can handle file paths
    return str(pdf_path)


def extract_sentence_location(
    pdf_url=None,
    pdf_filepath=None,
    sentence_text=None,
    case_sensitive=False,
    fuzzy_match=True
):
    """
    Extract a sentence from a PDF and return the exact page number where it's located.
    Supports both PDF URLs and local file paths.
    
    Args:
        pdf_url (str, optional): URL to the PDF file
        pdf_filepath (str, optional): Local file path to the PDF
        sentence_text (str): The sentence or paragraph text to search for
        case_sensitive (bool): If True, search is case-sensitive (default: False)
        fuzzy_match (bool): If True, uses partial matching with key phrases (default: True)
    
    Returns:
        dict: Dictionary containing:
            - 'found' (bool): Whether the sentence was found
            - 'page_number' (int): Page number where the sentence was found (1-indexed)
            - 'sentence' (str): The found sentence text
            - 'context' (str): Optional context around the sentence
    
    Raises:
        ValueError: If neither pdf_url nor pdf_filepath is provided
        ImportError: If required libraries are not installed
    
    Example:
        # From URL
        result = extract_sentence_location(
            pdf_url='https://example.com/document.pdf',
            sentence_text='This is a sample sentence.'
        )
        
        # From file path
        result = extract_sentence_location(
            pdf_filepath='/path/to/document.pdf',
            sentence_text='This is a sample sentence.'
        )
        
        if result['found']:
            print(f"Found on page {result['page_number']}")
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required. Install it with: pip install pdfplumber")
    
    if not pdf_url and not pdf_filepath:
        raise ValueError("Either pdf_url or pdf_filepath must be provided")
    
    if not sentence_text:
        return {
            'found': False,
            'page_number': None,
            'sentence': None,
            'context': None
        }
    
    # Normalize the search text
    normalize_func = _normalize_whitespace if case_sensitive else _normalize_text_for_search
    sentence_text_normalized = normalize_func(sentence_text)
    
    # For very long text (over 500 chars), extract key sentences/phrases instead of using the whole text
    if len(sentence_text_normalized) > 500:
        # Split into sentences and use the first few meaningful sentences
        sentences = re.split(r'[.!?]+\s+', sentence_text)
        # Filter out very short sentences and take first 3-5 meaningful ones
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        if meaningful_sentences:
            # Use the first meaningful sentence as primary search, plus combinations
            primary_search = normalize_func(meaningful_sentences[0])
            # Also try combining first 2-3 sentences
            if len(meaningful_sentences) > 1:
                combined_search = normalize_func(' '.join(meaningful_sentences[:2]))
            else:
                combined_search = primary_search
        else:
            # Fallback: if no sentence boundaries found, use first 200-400 chars as key phrases
            # Try multiple lengths to increase chances of match
            primary_search = normalize_func(sentence_text[:300])
            combined_search = normalize_func(sentence_text[:500])
    else:
        primary_search = sentence_text_normalized
        combined_search = sentence_text_normalized
    
    # Prepare key phrases for fuzzy matching
    key_phrases = []
    if fuzzy_match:
        # Always try the primary search first
        if primary_search not in key_phrases:
            key_phrases.append(primary_search)
        
        # For combined search (if different from primary)
        if combined_search != primary_search and combined_search not in key_phrases:
            key_phrases.append(combined_search)
        
        # Extract key phrases from the search text
        words = primary_search.split()
        if len(words) > 0:
            # For long text, try shorter phrases (20-50 words)
            if len(words) > 50:
                # Try phrases of 20, 30, 40, 50 words
                for phrase_len in [20, 30, 40, 50]:
                    if phrase_len <= len(words):
                        phrase = ' '.join(words[:phrase_len])
                        if phrase not in key_phrases:
                            key_phrases.append(phrase)
            else:
                # For shorter text, try from 30% to full
                min_words = max(5, int(len(words) * 0.3))
                max_words = min(len(words), 30)  # Cap at 30 words for performance
                # Try a few key lengths
                for phrase_len in [min_words, int(len(words) * 0.5), int(len(words) * 0.7), len(words)]:
                    if phrase_len <= len(words) and phrase_len >= min_words:
                        phrase = ' '.join(words[:phrase_len])
                        if phrase not in key_phrases:
                            key_phrases.append(phrase)
    
    # CACHE OPTIMIZATION: Check if we have a cached page lookup result
    pdf_identifier = pdf_url or pdf_filepath
    if CACHE_AVAILABLE and pdf_identifier:
        cache_manager = get_cache_manager()
        cached_page = cache_manager.get_page_lookup(pdf_identifier, primary_search)
        if cached_page is not None:
            print(f"✓ Found cached page lookup: page {cached_page}")
            return _create_result(cached_page, sentence_text, None)
    
    # Get PDF source
    try:
        if pdf_url:
            pdf_source = _get_pdf_from_url(pdf_url)
        else:
            pdf_source = _get_pdf_from_filepath(pdf_filepath)
    except Exception as e:
        return {
            'found': False,
            'page_number': None,
            'sentence': sentence_text,
            'context': None,
            'error': str(e)
        }
    
    try:
        with pdfplumber.open(pdf_source) as pdf:
            total_pages = len(pdf.pages)
            print(f"Searching through {total_pages} pages of PDF...")
            print(f"Original text length: {len(sentence_text)} characters")
            print(f"Primary search length: {len(primary_search)} characters")
            print(f"Number of key phrases for fuzzy matching: {len(key_phrases)}")
            
            # CACHE OPTIMIZATION: Load cached page texts if available
            cached_pages = {}
            if cache_manager is None and CACHE_AVAILABLE:
                try:
                    from config import settings
                    if settings.enable_caching:
                        cache_manager = get_cache_manager()
                        for page_num in range(1, total_pages + 1):
                            cached_text = cache_manager.get_pdf_page_text(pdf_identifier, page_num)
                            if cached_text:
                                cached_pages[page_num] = cached_text
                except Exception as e:
                    print(f"Warning: Cache load failed: {e}")
                    cache_manager = None
            
            # Build list of search phrases (primary first, then key phrases)
            search_phrases = [primary_search]
            if fuzzy_match and key_phrases:
                for phrase in key_phrases:
                    if phrase and len(phrase.strip()) >= 10 and phrase not in search_phrases:
                        search_phrases.append(phrase)
            
            # Try each search phrase across all pages (most specific first)
            for phrase_idx, search_phrase in enumerate(search_phrases):
                if not search_phrase or len(search_phrase.strip()) < 10:
                    continue
                
                print(f"Trying phrase {phrase_idx + 1}/{len(search_phrases)} (length: {len(search_phrase)} chars): {search_phrase[:100]}...")
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    # CACHE OPTIMIZATION: Use cached text if available, otherwise extract and cache
                    if page_num in cached_pages:
                        text_normalized = normalize_func(cached_pages[page_num])
                    else:
                        text = page.extract_text()
                        if not text:
                            continue
                        
                        text_normalized = normalize_func(text)
                        
                        # Cache the extracted text for future use
                        if cache_manager:
                            cache_manager.set_pdf_page_text(pdf_identifier, page_num, text_normalized)
                    
                    # Search for this phrase
                    match_index = text_normalized.find(search_phrase)
                    if match_index != -1:
                        context = _extract_context(text_normalized, match_index, len(search_phrase))
                        print(f"✓ Found match on page {page_num} with phrase {phrase_idx + 1} (length: {len(search_phrase)} chars)")
                        
                        # CACHE OPTIMIZATION: Cache the page lookup result
                        if cache_manager:
                            cache_manager.set_page_lookup(pdf_identifier, primary_search, page_num)
                        
                        return _create_result(page_num, sentence_text, context)
            
            print(f"✗ Text not found in any of the {total_pages} pages after trying {len(search_phrases)} phrases")
    except Exception as e:
        return {
            'found': False,
            'page_number': None,
            'sentence': sentence_text,
            'context': None,
            'error': str(e)
        }
    
    return {
        'found': False,
        'page_number': None,
        'sentence': sentence_text,
        'context': None
    }
