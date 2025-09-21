from flask import Flask, request, jsonify
import PyPDF2
import os
import re
import hashlib
from chunks import chunk_text_with_metadata
from db_insertion import insert_chunks
from db import init_db
from gen_embeddings import generate_embeddings, build_faiss_index

app = Flask(__name__)

def clean_text(text):
    text = re.sub(r'\uf0b7', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Read file bytes directly
    file_bytes = file.read()
    sha = hashlib.sha256(file_bytes).hexdigest()

    # Save file with SHA as filename
    os.makedirs("uploads", exist_ok=True)
    new_pdf_path = os.path.join("uploads", f"{sha}.pdf")
    with open(new_pdf_path, "wb") as f:
        f.write(file_bytes)

    # Extract text and clean
    raw_text = extract_text_from_pdf(new_pdf_path)
    cleaned_text = clean_text(raw_text)

    # Chunk, store, generate embeddings
    chunks_with_meta = chunk_text_with_metadata(cleaned_text, sha, new_pdf_path)
    init_db()
    insert_chunks(chunks_with_meta)
    embeddings = generate_embeddings(chunks_with_meta)
    build_faiss_index(embeddings)

    return jsonify({"status": "success", "doc_id": sha, "chunks": len(chunks_with_meta)})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
