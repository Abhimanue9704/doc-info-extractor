import re
import torch
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from reader import clean_text

model = SentenceTransformer('all-MiniLM-L6-v2')

def keyword_overlap(query, sentence):
    """Compute fraction of query words appearing in the sentence."""
    query_words = set(re.findall(r'\w+', query.lower()))
    sentence_words = set(re.findall(r'\w+', sentence.lower()))
    if not query_words:
        return 0.0
    return len(query_words & sentence_words) / len(query_words)

def hybrid_reranker(query, top_k_chunks, alpha=0.7, beta=0.3):
    """
    query: string
    top_k_chunks: list of dicts with keys 'text', 'source_id', 'chunk_index', 'doc_path', 'similarity'
    alpha: weight for vector similarity
    beta: weight for keyword overlap
    """
    query_emb = model.encode([query], convert_to_tensor=True)
    candidates = []

    for chunk in top_k_chunks:
        sentences = sent_tokenize(chunk['text'])
        for sent in sentences:
            sent_clean = clean_text(sent)
            sent_emb = model.encode([sent_clean], convert_to_tensor=True)
            vector_sim = torch.cosine_similarity(query_emb, sent_emb).item()
            kw_overlap = keyword_overlap(query, sent_clean)
            
            combined_score = alpha * vector_sim + beta * kw_overlap
            
            candidates.append({
                'sentence': sent_clean,
                'citation': {
                    'source_id': chunk['source_id'],
                    'chunk_index': chunk['chunk_index'],
                    'title': chunk['title'],
                    'doc_path': chunk['doc_path']
                },
                'vector_similarity': vector_sim,
                'keyword_overlap': kw_overlap,
                'combined_score': combined_score
            })
    
    if not candidates:
        return None, None, None
    
    best_candidate = max(candidates, key=lambda x: x['combined_score'])
    return best_candidate['sentence'], best_candidate['combined_score'], best_candidate['citation']

