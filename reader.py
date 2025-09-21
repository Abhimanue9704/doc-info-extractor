import PyPDF2
from chunks import chunk_text_with_metadata
from db_insertion import insert_chunks
from db import init_db
import re
import os
import hashlib
from verify_db import fetch_chunks
from gen_embeddings import generate_embeddings,build_faiss_index,search
from db_retrieval import get_chunk_by_id
from sentence_extractor import extract_answer_with_citation

def clean_text(text):
    text = re.sub(r'\uf0b7', '', text)  
    text = re.sub(r'\s+', ' ', text)
    return text.strip()



def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text
if __name__ == "__main__":
    pdf_path = "contract.pdf"
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(raw_text)
    sha=hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()

    new_pdf_path = os.path.join(os.path.dirname(pdf_path), f"{sha}.pdf")
    os.rename(pdf_path, new_pdf_path)

    chunks_with_meta = chunk_text_with_metadata(cleaned_text,sha,new_pdf_path)
    print(chunks_with_meta)
    init_db()
    insert_chunks(chunks_with_meta)

    embeddings= generate_embeddings(chunks_with_meta)

    build_faiss_index(embeddings)

