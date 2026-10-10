import asyncio
import logging
import threading
from functools import lru_cache
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Global state for the model
_model = None
_model_lock = threading.Lock()
_model_load_failed = False

def _get_model():
    global _model, _model_load_failed
    if _model is not None:
        return _model
    
    if _model_load_failed:
        return None

    with _model_lock:
        # Double-check inside lock
        if _model is not None:
            return _model
        if _model_load_failed:
            return None
            
        try:
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2' (this may download on first run)...")
            from sentence_transformers import SentenceTransformer
            # Load locally without external LLM API
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Model loaded successfully.")
            return _model
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            _model_load_failed = True
            return None

@lru_cache(maxsize=1024)
def _encode_text(text: str):
    """Cached synchronous function to encode a single string."""
    model = _get_model()
    if model is None:
        return None
    try:
        # Generate the embedding
        return model.encode(text)
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        return None

def _calculate_similarity_sync(text1: str, text2: str) -> Optional[float]:
    emb1 = _encode_text(text1)
    emb2 = _encode_text(text2)
    if emb1 is None or emb2 is None:
        return None
        
    try:
        from sentence_transformers.util import cos_sim
        score = cos_sim(emb1, emb2)
        return float(score[0][0])
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return None

def _calculate_max_similarity_sync(target: str, candidates: List[str]) -> tuple[Optional[float], Optional[str]]:
    """Returns the (max_score, best_candidate) against the target."""
    emb_target = _encode_text(target)
    if emb_target is None or not candidates:
        return None, None
        
    try:
        from sentence_transformers.util import cos_sim
        best_score = -1.0
        best_cand = None
        for cand in candidates:
            emb_cand = _encode_text(cand)
            if emb_cand is not None:
                score = float(cos_sim(emb_target, emb_cand)[0][0])
                if score > best_score:
                    best_score = score
                    best_cand = cand
                    
        if best_cand is None:
            return None, None
            
        return best_score, best_cand
    except Exception as e:
        logger.error(f"Error in max similarity: {e}")
        return None, None

async def calculate_similarity(text1: str, text2: str) -> Optional[float]:
    """Asynchronous wrapper to calculate cosine similarity without blocking the event loop."""
    return await asyncio.to_thread(_calculate_similarity_sync, text1, text2)

async def calculate_max_similarity(target: str, candidates: List[str]) -> tuple[Optional[float], Optional[str]]:
    """
    Given a target string and a list of candidate strings, returns the highest cosine 
    similarity score and the corresponding candidate string.
    """
    return await asyncio.to_thread(_calculate_max_similarity_sync, target, candidates)

def is_model_available() -> bool:
    """Check if model is loaded or can be loaded."""
    return _get_model() is not None
