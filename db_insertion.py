import sqlite3
def insert_chunks(chunks, db_path="doc_chunks.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for chunk in chunks:
        cursor.execute('''
        INSERT INTO chunks (source_id, chunk_index,text,title,doc_path)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            chunk["source_id"],
            chunk["chunk_index"],
            chunk["text"],
            chunk["title"],
            chunk["doc_path"]
        ))
    
    conn.commit()
    conn.close()

