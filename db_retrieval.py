import sqlite3
def get_chunk_by_id(source_id,chunk_index):
    db_path="doc_chunks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM chunks WHERE source_id = ? and chunk_index= ?", (source_id,chunk_index))
    row = cursor.fetchone()
    
    conn.close()
    return row