import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_answer_with_citation(query, chunk):

    text = chunk.get('text', "")
    sentences = sent_tokenize(text)
    
    if not sentences:
        return None, None, None

    # Query embedding (shape [1, hidden_dim])
    query_emb = model.encode([query], convert_to_tensor=True)

    best_sentence, best_score = None, -1.0
    from reader import clean_text
    for sent in sentences:
        sent=clean_text(sent)
        sent_emb = model.encode([sent], convert_to_tensor=True)
        # Both query_emb and sent_emb now have shape [1, hidden_dim]
        score = torch.cosine_similarity(query_emb, sent_emb).item()
        
        if score > best_score:
            best_score = score
            best_sentence = sent

    citation = {
        "doc_path": chunk.get("doc_path"),
        "source_id": chunk.get("source_id"),
        "chunk_index": chunk.get("chunk_index")
    }

    return best_sentence, best_score, citation
