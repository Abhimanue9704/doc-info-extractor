from sentence_extractor import extract_answer_with_citation
from flask import jsonify

def baseline(query,results):
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