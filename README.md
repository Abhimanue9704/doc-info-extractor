# Document Info Extractor

A comprehensive document ingestion, embedding, search, and reranking pipeline with REST API support for querying documents using both baseline vector search and hybrid reranker capabilities.

## Features

- **PDF Document Ingestion**: Upload and process PDF files into a vector database
- **Semantic Search**: Vector-based similarity search across document content
- **Hybrid Reranking**: Advanced reranking combining vector similarity and keyword matching
- **REST API**: Easy-to-use endpoints for document upload and querying
- **Multiple Query Modes**: Baseline vector search and enhanced reranker modes

## Setup

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd document-info-extractor
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv env
   ```

3. **Activate the environment:**
   - **Windows:** 
     ```bash
     .\env\Scripts\activate
     ```
   - **Linux/Mac:** 
     ```bash
     source env/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Document Upload

#### Using Python Script
```bash
python reader.py
```

#### Using REST API
```bash
curl -X POST http://localhost:5001/upload_pdf \
  -F "file=@path_to_file.pdf"
```

### 2. Querying Documents

#### Using Python Script
```bash
python query.py
```

#### Using REST API

**Baseline Mode:**
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "k": 3,
    "mode": "baseline",
    "q": "What documents must be available to authorities to show compliance with the Machinery Directive?"
  }'
```

**Reranker Mode:**
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "k": 3,
    "mode": "reranker",
    "q": "What documents must be available to authorities to show compliance with the Machinery Directive?"
  }'
```

## API Endpoints

### Upload PDF
- **URL:** `POST /upload_pdf`
- **Content-Type:** `multipart/form-data`
- **Parameters:** `file` (PDF file)

### Query Documents
- **URL:** `POST /ask`
- **Content-Type:** `application/json`
- **Parameters:**
  - `q` (string): Query text
  - `k` (integer): Number of results to return
  - `mode` (string): `"baseline"` or `"reranker"`

## Performance Comparison

**Test Query:** *"What documents must be available to authorities to show compliance with the Machinery Directive?"*

| Metric | Baseline | Reranker |
|--------|----------|----------|
| **Retrieved Answer** | "if compliance with these standards is ensured it can be assumed that the requirements of the machinery directive are also fulfilled" | "part 3 steps to meet machinery directive requirements37 step 9 proving compliance before a machine can be placed on the market the manufacturer must ensure that the machine is implemented in conformance with harmonized standards" |
| **Source Document** | Eaton — Safety Manual (EN ISO 13849-1 and IEC 62061) | EN_TechnicalguideNo10_REVF |
| **Chunk ID** | chunk 325 | chunk 89 |
| **Confidence Score** | 0.815 | 0.716 |
| **Notes** | Top vector match; no reranker used | Hybrid reranker used; better contextual relevance |

## Project Structure

```
document-info-extractor/
├── reader.py              # PDF ingestion and processing with upload API endpoint
├── chunks.py             # Document chunking utilities
├── gen_embeddings.py     # Embedding generation
├── db_insertion.py       # Database operations
├── query.py              # Query interface with query API endpoint
├── baseline.py           # Pure Vector similarity implementation
├── reranker.py           # Hybrid reranking implementation
├── requirements.txt      # Python dependencies
├── sources.json          # Document metadata
├── example.json          # 8 test questions
├── curl_example.txt      # 2 curl requests example
├── db.py                 # Contains database schema
└── README.md            # This file
```

## Key Components

### Ingestion Pipeline
- **Document Processing**: Extract text content from PDF files
- **Chunking**: Split documents into manageable, searchable segments
- **Embedding Generation**: Convert text chunks into vector representations
- **Database Storage**: Store embeddings with metadata for retrieval

### Search & Retrieval
- **Baseline Search**: Pure vector similarity search
- **Hybrid Reranker**: Combines semantic similarity with keyword matching
- **Result Ranking**: Confidence scoring and relevance optimization

### REST API
- **Document Upload**: Secure PDF file handling and processing
- **Query Interface**: Flexible querying with multiple modes
- **Response Format**: Structured JSON responses with metadata

## Key Learnings

- **Vector Database Architecture**: Implementing efficient semantic search across large document collections requires careful consideration of chunking strategies and embedding quality
- **Hybrid Retrieval Benefits**: Combining vector similarity with keyword-based signals significantly improves answer relevance, especially for technical queries requiring exact terminology matches
- **API Design**: REST endpoints provide seamless integration capabilities while maintaining separation between document ingestion and querying workflows
- **Preprocessing Impact**: Proper document chunking, metadata preservation, text preprocessing using SHA256 are critical for maintaining traceability and improving retrieval accuracy

## Testing

The repository includes `example.json` with 8 test queries designed to evaluate both baseline and reranker performance across different types of document content and query complexity.
The repository includes 'curl_example.txt' with 2 curl requests one easy and one tricky.
