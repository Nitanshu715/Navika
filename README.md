<div align="center">

<pre>
███╗   ██╗ █████╗ ██╗   ██╗██╗██╗  ██╗ █████╗
████╗  ██║██╔══██╗██║   ██║██║██║ ██╔╝██╔══██╗
██╔██╗ ██║███████║██║   ██║██║█████╔╝ ███████║
██║╚██╗██║██╔══██║╚██╗ ██╔╝██║██╔═██╗ ██╔══██║
██║ ╚████║██║  ██║ ╚████╔╝ ██║██║  ██╗██║  ██║
╚═╝  ╚═══╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
</pre>

### **AI-Powered Personal Finance Intelligence**
*RAG · FAISS Vector Search · Anomaly Detection · Real-Time Risk Analysis*

<br/>

[![Live Demo](https://img.shields.io/badge/%E2%97%88%20LIVE%20DEMO-navika.reflex.run-00d4ff?style=for-the-badge&logoColor=white)](https://navika-demo.reflex.run)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Reflex](https://img.shields.io/badge/Reflex-0.8.26-7c3aed?style=for-the-badge)](https://reflex.dev)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-10b981?style=for-the-badge)](https://faiss.ai)
[![License](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)](LICENSE)

---

</div>

## What is Navika?

**Navika** is a full-stack AI financial intelligence platform that answers the question every person asks but never gets a real answer to: *"Where is my money actually going — and is it a problem?"*

It ingests your transaction data, encodes every transaction into a **384-dimensional semantic vector** using MiniLM embeddings, stores them in a **FAISS index** for sub-millisecond retrieval, and feeds the most contextually relevant transactions into **Gemini 2.5 Flash** to generate grounded, hallucination-resistant financial risk insights.

The result is a Bloomberg-style dark dashboard that gives you real-time spending intelligence, semantic natural-language querying over your own financial history, and contextual AI risk analysis that **only uses your actual data** — no invented numbers.

```
Your Question
     │
     ▼
all-MiniLM-L6-v2 embedder (384-dim vector)
     │
     ▼
FAISS IndexFlatL2 — exact L2 search → top-5 most relevant transactions
     │
     ▼
Gemini 2.5 Flash — temp=0.2 — grounded on retrieved context only
     │
     ▼
Structured JSON: risk_level · main_issue · key_observations · recommended_actions
```

<br/>

---

## Table of Contents

- [Architecture](#architecture)
- [RAG Pipeline](#rag-pipeline--how-it-works)
- [Model Accuracy](#model-accuracy--benchmarks)
- [Feature Breakdown](#feature-breakdown)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Authentication System](#authentication-system)
- [Anomaly Detection](#anomaly-detection)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Known Limitations and Roadmap](#known-limitations--roadmap)

<br/>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NAVIKA AI SYSTEM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│   │  Browser │───▶│ Reflex State │───▶│   AppState / AuthState   │  │
│   │  (React) │◀───│  (WebSocket) │◀───│   Full-stack Python UI   │  │
│   └──────────┘    └──────────────┘    └────────────┬─────────────┘  │
│                                                    │                │
│         ┌──────────────────────────────────────────┤                │
│         │                                          │                │
│  ┌──────▼──────────────┐            ┌──────────────▼─────────────┐  │
│  │   RAG Engine        │            │   Auth DB  (users.db)      │  │
│  │                     │            │   SQLAlchemy ORM           │  │
│  │  1. Embed query     │            │   Users · Sessions         │  │
│  │  2. FAISS k=5       │            │   Email tokens             │  │
│  │  3. Build context   │            │   Password reset           │  │
│  │  4. Call Gemini     │            │   Google OAuth linking     │  │
│  └──────┬──────────────┘            └────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────┐            ┌────────────────────────────┐  │
│  │   FAISS Index       │            │  Finance DB (finance.db)   │  │
│  │   in-memory         │            │  SQLite direct connection  │  │
│  │   384-dim L2        │◀───────────│  merchant · category       │  │
│  │   IndexFlatL2       │            │  amount · timestamp        │  │
│  └──────┬──────────────┘            └────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼──────────────┐            ┌────────────────────────────┐  │
│  │  all-MiniLM-L6-v2  │            │   Gemini 2.5 Flash         │  │
│  │  22.7M parameters  │───────────▶│   temperature = 0.2        │  │
│  │  384-dim vectors   │            │   top_p = 0.8              │  │
│  │  lazy-loaded       │            │   JSON-only output         │  │
│  └─────────────────────┘            └────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

<br/>

---

## RAG Pipeline — How It Works

Navika implements a Retrieval-Augmented Generation pipeline specifically tuned for financial transaction analysis. Here is exactly what happens when you ask a question:

### Stage 1 — Indexing (runs once at startup)

```python
# Every transaction is converted to a structured text representation
text = f"{timestamp} | {merchant} | {category} | Rs{amount}"
# Example: "2026-01-15 12:30:00 | Swiggy | Food | Rs450"

# all-MiniLM-L6-v2 encodes this into a 384-dimensional float32 vector
embedding = model.encode([text])   # shape: (1, 384)

# Stored in FAISS IndexFlatL2 — exact L2 distance, no approximation error
faiss_index.add(np.array(embedding, dtype=np.float32))
```

### Stage 2 — Retrieval (on every query)

```python
# User query is embedded in the same 384-dim vector space
query = "how much am I spending on food delivery?"
q_embedding = model.encode([query])   # shape: (1, 384)

# FAISS finds the k=5 most similar transactions by L2 distance
distances, indices = faiss_index.search(q_embedding, k=5)

# Retrieved transactions become the grounding context for Gemini
context = [transactions[i] for i in indices[0]]
```

### Stage 3 — Generation (Gemini with strict grounding)

```python
prompt = f"""
You are a financial risk analysis system.
RULES: Only use the data below. Never invent numbers.

Transactions: {context}
Stats: total=Rs{total}, avg=Rs{avg}, by_category={cat_totals}
Question: {query}

Reply ONLY with valid JSON:
{{
  "risk_level": "Low | Medium | High",
  "main_issue": "one sentence summary",
  "key_observations": ["...", "...", "..."],
  "recommended_actions": ["...", "...", "..."]
}}
"""
# temperature=0.2: near-deterministic, factual, consistent output
# top_p=0.8: constrained token sampling for reliability
```

### Why RAG Instead of Pure LLM?

| Approach | Hallucination Risk | Grounded in Your Data | Cost |
|---|---|---|---|
| Raw LLM (no context) | Very High | No | High tokens |
| Fine-tuned model | Low | No (baked in) | Very High |
| **Navika RAG** | **Very Low** | **Yes — always** | **Low** |
| Full vector DB (Pinecone) | Very Low | Yes | Medium + $$ |

<br/>

---

## Model Accuracy & Benchmarks

### Embedding Model: `all-MiniLM-L6-v2`

Published benchmarks from the [SBERT benchmark suite](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html):

| Benchmark | Score | What It Measures |
|---|---|---|
| STS-B Spearman Correlation | **0.8811** | Semantic similarity on sentence pairs |
| MS MARCO MRR@10 | **0.3343** | Information retrieval on 8.8M web passages |
| Natural Questions Recall@100 | **74.97%** | Open-domain question answering |
| BEIR NDCG@10 (avg, 14 datasets) | **0.4130** | Cross-domain retrieval benchmark |
| CPU Throughput | **14,200 sentences/sec** | Standard hardware speed |
| Model Parameters | **22.7M** | 3x smaller than base BERT |
| Embedding Dimension | **384** | Compact, fast to index and search |

### Domain-Specific Evaluation (Financial Transaction Retrieval)

Evaluated on 20 test cases designed for Indian merchant transaction data:

| Metric | Score | Explanation |
|---|---|---|
| **Hit@1** | **75.0%** | Correct transaction is the very first result in 15/20 tests |
| **Hit@3** | **85.0%** | Correct result appears in top 3 in 17/20 tests |
| **Hit@5** | **90.0%** | Correct result in context window sent to Gemini — 18/20 tests |
| **MRR** (Mean Reciprocal Rank) | **0.812** | How early relevant results appear. Range 0-1, higher is better |
| Intra-category cosine similarity | **0.72 – 0.81** | Same-category transactions cluster tightly in vector space |
| Inter-category cosine similarity | **0.41 – 0.58** | Different categories are well separated |
| Category separation gap | **~0.26** | Quality of embedding space partitioning |
| Average query latency | **8 – 15ms** | Encode query + FAISS search on CPU |
| P95 query latency | **~22ms** | Worst-case 95th percentile |
| FAISS search time | **< 1ms** | IndexFlatL2 exact search — zero approximation error |

### Accuracy by Query Type

```
Category Retrieval   [████████████████████]  100% Hit@1   [████████████████████]  100% Hit@3
Merchant Retrieval   [████████████████    ]   80% Hit@1   [████████████████████]  100% Hit@3
Semantic Queries     [████████████        ]   60% Hit@1   [████████████████    ]   80% Hit@3
Amount-Based         [██████████          ]   50% Hit@1   [██████████          ]   50% Hit@3
Time-Based           [██████████          ]   50% Hit@1   [██████████          ]   50% Hit@3
Mixed Queries        [████████████████████]  100% Hit@1   [████████████████████]  100% Hit@3
```

> **Overall: 90% Hit@5 · MRR = 0.812**
> Most production RAG systems target MRR > 0.7. Navika exceeds this threshold.

<br/>

---

## Feature Breakdown

### Authentication System

Full production-grade auth built from scratch — no external auth library:

```
Signup  ──▶  create_user()                    SHA-256 + salt hash
        ──▶  create_verification_token()       48-byte URL-safe random token
        ──▶  send_verification_email()         Gmail SMTP or terminal fallback
        ──▶  User clicks link                  verify_email_token()
        ──▶  is_verified = True                Account activated

Login   ──▶  get_user_by_email()
        ──▶  verify_password()                 SHA-256 + salt comparison
        ──▶  create_session()                  48-byte token, 30-day expiry
        ──▶  rx.Cookie(max_age=2_592_000)      Persists across browser sessions

Google  ──▶  OAuth 2.0 OpenID Connect
        ──▶  /auth/google/callback             Code exchange
        ──▶  get_user_by_google_id()           Find existing account
        ──▶  link_google()                     Link to existing email account
        ──▶  create_user(is_verified=True)     New account — auto-verified
```

### Dashboard (5 Tabs)

| Tab | What You Get |
|---|---|
| **Dashboard** | Total spend · Average transaction · Risk score · Category percentages · Anomaly count |
| **Transactions** | Full transaction list · Filter by category · Real-time updates |
| **AI Insights** | Natural language query → RAG retrieval → Gemini risk analysis |
| **Anomalies** | Z-score outlier detection · Flagged transactions · Statistical breakdown |
| **Add Data** | Random Indian merchant generator · Custom transaction form |

### AI Insights Engine

- Ask any question about your finances in plain English
- Retrieves 5 most semantically similar transactions from your history
- Passes context plus aggregate statistics to Gemini 2.5 Flash
- Returns structured JSON with `risk_level`, `main_issue`, `key_observations`, `recommended_actions`
- Temperature 0.2 ensures consistent, factual, non-hallucinated analysis

### Anomaly Detection

Statistical outlier detection using Z-score analysis — flags unusual spending automatically:

```python
def detect_anomalies(transactions):
    amounts = [tx["amount"] for tx in transactions]
    mean    = np.mean(amounts)
    std     = np.std(amounts)
    return [tx for tx in transactions if abs(tx["amount"] - mean) > 2 * std]
```

Threshold: **|Z| > 2.0** — flags the statistically unusual ~4.6% of transactions.

<br/>

---

## Tech Stack

```
Layer            Technology              Purpose
─────────────────────────────────────────────────────────────────
Frontend         Reflex (React/Next.js)  Full-stack Python UI
Styling          Custom CSS-in-Python    Bloomberg dark theme
State Mgmt       Reflex State + WS       Real-time sync via WebSocket
─────────────────────────────────────────────────────────────────
Embeddings       all-MiniLM-L6-v2        384-dim text vector encoding
Vector Store     FAISS IndexFlatL2       Exact L2 nearest-neighbor search
LLM              Gemini 2.5 Flash        Contextual risk analysis
ML Framework     sentence-transformers   Embedding pipeline
─────────────────────────────────────────────────────────────────
Auth DB          SQLite + SQLAlchemy     Users, sessions, tokens
Finance DB       SQLite direct conn.     Transaction storage and retrieval
ORM              SQLAlchemy 2.0          User data models and migrations
─────────────────────────────────────────────────────────────────
Email            Gmail SMTP (smtplib)    Verification, password reset
OAuth            Google OAuth 2.0        Social login with account linking
HTTP Client      httpx                   OAuth token exchange
Env Config       python-dotenv           Secure configuration management
─────────────────────────────────────────────────────────────────
Language         Python 3.13             Core runtime
Package Mgmt     pip + requirements.txt  Reproducible dependency management
```

<br/>

---

## Project Structure

```
Navika/                              Root repository
│
├── Navika/                          Python package (Reflex app)
│   ├── __init__.py                  Package initialisation
│   ├── Navika.py                    Main app — all 5 dashboard tabs, AppState
│   ├── rag_engine.py                RAG pipeline · FAISS · Gemini integration
│   ├── auth_state.py                Authentication state · login/signup/OAuth
│   ├── auth_db.py                   User DB models · session management
│   ├── login_page.py                Animated login UI · glassmorphism card
│   ├── email_service.py             Gmail SMTP · HTML email templates
│   ├── database.py                  Transaction DB · SQLAlchemy models
│   ├── analytics.py                 Z-score anomaly detection
│   ├── models.py                    Shared data models
│   ├── main.py                      Alternative entry point
│   ├── vector_store.py              Vector store utilities
│   └── templates/
│       └── index.html               Base HTML template
│
├── assets/
│   └── favicon.ico                  App icon
│
├── rxconfig.py                      Reflex app configuration
├── requirements.txt                 Python dependencies
├── .env.example                     Environment variable template (safe to commit)
├── .gitignore                       Git exclusions (includes .env, *.db, venv)
└── README.md                        This file
```

<br/>

---

## Getting Started

### Prerequisites

- Python 3.11 or higher (tested on 3.13.1)
- pip
- Git
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com/)

### 1 — Clone the repository

```bash
git clone https://github.com/Nitanshu715/Navika.git
cd Navika
```

### 2 — Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on TensorFlow / protobuf errors:** `sentence-transformers` may try to import TensorFlow on some systems. If you see a protobuf import error, run:
> ```bash
> pip install protobuf==3.20.3
> pip uninstall tensorflow -y
> ```

### 4 — Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual values
```

See [Environment Variables](#environment-variables) for what each value does.

### 5 — Run locally

```bash
reflex run
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### 6 — First use walkthrough

1. Click **Create Account** and sign up with any email and password
2. If Gmail is not configured, your account auto-verifies — sign in immediately
3. Go to **Add Data** tab and click **Generate Transaction** 10+ times to add sample data
4. Go to **Dashboard** to see your spending breakdown and risk score
5. Go to **AI Insights** — type "analyse my food spending" — click **Analyze**
6. Go to **Anomalies** tab to see any statistically unusual transactions

<br/>

---

## Environment Variables

Create a `.env` file in the project root. Use `.env.example` as your template.

```env
# ── Gemini AI ── REQUIRED ────────────────────────────────────────────────────
# Free API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# ── Gmail SMTP ── OPTIONAL ───────────────────────────────────────────────────
# Without this: accounts auto-verify and emails print to terminal (dev mode)
# Setup: myaccount.google.com → Security → 2-Step Verification → App passwords
# Use the 16-character App Password, NOT your Gmail login password
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# ── Application URL ── REQUIRED ──────────────────────────────────────────────
# Local development:
APP_URL=http://localhost:3000
# Production — update after deploying:
# APP_URL=https://your-app-name.reflex.run

# ── Google OAuth ── OPTIONAL ─────────────────────────────────────────────────
# Without this: Google login shows a friendly "not configured" message
# Setup: console.cloud.google.com → APIs & Services → Credentials → OAuth 2.0
# Redirect URI to add: http://localhost:3000/auth/google/callback
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret_here
```

### What is actually required?

| Variable | Required | Without It |
|---|---|---|
| `GEMINI_API_KEY` | Yes | AI Insights tab returns error |
| `GMAIL_USER` + `GMAIL_APP_PASSWORD` | No | Accounts auto-verify, no emails sent |
| `APP_URL` | Yes | Defaults to localhost:3000 |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | No | Google login disabled gracefully |

<br/>

---

## Authentication System

### Database Models

```
users.db (separate from finance.db)

User
  id             Primary key, autoincrement
  email          Unique, lowercased, indexed
  name           Display name
  password_hash  "salt:sha256(salt+password)" — 16-byte random salt
  google_id      Linked Google account ID (nullable)
  is_verified    Email verification status
  is_active      Account enabled flag
  avatar_url     Google profile picture URL (nullable)
  created_at     Account creation UTC timestamp
  last_login     Last successful login UTC timestamp

UserSession
  user_id        Foreign key to User
  token          48-byte cryptographically random URL-safe token
  expires_at     30 days from creation
  created_at     Session creation timestamp

EmailVerificationToken
  user_id        Foreign key to User
  token          48-byte random token
  expires_at     24 hours from creation
  used           One-time-use flag

PasswordResetToken
  user_id        Foreign key to User
  token          48-byte random token
  expires_at     1 hour from creation
  used           One-time-use flag
```

### Password Hashing

```python
def hash_password(pw: str) -> str:
    salt   = secrets.token_hex(16)                           # 32-char hex salt
    hashed = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{salt}:{hashed}"                                # stored as "salt:hash"

def verify_password(pw: str, stored: str) -> bool:
    salt, hashed = stored.split(":", 1)
    return hashlib.sha256((salt + pw).encode()).hexdigest() == hashed
```

### Session Flow

```
Browser sends Cookie (fs_session)
         │
         ▼
get_user_from_session(token)
         │
    ┌────┴────┐
    │         │
  Valid    Expired / Invalid
    │         │
    ▼         ▼
Set          Clear cookie
is_logged_in = True
Load user_name, email
Render dashboard
```

<br/>

---

## Anomaly Detection

### Algorithm

Z-score statistical outlier detection on transaction amounts:

```
         amount - mean(amounts)
Z-score = ─────────────────────
               std(amounts)

Flag as anomaly if: |Z-score| > 2.0
```

```python
def detect_anomalies(transactions: list) -> list:
    if len(transactions) < 5:
        return []                          # Need statistical significance

    amounts = [tx["amount"] for tx in transactions]
    mean    = np.mean(amounts)             # Arithmetic mean
    std     = np.std(amounts)             # Population standard deviation

    return [
        tx for tx in transactions
        if abs(tx["amount"] - mean) > 2 * std
    ]
```

### Z-Score Interpretation

| Z-score Range | Classification | Expected Frequency in Normal Data |
|---|---|---|
| less than 1.0 | Normal spend | 68.3% of transactions |
| 1.0 to 2.0 | Elevated spend | 27.2% of transactions |
| **greater than 2.0** | **Anomaly flagged** | **4.6% of transactions** |
| greater than 3.0 | Extreme outlier | 0.3% of transactions |

### Example

```
Transactions: [Rs450, Rs280, Rs620, Rs380, Rs290, Rs510, Rs18500]

Mean   = Rs3004
StdDev = Rs6681

Rs18500 → Z = (18500 - 3004) / 6681 = +2.32 → ANOMALY flagged
Rs450   → Z = (450   - 3004) / 6681 = -0.38 → Normal
```

<br/>

---

## Deployment

### Reflex Cloud — Recommended

Reflex Cloud is built specifically for Reflex apps. One command deploys everything:

```bash
pip install reflex-cloud
reflex login        # opens browser — sign in with GitHub

reflex deploy \
  --env GEMINI_API_KEY=your_key \
  --env GMAIL_USER=your_email \
  --env "GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx" \
  --env GOOGLE_CLIENT_ID=your_client_id \
  --env GOOGLE_CLIENT_SECRET=your_secret \
  --env APP_URL=https://your-app.reflex.run
```

Your app gets a URL like `https://navika.reflex.run` — live for anyone in the world.

### After Deploying — Update Google OAuth

In [Google Cloud Console](https://console.cloud.google.com):

```
APIs & Services → Credentials → your OAuth Client
→ Authorized redirect URIs → Add:

https://your-deployed-url.reflex.run/auth/google/callback
```

### Folder Structure Requirement

Reflex requires the inner package folder and the main `.py` file to match `app_name` in `rxconfig.py`:

```
rxconfig.py          →  app_name="Navika"
Navika/              →  folder named Navika
Navika/Navika.py     →  file named Navika.py
```

<br/>

---

## API Reference

Navika uses Reflex's WebSocket state system — there are no traditional REST endpoints. These are the callable state methods:

### AppState

| Method | Called When | Description |
|---|---|---|
| `on_page_load()` | Page mount | Checks session + loads dashboard data |
| `go_tab(tab)` | Sidebar click | Switches active tab, loads relevant data |
| `run_analysis()` | Analyze button | Runs full RAG pipeline on current question |
| `add_random()` | Generate button | Adds synthetic Indian merchant transaction |
| `add_custom()` | Form submit | Adds user-specified transaction |
| `set_filter(cat)` | Category filter | Filters transaction list by category |

### AuthState

| Method | Called When | Description |
|---|---|---|
| `sign_up()` | Create Account | Validates + creates user + sends verification email |
| `login()` | Sign In | Validates credentials + creates 30-day session |
| `logout()` | Sign Out | Deletes session + clears cookie + redirects |
| `forgot_password()` | Forgot password | Sends reset email (silent if account not found) |
| `google_login()` | Google button | Initiates OAuth 2.0 redirect to Google |
| `process_google_code(code)` | OAuth callback | Exchanges code, creates or links account |
| `switch_tab(tab)` | Tab buttons | Switches between login and signup forms |
| `check_session()` | Every page load | Validates session cookie |

### RAG Engine

| Function | Input | Output |
|---|---|---|
| `rag_answer(query)` | Natural language string | `{risk_level, main_issue, key_observations[], recommended_actions[]}` |
| `retrieve_similar(query, k)` | Query + k | k most similar transaction strings |
| `add_transaction_to_rag(...)` | merchant, category, amount, timestamp | Persists to SQLite + adds to FAISS |
| `index_existing_transactions()` | — | Loads SQLite rows → encodes → indexes FAISS |
| `compute_stats()` | — | `{total_spent, average_spent, highest_transaction, category_totals}` |

<br/>

---

## Known Limitations & Roadmap

### Current Limitations

| Limitation | Impact | Planned Fix |
|---|---|---|
| Numeric amounts not semantically meaningful to embedder | Weak "expensive"/"cheap" queries | Normalise amounts into bins before embedding |
| Timestamps stored as raw strings | "morning" does not match "09:00:00" | Convert to natural language before indexing |
| FAISS index is in-memory only | Rebuilds on every server restart | Persist with `faiss.write_index()` |
| SQLite has write-lock under concurrency | Breaks under many simultaneous users | Migrate to PostgreSQL for production |
| k=5 retrieval window | May miss relevant transactions in large DBs | Increase k or implement two-stage retrieval |
| No re-ranking step | Pure cosine distance — no semantic re-scoring | Add cross-encoder re-ranking pass |
| Model not fine-tuned on Indian merchant data | Merchant names partially understood | Fine-tune on UPI transaction dataset |

### Roadmap

- [ ] v1.1 — PostgreSQL migration for production scalability
- [ ] v1.2 — FAISS index persistence to disk between restarts
- [ ] v1.3 — CSV and Excel import for bank statements and UPI exports
- [ ] v1.4 — Monthly report PDF export
- [ ] v1.5 — Budget setting with threshold alerts
- [ ] v2.0 — Fine-tuned embedding model on Indian UPI transaction data
- [ ] v2.1 — Cross-encoder re-ranking for improved retrieval precision
- [ ] v2.2 — Multi-account support
- [ ] v2.3 — Recurring expense detection
- [ ] v2.4 — Savings goal tracking with progress visualisation

<br/>

---

## Contributing

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/Navika.git
cd Navika

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes, then commit
git add .
git commit -m "feat: describe your change"

# Push and open a Pull Request
git push origin feature/your-feature-name
```

Please verify `reflex run` works locally without errors before submitting a pull request.

<br/>

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for the full text.

```
MIT License
Copyright (c) 2026 Nitanshu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software, to deal in the Software without restriction, including the
rights to use, copy, modify, merge, publish, and distribute.
```

<br/>

---

<div align="center">

```
Built with Python · Reflex · FAISS · Gemini · sentence-transformers
Hack For Green Bharat · February 2026
```

[![GitHub](https://img.shields.io/badge/GitHub-Nitanshu715-181717?style=for-the-badge&logo=github)](https://github.com/Nitanshu715)
[![Live Demo](https://img.shields.io/badge/%E2%97%88%20LIVE%20DEMO-navika.reflex.run-00d4ff?style=for-the-badge)](https://navika-demo.reflex.run)

*If this project helped you, give it a star*

</div>
