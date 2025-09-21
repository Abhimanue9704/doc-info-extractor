from flask import Flask, request, jsonify
from reader import search
from sentence_extractor import extract_answer_with_citation

app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("q")
    top_k = data.get("k", 3)
    
    if not query:
        return jsonify({"error": "No query provided"}), 400

    results = search(query, top_k)

    threshold = 0.3
    confident = any(res['similarity'] > threshold for res in results)

    if not confident:
        return jsonify({"answer": None, "contexts": [], "reranker_used": False})

    contexts = []
    best_answer = None
    best_similarity = -1

    for res in results:
        answer, similarity, citation = extract_answer_with_citation(query, res)
        contexts.append({
            "answer": answer,
            "similarity": similarity,
            "citation": citation
        })
        if similarity > best_similarity:
            best_similarity = similarity
            best_answer = answer

    return jsonify({
        "answer": best_answer,
        "contexts": contexts,
        "reranker_used": False
    })

if __name__ == "__main__":
    app.run(debug=True)
