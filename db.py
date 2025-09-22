import sqlite3

def init_db(db_path="doc_chunks.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chunks (
        source_id TEXT,
        chunk_index INTEGER,
        text TEXT,
        title TEXT,
        doc_path TEXT,
        PRIMARY KEY(source_id,chunk_index)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        source_id TEXT,
        chunk_index INTEGER,
        embedding_vector BLOB,
        FOREIGN KEY(source_id, chunk_index)
            REFERENCES chunks(source_id, chunk_index)
    )
    ''')
    
    conn.commit()
    conn.close()
