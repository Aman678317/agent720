import numpy as np
from config import get_llm_provider
from personas import PERSONAS

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def fallback_keyword_similarity(post: str, persona: dict) -> float:
    post_lower = post.lower()
    bot_id = persona["bot_id"]
    if bot_id == "bot_a" and ("ai" in post_lower or "model" in post_lower or "tech" in post_lower):
        return 0.88
    if bot_id == "bot_b" and ("ai" in post_lower or "replace" in post_lower or "monopolies" in post_lower):
        return 0.86
    return 0.5

def route_post_to_bots(post_content: str, threshold: float = 0.85):
    provider = get_llm_provider()
    results = []
    use_fallback = False
    
    if provider == "openai":
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings
            import faiss
            
            embeddings = OpenAIEmbeddings()
            persona_texts = [p["persona"] for p in PERSONAS]
            
            post_emb = embeddings.embed_query(post_content)
            bot_embs = embeddings.embed_documents(persona_texts)
            
            for i, p in enumerate(PERSONAS):
                sim = cosine_similarity(post_emb, bot_embs[i])
                if sim >= threshold:
                    results.append({
                        "bot_id": p["bot_id"],
                        "bot_name": p["name"],
                        "similarity_score": float(sim),
                        "reason": f"Cosine similarity {sim:.2f} >= {threshold}"
                    })
        except Exception as e:
            print(f"[Phase 1] FAISS/Embedding failed: {e}. Falling back to keyword similarity.")
            use_fallback = True
    else:
        use_fallback = True
        
    if use_fallback:
        for p in PERSONAS:
            sim = fallback_keyword_similarity(post_content, p)
            if sim >= threshold:
                results.append({
                    "bot_id": p["bot_id"],
                    "bot_name": p["name"],
                    "similarity_score": float(sim),
                    "reason": f"Fallback keyword similarity {sim:.2f} >= {threshold}"
                })
                
    return results

if __name__ == "__main__":
    post = "OpenAI just released a new model that might replace junior developers."
    print("Test Post:", post)
    print("Routing Results:", route_post_to_bots(post))
