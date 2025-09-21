import sqlite3
def fetch_chunks(db_path="doc_chunks.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_id, chunk_index, text, doc_path FROM chunks LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    return rows


