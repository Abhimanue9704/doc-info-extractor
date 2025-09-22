def chunk_text_with_metadata(text, source_id, title, path, chunk_size=150, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    index = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "source_id": source_id,
            "chunk_index": index,
            "text": chunk_text,
            "title": title,
            "doc_path": path
        })
        start += chunk_size - overlap
        index += 1
    return chunks

