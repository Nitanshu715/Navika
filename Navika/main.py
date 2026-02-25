from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from rag_engine import rag_answer, add_transaction_to_rag
from database import save_transaction, get_all_transactions
from datetime import datetime
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    transactions = get_all_transactions()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "transactions": transactions, "answer": ""}
    )

@app.post("/add")
def add():
    merchants = {
        "Swiggy": "Food",
        "Zomato": "Food",
        "Uber": "Transport",
        "Amazon": "Shopping",
        "Netflix": "Entertainment",
    }

    merchant = random.choice(list(merchants.keys()))
    category = merchants[merchant]

    tx = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "merchant": merchant,
        "category": category,
        "amount": round(random.uniform(200, 1500), 2),
    }

    save_transaction(tx)
    add_transaction_to_rag(tx)

    return {"status": "added"}

@app.post("/ask", response_class=HTMLResponse)
def ask(request: Request, question: str = Form(...)):
    answer = rag_answer(question)
    transactions = get_all_transactions()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "transactions": transactions, "answer": answer}
    )