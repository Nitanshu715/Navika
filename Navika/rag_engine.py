# finance_ai/rag_engine.py
#
# IMPORTANT: No google, genai, or sentence_transformers imports at the top level.
# All are loaded lazily inside functions to avoid startup crashes.

import os
import json
import sqlite3
import numpy as np
import faiss
from dotenv import load_dotenv

load_dotenv()

def _get_api_key():
    return os.getenv("GEMINI_API_KEY", "")

# ─────────────────────────────────────────────────────────────────────────────
# Lazy Gemini client
# We try google.generativeai first (installed as google-generativeai, very common).
# If that fails we try google.genai (newer google-genai package).
# Either way it's done inside a function so it never runs at import time.
# ─────────────────────────────────────────────────────────────────────────────
_gemini_client = None
_gemini_style  = None   # "old" or "new"

def _get_gemini():
    global _gemini_client, _gemini_style
    if _gemini_client is not None:
        return _gemini_client, _gemini_style

    api_key = _get_api_key()
    # Try the stable google-generativeai package first
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_client = genai
        _gemini_style  = "old"
        print("[rag_engine] Using google-generativeai SDK")
        return _gemini_client, _gemini_style
    except Exception:
        pass

    # Fall back to newer google-genai package
    try:
        from google import genai as _genai
        _gemini_client = _genai.Client(api_key=api_key)
        _gemini_style  = "new"
        print("[rag_engine] Using google-genai SDK")
        return _gemini_client, _gemini_style
    except Exception as e:
        raise ImportError(
            f"Cannot import Gemini SDK.\n"
            f"Run ONE of these:\n"
            f"  pip install google-generativeai\n"
            f"  pip install google-genai\n"
            f"Original error: {e}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Ultra-Fast ONNX Embedder (fastembed: ~3-5ms CPU latency, zero PyTorch overhead)
# ─────────────────────────────────────────────────────────────────────────────
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        print("[rag_engine] Initializing lightweight ONNX embedding model (fastembed)...")
        from fastembed import TextEmbedding
        # BAAI/bge-small-en-v1.5 or sentence-transformers/all-MiniLM-L6-v2 ONNX (384-dimensional)
        _embedder = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print("[rag_engine] ONNX Embedding model ready.")
    return _embedder


def _encode_texts(texts: list) -> np.ndarray:
    embedder = _get_embedder()
    # fastembed.embed returns an iterator of numpy arrays
    embeddings = list(embedder.embed(texts))
    return np.array(embeddings, dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# SQLite (finance.db) — transactions only, separate from users.db
# ─────────────────────────────────────────────────────────────────────────────
_here    = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_here, "..", "finance.db")

conn   = sqlite3.connect(_DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER DEFAULT 1,
        merchant  TEXT,
        category  TEXT,
        amount    REAL,
        timestamp TEXT
    )
""")
try:
    cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER DEFAULT 1")
    conn.commit()
except Exception:
    pass
conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# FAISS index
# ─────────────────────────────────────────────────────────────────────────────
DIMENSION      = 384
faiss_index    = faiss.IndexFlatL2(DIMENSION)
metadata_store = []   # list of (id, merchant, category, amount, timestamp, user_id)


def index_existing_transactions(user_id: int = None):
    global metadata_store
    if faiss_index.ntotal > 0:
        return
    if user_id:
        cursor.execute("SELECT id, merchant, category, amount, timestamp, user_id FROM transactions WHERE user_id = ? OR user_id IS NULL", (user_id,))
    else:
        cursor.execute("SELECT id, merchant, category, amount, timestamp, user_id FROM transactions")
    rows = cursor.fetchall()
    if not rows:
        return
    texts = [f"{r[4]} | {r[1]} | {r[2]} | ₹{r[3]}" for r in rows]
    emb   = _encode_texts(texts)
    faiss_index.add(emb)
    metadata_store = list(rows)


def add_transaction_to_rag(merchant, category, amount, timestamp, user_id: int = 1):
    cursor.execute(
        "INSERT INTO transactions (merchant, category, amount, timestamp, user_id) VALUES (?,?,?,?,?)",
        (merchant, category, amount, timestamp, user_id),
    )
    conn.commit()
    tx_id = cursor.lastrowid
    text  = f"{timestamp} | {merchant} | {category} | ₹{amount}"
    emb   = _encode_texts([text])
    faiss_index.add(emb)
    metadata_store.append((tx_id, merchant, category, amount, timestamp, user_id))


def retrieve_similar(query, k=5):
    if faiss_index.ntotal == 0:
        return []
    q_emb = _encode_texts([query])
    _, indices = faiss_index.search(q_emb, k)
    results = []
    for idx in indices[0]:
        if 0 <= idx < len(metadata_store):
            r = metadata_store[idx]
            results.append(f"{r[4]} | {r[1]} | {r[2]} | ₹{r[3]}")
    return results


def compute_stats(user_id: int = None):
    if user_id:
        cursor.execute("SELECT merchant, category, amount FROM transactions WHERE user_id = ? OR user_id IS NULL", (user_id,))
    else:
        cursor.execute("SELECT merchant, category, amount FROM transactions")
    rows = cursor.fetchall()
    if not rows:
        return {}
    total     = sum(r[2] for r in rows)
    avg       = total / len(rows)
    highest   = max(rows, key=lambda x: x[2])
    cat_totals = {}
    for r in rows:
        cat_totals[r[1]] = cat_totals.get(r[1], 0) + r[2]
    return {
        "total_spent":   round(total, 2),
        "average_spent": round(avg, 2),
        "highest_transaction": {"merchant": highest[0], "category": highest[1], "amount": highest[2]},
        "category_totals": cat_totals,
    }


def _call_gemini(prompt: str) -> str:
    """Call Gemini using whichever SDK is installed."""
    client, style = _get_gemini()
    if style == "old":
        # google-generativeai style
        model    = client.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    else:
        # google-genai style
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"temperature": 0.2, "top_p": 0.8},
        )
        return response.text


def rag_answer(query):
    index_existing_transactions()
    similar = retrieve_similar(query)
    stats   = compute_stats()

    if not stats:
        return {
            "risk_level":          "Unknown",
            "main_issue":          "No transaction data yet. Add some transactions first.",
            "key_observations":    [],
            "recommended_actions": [],
        }

    context = "\n".join(similar) if similar else "No similar transactions found."
    prompt  = f"""You are a financial risk analysis system.

RULES: Only use the data below. Never invent numbers. Be concise.

Transactions:
{context}

Stats:
- Total Spent: ₹{stats["total_spent"]}
- Average: ₹{stats["average_spent"]}
- By Category: {stats["category_totals"]}

Question: {query}

Reply ONLY with valid JSON, no markdown:
{{
  "risk_level": "Low | Medium | High",
  "main_issue": "one sentence",
  "key_observations": ["...", "...", "..."],
  "recommended_actions": ["...", "...", "..."]
}}"""

    try:
        raw   = _call_gemini(prompt).strip()
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        return {
            "risk_level":          "Unknown",
            "main_issue":          f"Analysis error: {e}",
            "key_observations":    [],
            "recommended_actions": [],
        }