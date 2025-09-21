from flask import Flask, request, jsonify
from reader import search
from reranker import hybrid_reranker
from baseline import baseline
app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("q")
    top_k = data.get("k",3)
    mode = data.get("mode", "baseline")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    results = search(query, top_k)

    threshold = 0.3
    confident = any(res['similarity'] > threshold for res in results)

    if not confident:
        return jsonify({"answer": None, "contexts": [], "reranker_used": False})
    if(mode=="baseline"):
        return baseline(query, results)
    else:
        best_sentence, best_score, citation = hybrid_reranker(query, results)
        response = {
            "answer": best_sentence,
            "contexts": [{
                "answer": best_sentence,
                "similarity": best_score,
                "citation": citation
            }],
            "reranker_used": True
        }
        return jsonify(response)
if __name__ == "__main__":
    app.run(debug=True)
