from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
import faiss

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(chunks_with_meta, db_path="doc_chunks.db"):
    # print(f"Generating embeddings for {len(chunks_with_meta)} chunks...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    embeddings = []
    
    for chunk in chunks_with_meta:
        source_id, chunk_index, text = chunk['source_id'],chunk['chunk_index'],chunk['text']  # FIXED: Added path
        
        # print(text)
            
        emb = model.encode(text)
        # print(emb)

        cursor.execute('''
        INSERT INTO embeddings (source_id, chunk_index, embedding_vector)
        VALUES (?, ?, ?)
        ''', (source_id, chunk_index, sqlite3.Binary(emb.tobytes())))
        
        embeddings.append(emb)
    
    conn.commit()
    conn.close()
    return np.stack(embeddings).astype('float32')

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    
    try:
        index = faiss.read_index("embeddings.index")
        # print(f"Loaded existing index with {index.ntotal} embeddings")
    except:
        index = faiss.IndexFlatIP(dim)
        # print("Created new FAISS index")
    
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    faiss.write_index(index, "embeddings.index")
    # print(f"Updated FAISS index, now has {index.ntotal} embeddings")
    
def search(query, top_k):
    print(f"Searching for: '{query}'")
    
    # 1. Search FAISS for most similar embeddings
    faiss_index = faiss.read_index("embeddings.index")
    print(f"Loaded FAISS index with {faiss_index.ntotal} embeddings")
    
    query_emb = model.encode([query]).astype('float32')
    faiss.normalize_L2(query_emb.reshape(1, -1))
    
    scores, indices = faiss_index.search(query_emb.reshape(1, -1), top_k)
    print(f"FAISS search results - scores: {scores[0]}, indices: {indices[0]}")
    
    # 2. Get the FAISS embeddings and find matching ones in embeddings table
    conn = sqlite3.connect("doc_chunks.db")
    cursor = conn.cursor()
    
    results = []
    for i, (faiss_idx, score) in enumerate(zip(indices[0], scores[0])):
        print(f"Processing result {i}: faiss_idx={faiss_idx}, score={score}")
        
        if faiss_idx == -1:
            print(f"  Skipping invalid index")
            continue
        
        # Get the embedding from embeddings table by position
        cursor.execute("""
            SELECT source_id, chunk_index, embedding_vector 
            FROM embeddings 
            ORDER BY ROWID 
            LIMIT 1 OFFSET ?
        """, (int(faiss_idx),))
        
        emb_row = cursor.fetchone()
        print(f"  Embeddings table query result: {emb_row is not None}")
        
        if emb_row:
            source_id, chunk_index, _ = emb_row
            print(f"  Found embedding: source_id={source_id[:8]}..., chunk_index={chunk_index}")
            
            # 3. Get the actual text from chunks table
            cursor.execute("""
                SELECT text, doc_path
                FROM chunks 
                WHERE source_id = ? AND chunk_index = ?
            """, (source_id, chunk_index))
            
            chunk_row = cursor.fetchone()
            print(f"  Chunks table query result: {chunk_row is not None}")
            
            if chunk_row:
                text,doc_path = chunk_row
                result = {
                    'source_id': source_id,
                    'chunk_index': chunk_index, 
                    'text': text,  # Truncate for debug
                    'similarity': float(score),
                    'doc_path': doc_path
                }
                results.append(result)
                print(f"  Added result: {result}")
    
    conn.close()
    print(f"Final results count: {len(results)}")
    return results