import time
import torch

# Check for NVIDIA GPU (CUDA), Apple Silicon (MPS), or fallback to CPU
device = torch.device(
    "cuda" if torch.cuda.is_available() 
    else "mps" if torch.backends.mps.is_available() 
    else "cpu"
)

print(f"Using device: {device}")
from sentence_transformers import CrossEncoder

# 1. Load model (good default)
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
model.to(device)

def rerank(query, documents, top_k=None):
    """
    query: str
    documents: list of dicts OR list of strings
    top_k: optional cutoff
    """

    # Extract text field if documents are dicts
    if isinstance(documents[0], dict):
        texts = [(doc["title"]+'\n'+doc['meta_description']+"\n"+doc['html']) for doc in documents]
    else:
        texts = documents

    # 2. Create (query, doc) pairs
    pairs = [(query, doc) for doc in texts]

    # 3. Score
    scores = model.predict(pairs)

    # 4. Attach scores
    if isinstance(documents[0], dict):
        for doc, score in zip(documents, scores):
            doc["cross_score"] = float(score)
        ranked = sorted(documents, key=lambda x: x["cross_score"], reverse=True)
    else:
        ranked = sorted(zip(texts, scores), key=lambda x: x[1], reverse=True)

    # 5. Optional cutoff
    if top_k:
        ranked = ranked[:top_k]

    return ranked

# query = "best anime with overpowered protagonist"

# docs = [
#     {"id": 1, "text": "One Punch Man is about a hero who defeats enemies in one punch."},
#     {"id": 2, "text": "A romantic slice of life anime set in high school."},
#     {"id": 3, "text": "Overlord features a powerful main character trapped in a game world."}
# ]

# start = time.time_ns()
# results = rerank(query, docs, top_k=3)
# print(f'Results in {time.time_ns() - start} ns')
# for r in results:
#     print(r["cross_score"], r["text"])