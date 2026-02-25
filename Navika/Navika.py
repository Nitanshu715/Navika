# finance_ai/finance_ai.py
import reflex as rx
import random
from datetime import datetime
from typing import List, Dict, Any

from .database import get_all_transactions
from .analytics import detect_anomalies
from .auth_state import AuthState
from .login_page import login_page, verified_page

BG    = "#060a14"
CARD  = "#0b1120"
BDR   = "#1a2f50"
CYAN  = "#00d4ff"
PURP  = "#7c3aed"
GREEN = "#10b981"
RED   = "#ef4444"
AMBER = "#f59e0b"
TEXT  = "#e2e8f0"
MUTED = "#4a6080"
MONO  = "'Courier New', monospace"
CS    = {"border": f"1px solid {BDR}", "border-radius": "14px"}
IS    = {"border": f"1px solid {BDR}"}


class AppState(rx.State):
    active_tab: str = "dashboard"

    total_spent: float = 0.0
    avg_spent: float = 0.0
    tx_count: int = 0
    top_category: str = ""
    risk_score: str = "Low"
    food_pct: float = 0.0
    shopping_pct: float = 0.0
    transport_pct: float = 0.0
    entertainment_pct: float = 0.0
    anomaly_count: int = 0
    has_data: bool = False

    transactions: List[Dict[str, Any]] = []
    filtered_transactions: List[Dict[str, Any]] = []
    filter_category: str = "All"
    anomalies: List[Dict[str, Any]] = []

    question: str = ""
    risk_level: str = ""
    main_issue: str = ""
    key_observations: List[str] = []
    recommended_actions: List[str] = []
    retrieved_context: List[str] = []
    is_loading: bool = False
    analysis_error: str = ""

    custom_merchant: str = ""
    custom_category: str = "Food"
    custom_amount: str = ""
    add_status: str = ""
    add_ok: bool = True

    def load_transactions(self): self._load_tx()
    def load_anomalies(self):    self._load_anomalies()

    def go_tab(self, tab: str):
        self.active_tab = tab
        if tab == "dashboard":      self._refresh()
        elif tab == "transactions": self._load_tx()
        elif tab == "anomalies":    self._load_anomalies()

    def _refresh(self):
        from .rag_engine import compute_stats
        txs = get_all_transactions()
        self.tx_count = len(txs); self.has_data = self.tx_count > 0
        self.transactions = txs
        stats = compute_stats()
        if stats and self.has_data:
            self.total_spent = round(stats.get("total_spent", 0), 2)
            self.avg_spent   = round(stats.get("average_spent", 0), 2)
            cat   = stats.get("category_totals", {})
            total = self.total_spent or 1
            self.food_pct          = round(cat.get("Food", 0)          / total * 100, 1)
            self.shopping_pct      = round(cat.get("Shopping", 0)      / total * 100, 1)
            self.transport_pct     = round(cat.get("Transport", 0)     / total * 100, 1)
            self.entertainment_pct = round(cat.get("Entertainment", 0) / total * 100, 1)
            self.top_category      = max(cat, key=cat.get) if cat else ""
        self.risk_score = (
            "High"   if self.total_spent > 20000 else
            "Medium" if self.total_spent > 8000  else "Low"
        )
        self.anomaly_count = len(detect_anomalies(txs))

    def _load_tx(self):
        self.transactions = get_all_transactions()
        self.filtered_transactions = (
            self.transactions if self.filter_category == "All"
            else [t for t in self.transactions if t["category"] == self.filter_category]
        )

    def _load_anomalies(self):
        self.anomalies = detect_anomalies(get_all_transactions())

    def on_page_load(self):
        from .rag_engine import index_existing_transactions
        index_existing_transactions()
        self._refresh()

    def set_filter(self, cat: str):
        self.filter_category = cat; self._load_tx()

    def set_question(self, v: str):        self.question        = v
    def set_custom_merchant(self, v: str): self.custom_merchant = v
    def set_custom_category(self, v: str): self.custom_category = v
    def set_custom_amount(self, v: str):   self.custom_amount   = v

    def add_random(self):
        pool = {
            "Swiggy":"Food","Zomato":"Food","BigBasket":"Food",
            "Uber":"Transport","Ola":"Transport",
            "Amazon":"Shopping","Flipkart":"Shopping","Myntra":"Shopping",
            "Netflix":"Entertainment","Spotify":"Entertainment",
            "Apollo":"Healthcare","PharmEasy":"Healthcare",
        }
        m = random.choice(list(pool.keys()))
        a = round(random.uniform(100, 2000), 2)
        from .rag_engine import add_transaction_to_rag
        add_transaction_to_rag(m, pool[m], a, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.add_status = f"✓  {m}  ₹{a}"; self.add_ok = True
        self._refresh()

    def add_custom(self):
        if not self.custom_merchant.strip() or not self.custom_amount.strip():
            self.add_status = "✗  Merchant and amount required"; self.add_ok = False; return
        try:
            a = float(self.custom_amount); assert a > 0
        except Exception:
            self.add_status = "✗  Enter a valid positive amount"; self.add_ok = False; return
        from .rag_engine import add_transaction_to_rag
        add_transaction_to_rag(
            self.custom_merchant.strip(), self.custom_category,
            round(a, 2), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.add_status = f"✓  {self.custom_merchant}  ₹{a}"; self.add_ok = True
        self.custom_merchant = ""; self.custom_amount = ""; self._refresh()

    def run_analysis(self):
        if not self.question.strip(): return
        self.is_loading = True; self.analysis_error = ""; self.risk_level = ""
        self.main_issue = ""; self.key_observations = []
        self.recommended_actions = []; self.retrieved_context = []
        yield
        try:
            from .rag_engine import rag_answer, retrieve_similar
            ctx = retrieve_similar(self.question, k=5)
            self.retrieved_context   = [c for c in ctx if c.strip()]
            result = rag_answer(self.question)
            self.risk_level          = result.get("risk_level", "Unknown")
            self.main_issue          = result.get("main_issue", "No analysis available")
            self.key_observations    = result.get("key_observations", [])
            self.recommended_actions = result.get("recommended_actions", [])
        except Exception as e:
            self.analysis_error = f"Analysis failed: {str(e)}"
        finally:
            self.is_loading = False


# ── UI helpers ────────────────────────────────────────────────────────────────

def card(*children, xs: dict = None, padding: str = "24px", **kwargs):
    s = {**CS, "background": CARD, "padding": padding}
    if xs: s.update(xs)
    return rx.box(*children, style=s, **kwargs)

def risk_badge(level):
    return rx.cond(
        level == "High",
        rx.box(rx.text(level, font_size="11px", font_weight="800", color=RED, letter_spacing="0.08em"),
               padding="3px 11px", background="#1c0505", border_radius="5px",
               style={"border": f"1px solid {RED}66"}),
        rx.cond(level == "Medium",
            rx.box(rx.text(level, font_size="11px", font_weight="800", color=AMBER, letter_spacing="0.08em"),
                   padding="3px 11px", background="#190f00", border_radius="5px",
                   style={"border": f"1px solid {AMBER}66"}),
            rx.box(rx.text(level, font_size="11px", font_weight="800", color=GREEN, letter_spacing="0.08em"),
                   padding="3px 11px", background="#041410", border_radius="5px",
                   style={"border": f"1px solid {GREEN}66"}),
        ),
    )

def pbar(label, pct, color, icon=""):
    txt = f"{icon} {label}" if icon else label
    return rx.vstack(
        rx.hstack(
            rx.text(txt, font_size="13px", color=TEXT, font_weight="500"),
            rx.spacer(),
            rx.text(pct.to_string() + "%", font_size="12px", color=color, font_weight="700", font_family=MONO),
            width="100%", align="center",
        ),
        rx.box(
            rx.box(height="7px", width=pct.to_string() + "%", background=color,
                   border_radius="4px", transition="width 0.8s ease"),
            width="100%", height="7px", background="#0d1e36", border_radius="4px",
        ),
        spacing="2", width="100%",
    )

def stat_card(label, value, prefix, color):
    return card(
        rx.vstack(
            rx.text(label, font_size="10px", font_weight="700", color=MUTED,
                    letter_spacing="0.13em", text_transform="uppercase"),
            rx.hstack(
                rx.text(prefix, font_size="14px", color=color, font_weight="700",
                        align_self="flex-end", padding_bottom="3px"),
                rx.text(value, font_size="28px", font_weight="900", color=TEXT,
                        font_family=MONO, letter_spacing="-0.02em"),
                spacing="1", align="end",
            ),
            spacing="2", align_items="start",
        ),
        min_width="155px", flex="1",
    )

def cat_pill(cat):
    M = {"Food":(AMBER,"#160e00"),"Shopping":(PURP,"#100818"),
         "Transport":(CYAN,"#001318"),"Entertainment":("#ec4899","#160010"),
         "Healthcare":(GREEN,"#031310")}
    clr, bg = M.get(cat, (MUTED, "#0d141e"))
    return rx.box(
        rx.text(cat, font_size="10px", font_weight="700", color=clr, letter_spacing="0.06em"),
        padding="3px 10px", background=bg, border_radius="4px", display="inline-block",
    )

def sh(title, sub=""):
    return rx.vstack(
        rx.text(title, font_size="19px", font_weight="800", color=TEXT),
        rx.cond(sub != "", rx.text(sub, font_size="12px", color=MUTED), rx.box(height="0")),
        spacing="1", margin_bottom="18px", align_items="start",
    )

def inp(placeholder, on_change, value, **kw):
    return rx.input(
        placeholder=placeholder, on_change=on_change, value=value,
        background=BG, border_radius="8px", padding="10px 14px",
        font_size="13px", color=TEXT, style=IS, _placeholder={"color": MUTED}, **kw,
    )

def empty_state(msg="No data yet"):
    return rx.box(
        rx.vstack(
            rx.text("◎", font_size="36px", color=MUTED, text_align="center"),
            rx.text(msg, font_size="14px", color=MUTED, text_align="center", font_weight="600"),
            rx.text("Go to Add Data to stream transactions into the engine",
                    font_size="12px", color=MUTED, text_align="center"),
            rx.button("→ Add Transactions", on_click=AppState.go_tab("add"),
                      background=PURP, color="white", border_radius="8px",
                      padding="8px 20px", font_size="13px", cursor="pointer",
                      _hover={"background": "#6d28d9"}),
            spacing="3", align="center", padding="50px", width="100%",
        ),
        width="100%",
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def nbtn(label, tab, icon):
    return rx.button(
        rx.hstack(rx.text(icon, font_size="14px"),
                  rx.text(label, font_size="13px", font_weight="600"),
                  spacing="3", align="center"),
        on_click=AppState.go_tab(tab),
        background=rx.cond(AppState.active_tab == tab, "#08183a", "transparent"),
        color=rx.cond(AppState.active_tab == tab, CYAN, MUTED),
        border_radius="9px", padding="10px 14px", width="100%",
        cursor="pointer", transition="all 0.15s",
        style={"border": rx.cond(AppState.active_tab == tab,
                                 f"1px solid {BDR}", "1px solid transparent"),
               "text-align": "left"},
        _hover={"background": "#08183a", "color": TEXT},
    )

def sidebar():
    return rx.box(
        rx.vstack(
            rx.box(
                rx.hstack(
                    rx.text("◈", font_size="20px", color=CYAN),
                    rx.vstack(
                        rx.text("Navika", font_size="16px", font_weight="900",
                                color=TEXT, letter_spacing="0.2em", font_family=MONO),
                        rx.text("AI · INTELLIGENCE · OS", font_size="8px",
                                color=MUTED, letter_spacing="0.18em"),
                        spacing="0",
                    ),
                    spacing="3", align="center",
                ),
                padding="24px 18px 22px",
                style={"border-bottom": f"1px solid {BDR}"},
                width="100%",
            ),
            rx.vstack(
                nbtn("Dashboard",    "dashboard",    "◎"),
                nbtn("Transactions", "transactions", "⊞"),
                nbtn("AI Insights",  "insights",     "◈"),
                nbtn("Anomalies",    "anomalies",    "⚠"),
                nbtn("Add Data",     "add",          "⊕"),
                spacing="2", padding="14px 12px", width="100%",
            ),
            rx.spacer(),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(width="7px", height="7px", background=GREEN, border_radius="50%"),
                        rx.text("Engine Online", font_size="11px", color=GREEN, font_weight="600"),
                        spacing="2", align="center",
                    ),
                    rx.text("FAISS · SQLite · Gemini", font_size="9px", color=MUTED, letter_spacing="0.1em"),
                    rx.text("MiniLM-L6-v2 Embeddings", font_size="9px", color=MUTED),
                    rx.divider(color=BDR, margin_y="8px"),
                    # User info
                    rx.text(AuthState.user_name, font_size="12px", color=TEXT,
                            font_weight="700", font_family=MONO),
                    rx.text(AuthState.user_email, font_size="10px", color=MUTED, font_family=MONO),
                    rx.button(
                        "↩ Sign Out",
                        on_click=AuthState.logout,
                        background="transparent", color=MUTED, border="none",
                        font_size="11px", font_family=MONO, cursor="pointer",
                        padding="4px 0", margin_top="4px",
                        _hover={"color": RED},
                    ),
                    spacing="1", align_items="start",
                ),
                padding="16px 18px",
                style={"border-top": f"1px solid {BDR}"},
                width="100%",
            ),
            spacing="0", height="100vh", align_items="start",
        ),
        width="215px", min_height="100vh", background=CARD,
        flex_shrink="0", position="sticky", top="0",
        style={"border-right": f"1px solid {BDR}"},
    )


# ── Pages (unchanged from your working version) ───────────────────────────────

def dashboard_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Dashboard", font_size="26px", font_weight="900",
                        color=TEXT, letter_spacing="-0.02em"),
                rx.text("Real-time financial intelligence overview", font_size="13px", color=MUTED),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                AppState.has_data,
                rx.hstack(
                    rx.text("RISK:", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                    risk_badge(AppState.risk_score),
                    rx.box(
                        rx.text(AppState.anomaly_count.to_string() + " ANOMALIES",
                                font_size="10px", font_weight="700", color=RED, letter_spacing="0.1em"),
                        padding="3px 10px", background="#1a0505", border_radius="5px",
                        style={"border": f"1px solid {RED}44"},
                    ),
                    spacing="3", align="center",
                ),
                rx.box(),
            ),
            width="100%", margin_bottom="24px",
        ),
        rx.cond(
            AppState.has_data,
            rx.vstack(
                rx.hstack(
                    stat_card("Total Spent",     AppState.total_spent.to_string(), "₹", CYAN),
                    stat_card("Transactions",    AppState.tx_count.to_string(),    "#", PURP),
                    stat_card("Avg Transaction", AppState.avg_spent.to_string(),   "₹", GREEN),
                    stat_card("Top Category",    AppState.top_category,            "",  AMBER),
                    spacing="4", width="100%", flex_wrap="wrap",
                ),
                rx.hstack(
                    card(
                        rx.vstack(
                            sh("Spending Breakdown", "Category distribution"),
                            pbar("Food",          AppState.food_pct,          AMBER),
                            pbar("Shopping",      AppState.shopping_pct,      PURP),
                            pbar("Transport",     AppState.transport_pct,     CYAN),
                            pbar("Entertainment", AppState.entertainment_pct, "#ec4899"),
                            spacing="4", width="100%",
                        ),
                        flex="1",
                    ),
                    card(
                        rx.vstack(
                            sh("Latest AI Analysis", "From Insights engine"),
                            rx.cond(
                                AppState.risk_level != "",
                                rx.vstack(
                                    rx.hstack(rx.text("Risk:", font_size="12px", color=MUTED, font_weight="600"),
                                              risk_badge(AppState.risk_level), spacing="2", align="center"),
                                    rx.box(rx.text(AppState.main_issue, font_size="13px", color=TEXT, line_height="1.8"),
                                           padding="12px 14px", background=BG, border_radius="8px", width="100%",
                                           style={"border-left": f"3px solid {CYAN}"}),
                                    rx.text("→ Full analysis in AI Insights", font_size="12px", color=CYAN,
                                            cursor="pointer", on_click=AppState.go_tab("insights"),
                                            _hover={"text_decoration": "underline"}),
                                    spacing="3", width="100%",
                                ),
                                rx.vstack(
                                    rx.text("No analysis yet", font_size="14px", color=MUTED, text_align="center", font_weight="600"),
                                    rx.button("→ Go to AI Insights", on_click=AppState.go_tab("insights"),
                                              background="transparent", color=CYAN, font_size="12px", cursor="pointer",
                                              style={"border": f"1px solid {CYAN}33"}, border_radius="6px", padding="6px 14px"),
                                    spacing="2", align="center", padding="10px", width="100%",
                                ),
                            ),
                            width="100%",
                        ),
                        flex="1",
                    ),
                    spacing="4", width="100%", align="start", flex_wrap="wrap",
                ),
                card(
                    rx.vstack(
                        sh("Recent Transactions", "Latest ingested events"),
                        rx.vstack(
                            rx.foreach(
                                AppState.transactions,
                                lambda tx: rx.hstack(
                                    cat_pill(tx["category"]),
                                    rx.text(tx["merchant"], font_size="13px", color=TEXT, font_weight="600", flex="1"),
                                    rx.text(tx["timestamp"], font_size="11px", color=MUTED, font_family=MONO),
                                    rx.text("₹" + tx["amount"].to_string(), font_size="14px", color=CYAN,
                                            font_weight="800", font_family=MONO, min_width="90px", text_align="right"),
                                    spacing="4", width="100%", padding="10px 0",
                                    style={"border-bottom": f"1px solid {BDR}33"}, align="center",
                                ),
                            ),
                            spacing="0", width="100%",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),
                spacing="4", width="100%",
            ),
            empty_state("No transactions yet"),
        ),
        spacing="5", width="100%", padding_bottom="40px", on_mount=AppState.on_page_load,
    )


def transactions_page():
    cats = ["All","Food","Shopping","Transport","Entertainment","Healthcare"]
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Transaction Ledger", font_size="26px", font_weight="900", color=TEXT, letter_spacing="-0.02em"),
                rx.text("Full indexed financial event history", font_size="13px", color=MUTED),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.hstack(
                *[rx.button(cat, on_click=AppState.set_filter(cat),
                            background=rx.cond(AppState.filter_category == cat, PURP, "transparent"),
                            color=rx.cond(AppState.filter_category == cat, "white", MUTED),
                            border_radius="7px", padding="6px 14px", font_size="12px",
                            font_weight="600", cursor="pointer", style={"border": f"1px solid {BDR}"},
                            _hover={"background": "#12203a", "color": TEXT}, transition="all 0.15s")
                  for cat in cats],
                spacing="2", flex_wrap="wrap",
            ),
            width="100%", margin_bottom="24px", flex_wrap="wrap", align="start",
        ),
        rx.cond(
            AppState.has_data,
            card(
                rx.vstack(
                    rx.hstack(
                        rx.text("TIMESTAMP", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em", width="180px"),
                        rx.text("MERCHANT",  font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em", flex="1"),
                        rx.text("CATEGORY",  font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em", width="120px"),
                        rx.text("AMOUNT",    font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em", width="100px", text_align="right"),
                        width="100%", padding="0 0 14px", style={"border-bottom": f"1px solid {BDR}"},
                    ),
                    rx.cond(
                        AppState.filtered_transactions.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                AppState.filtered_transactions,
                                lambda tx: rx.hstack(
                                    rx.text(tx["timestamp"], font_size="11px", color=MUTED, font_family=MONO, width="180px"),
                                    rx.text(tx["merchant"], font_size="13px", color=TEXT, font_weight="600", flex="1"),
                                    rx.box(cat_pill(tx["category"]), width="120px"),
                                    rx.text("₹"+tx["amount"].to_string(), font_size="13px", color=CYAN,
                                            font_weight="700", font_family=MONO, width="100px", text_align="right"),
                                    spacing="4", width="100%", padding="11px 0",
                                    style={"border-bottom": f"1px solid {BDR}22"}, align="center",
                                    _hover={"background": "#0a1626"}, transition="background 0.1s",
                                ),
                            ),
                            spacing="0", width="100%",
                        ),
                        rx.box(rx.text("No transactions in this category", font_size="13px",
                                       color=MUTED, text_align="center"), padding="50px", width="100%"),
                    ),
                    spacing="0", width="100%",
                ),
                width="100%",
            ),
            empty_state("No transactions yet"),
        ),
        spacing="4", width="100%", padding_bottom="40px", on_mount=AppState.load_transactions,
    )


def insights_page():
    return rx.vstack(
        rx.vstack(
            rx.text("AI Insights Engine", font_size="26px", font_weight="900", color=TEXT, letter_spacing="-0.02em"),
            rx.text("Vector retrieval  ·  Statistical analytics  ·  LLM reasoning", font_size="13px", color=MUTED),
            spacing="1", align_items="start", margin_bottom="20px",
        ),
        card(
            rx.hstack(
                *[rx.hstack(
                    rx.vstack(
                        rx.text(icon, font_size="18px", text_align="center"),
                        rx.text(step, font_size="9px", color=CYAN, font_weight="700", letter_spacing="0.08em", text_align="center"),
                        rx.text(desc, font_size="9px", color=MUTED, text_align="center"),
                        spacing="1", align="center", min_width="70px",
                    ),
                    rx.text("→", font_size="16px", color=BDR) if i < 4 else rx.box(),
                    spacing="2", align="center",
                ) for i, (icon, step, desc) in enumerate([
                    ("()--","QUERY","User input"), ("◈","EMBED","MiniLM-L6"),
                    ("⊞","RETRIEVE","FAISS Top-5"), ("[|]","STATS","SQLite agg"),
                    ("@","REASON","Gemini LLM"),
                ])],
                spacing="0", justify="center", width="100%",
            ),
            width="100%", padding="16px 24px",
        ),
        card(
            rx.vstack(
                rx.text("QUERY THE INTELLIGENCE ENGINE", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.14em"),
                rx.hstack(
                    rx.input(
                        placeholder="e.g. 'Analyze my food spending' · 'Any unusual activity?' · 'Where am I overspending?'",
                        on_change=AppState.set_question, value=AppState.question,
                        background=BG, border_radius="8px", height="44px",
                        font_size="14px", color=TEXT, flex="1", style=IS, _placeholder={"color": MUTED},
                    ),
                    rx.button(
                        rx.cond(
                            AppState.is_loading,
                            rx.hstack(rx.spinner(color=CYAN, size="2"),
                                      rx.text("Analyzing…", font_size="13px", font_weight="700"),
                                      spacing="2", align="center"),
                            rx.hstack(rx.text("◈", font_size="14px"),
                                      rx.text("Analyze", font_size="13px", font_weight="700"),
                                      spacing="2", align="center"),
                        ),
                        on_click=AppState.run_analysis,
                        background=rx.cond(AppState.is_loading, "#4a1d96", PURP),
                        color="white", border_radius="8px", height="44px", padding="0 24px",
                        cursor="pointer", _hover={"background": "#6d28d9"},
                        disabled=AppState.is_loading, transition="all 0.15s", white_space="nowrap",
                    ),
                    spacing="3", width="100%", align="center",
                ),
                rx.hstack(
                    rx.text("Try:", font_size="11px", color=MUTED),
                    *[rx.box(rx.text(q, font_size="11px", color=CYAN, cursor="pointer", _hover={"color": TEXT}),
                             padding="3px 10px", background="#001520", border_radius="4px",
                             cursor="pointer", style={"border": f"1px solid {CYAN}33"},
                             on_click=AppState.set_question(q))
                      for q in ["Analyze my overall spending risk","Where am I overspending?",
                                "Is there unusual activity?","Break down my food expenses"]],
                    spacing="2", flex_wrap="wrap", align="center",
                ),
                spacing="3",
            ),
            width="100%",
        ),
        rx.cond(AppState.analysis_error != "",
                rx.box(rx.text(AppState.analysis_error, font_size="13px", color=RED, font_weight="600"),
                       padding="12px 16px", background="#1a0404", border_radius="8px", width="100%",
                       style={"border": f"1px solid {RED}55"}), rx.box()),
        rx.cond(
            AppState.risk_level != "",
            rx.vstack(
                card(
                    rx.hstack(
                        rx.vstack(rx.text("RISK LEVEL", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                                  risk_badge(AppState.risk_level), spacing="2", align_items="start"),
                        rx.box(style={"border-left": f"1px solid {BDR}"}, height="48px", margin_x="20px"),
                        rx.vstack(rx.text("MAIN FINDING", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                                  rx.text(AppState.main_issue, font_size="14px", color=TEXT, line_height="1.6"),
                                  spacing="1", align_items="start", flex="1"),
                        spacing="0", width="100%", align="center",
                    ),
                    width="100%", padding="20px 24px",
                ),
                rx.hstack(
                    card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("RETRIEVED CONTEXT", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                                rx.spacer(),
                                rx.box(rx.text("FAISS · Top-5", font_size="9px", color=GREEN, font_weight="700"),
                                       padding="2px 8px", background="#041a10", border_radius="4px",
                                       style={"border": f"1px solid {GREEN}44"}),
                                width="100%", align="center",
                            ),
                            rx.text("Semantically similar records from vector index", font_size="11px", color=MUTED, margin_bottom="10px"),
                            rx.vstack(
                                rx.foreach(AppState.retrieved_context,
                                    lambda ctx: rx.box(
                                        rx.text(ctx, font_size="11px", color=GREEN, font_family=MONO, line_height="1.6"),
                                        padding="8px 12px", background="#030e08", border_radius="0 6px 6px 0",
                                        margin_bottom="6px", width="100%", style={"border-left": f"3px solid {GREEN}"},
                                    )),
                                spacing="0", width="100%",
                            ),
                            spacing="0", width="100%", align_items="start",
                        ),
                        flex="1", min_width="250px",
                    ),
                    card(
                        rx.vstack(
                            rx.text("KEY OBSERVATIONS", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                            rx.vstack(
                                rx.foreach(AppState.key_observations,
                                    lambda obs: rx.hstack(
                                        rx.box(rx.text("→", font_size="12px", color=CYAN, font_weight="900"), min_width="20px"),
                                        rx.text(obs, font_size="13px", color=TEXT, line_height="1.7"),
                                        spacing="2", align="start", width="100%",
                                    )),
                                spacing="3", width="100%", margin_bottom="18px",
                            ),
                            rx.hstack(
                                rx.text("RECOMMENDED ACTIONS", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.12em"),
                                rx.spacer(),
                                rx.box(rx.text("AI-generated", font_size="9px", color=PURP, font_weight="700"),
                                       padding="2px 8px", background="#100818", border_radius="4px",
                                       style={"border": f"1px solid {PURP}44"}),
                                width="100%", align="center",
                            ),
                            rx.vstack(
                                rx.foreach(AppState.recommended_actions,
                                    lambda act: rx.hstack(
                                        rx.box(rx.text("✓", font_size="12px", color=GREEN, font_weight="900"), min_width="20px"),
                                        rx.text(act, font_size="13px", color=TEXT, line_height="1.7"),
                                        spacing="2", align="start", width="100%",
                                    )),
                                spacing="3", width="100%",
                            ),
                            spacing="3", align_items="start", width="100%",
                        ),
                        flex="1.4", min_width="250px",
                    ),
                    spacing="4", width="100%", align="start", flex_wrap="wrap",
                ),
                spacing="4", width="100%",
            ),
            rx.box(),
        ),
        spacing="4", width="100%", padding_bottom="40px",
    )


def anomalies_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Anomaly Detection", font_size="26px", font_weight="900", color=TEXT, letter_spacing="-0.02em"),
                rx.text("Statistical outlier scan  ·  z-score ±2σ", font_size="13px", color=MUTED),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.box(rx.text("SECURITY SCAN", font_size="10px", color=RED, font_weight="800", letter_spacing="0.14em"),
                   padding="5px 14px", background="#180404", border_radius="5px",
                   style={"border": f"1px solid {RED}55"}),
            width="100%", margin_bottom="24px", align="center",
        ),
        card(
            rx.hstack(
                rx.box(rx.text("⚡", font_size="22px"), padding="10px", background="#140c00", border_radius="9px"),
                rx.vstack(
                    rx.text("Detection Methodology", font_size="14px", font_weight="700", color=TEXT),
                    rx.text("Transactions deviating more than 2 standard deviations from your mean spend are flagged. Requires ≥5 transactions.",
                            font_size="13px", color=MUTED, line_height="1.75"),
                    spacing="1", align_items="start",
                ),
                spacing="4", align="start", width="100%",
            ),
            width="100%", xs={"border": f"1px solid {AMBER}33"},
        ),
        rx.cond(
            AppState.has_data,
            rx.cond(
                AppState.anomalies.length() > 0,
                rx.vstack(
                    rx.foreach(AppState.anomalies,
                        lambda tx: card(
                            rx.hstack(
                                rx.box(rx.text("⚠", font_size="20px"), padding="10px", background="#1a0505", border_radius="9px"),
                                rx.vstack(
                                    rx.text(tx["merchant"], font_size="16px", font_weight="800", color=TEXT),
                                    rx.hstack(cat_pill(tx["category"]), rx.text("·", color=MUTED),
                                              rx.text(tx["timestamp"], font_size="12px", color=MUTED, font_family=MONO),
                                              spacing="2", align="center"),
                                    spacing="2", align_items="start",
                                ),
                                rx.spacer(),
                                rx.vstack(
                                    rx.text("₹"+tx["amount"].to_string(), font_size="22px", font_weight="900", color=RED, font_family=MONO),
                                    rx.text("ANOMALOUS", font_size="9px", color=RED, letter_spacing="0.16em", text_align="right"),
                                    spacing="0", align_items="end",
                                ),
                                spacing="4", width="100%", align="center",
                            ),
                            width="100%", xs={"border": f"1px solid {RED}44"},
                        )),
                    spacing="3", width="100%",
                ),
                card(
                    rx.vstack(
                        rx.text("✓", font_size="36px", color=GREEN, text_align="center"),
                        rx.text("No anomalies detected", font_size="15px", font_weight="700", color=GREEN, text_align="center"),
                        rx.text("All transactions within normal range", font_size="12px", color=MUTED, text_align="center"),
                        spacing="2", align="center", padding="36px", width="100%",
                    ),
                    width="100%", xs={"border": f"1px solid {GREEN}44"},
                ),
            ),
            empty_state("Add transactions to run anomaly detection"),
        ),
        spacing="4", width="100%", padding_bottom="40px", on_mount=AppState.load_anomalies,
    )


def add_page():
    return rx.vstack(
        rx.vstack(
            rx.text("Data Ingestion", font_size="26px", font_weight="900", color=TEXT, letter_spacing="-0.02em"),
            rx.text("Stream new financial events into the live RAG pipeline", font_size="13px", color=MUTED),
            spacing="1", align_items="start", margin_bottom="24px",
        ),
        rx.hstack(
            card(
                rx.vstack(
                    rx.text("QUICK ADD", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.14em"),
                    rx.divider(color=BDR, margin_y="10px"),
                    rx.text("Auto-generate a realistic transaction", font_size="14px", color=TEXT, font_weight="600"),
                    rx.text("Randomly picks from 12 real merchants. Amount ₹100–₹2000.",
                            font_size="12px", color=MUTED, line_height="1.75"),
                    rx.button(
                        rx.hstack(rx.text("⊕"), rx.text("Generate Transaction", font_weight="700"), spacing="2", align="center"),
                        on_click=AppState.add_random,
                        background=PURP, color="white", border_radius="9px",
                        padding="11px 22px", cursor="pointer", width="100%",
                        _hover={"background": "#6d28d9"}, transition="all 0.15s",
                    ),
                    rx.cond(
                        AppState.add_status != "",
                        rx.box(
                            rx.text(AppState.add_status, font_size="13px", font_weight="600",
                                    font_family=MONO, color=rx.cond(AppState.add_ok, GREEN, RED)),
                            padding="9px 14px",
                            background=rx.cond(AppState.add_ok, "#031310", "#1a0404"),
                            border_radius="7px", width="100%",
                        ),
                        rx.box(),
                    ),
                    spacing="4", width="100%",
                ),
                flex="1",
            ),
            card(
                rx.vstack(
                    rx.text("CUSTOM TRANSACTION", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.14em"),
                    rx.divider(color=BDR, margin_y="10px"),
                    rx.vstack(
                        rx.text("MERCHANT", font_size="10px", color=MUTED, font_weight="600", letter_spacing="0.1em"),
                        inp("e.g. BigBazaar, HDFC, Zomato", AppState.set_custom_merchant, AppState.custom_merchant, width="100%"),
                        spacing="2", width="100%",
                    ),
                    rx.vstack(
                        rx.text("CATEGORY", font_size="10px", color=MUTED, font_weight="600", letter_spacing="0.1em"),
                        rx.select(["Food","Shopping","Transport","Entertainment","Healthcare","Other"],
                                  on_change=AppState.set_custom_category, value=AppState.custom_category,
                                  background=BG, border_radius="8px", color=TEXT, width="100%",
                                  style={"border": f"1px solid {BDR}"}),
                        spacing="2", width="100%",
                    ),
                    rx.vstack(
                        rx.text("AMOUNT (₹)", font_size="10px", color=MUTED, font_weight="600", letter_spacing="0.1em"),
                        inp("0.00", AppState.set_custom_amount, AppState.custom_amount, width="100%"),
                        spacing="2", width="100%",
                    ),
                    rx.button(
                        rx.hstack(rx.text("⊕"), rx.text("Add Transaction", font_weight="700"), spacing="2", align="center"),
                        on_click=AppState.add_custom,
                        background=GREEN, color="white", border_radius="9px",
                        padding="11px 22px", cursor="pointer", width="100%",
                        _hover={"background": "#059669"}, transition="all 0.15s",
                    ),
                    spacing="3", width="100%",
                ),
                flex="1",
            ),
            spacing="4", width="100%", align="start", flex_wrap="wrap",
        ),
        card(
            rx.vstack(
                rx.text("SYSTEM ARCHITECTURE", font_size="10px", color=MUTED, font_weight="700", letter_spacing="0.14em"),
                rx.divider(color=BDR, margin_y="10px"),
                rx.hstack(
                    *[rx.hstack(
                        rx.vstack(
                            rx.text(icon, font_size="20px", text_align="center"),
                            rx.text(lbl, font_size="10px", color=clr, font_weight="700", text_align="center", letter_spacing="0.06em"),
                            rx.text(tech, font_size="9px", color=MUTED, text_align="center"),
                            spacing="1", align="center", min_width="85px",
                        ),
                        rx.text("→", font_size="18px", color=BDR) if i < 5 else rx.box(),
                        spacing="2", align="center",
                    ) for i, (icon, lbl, tech, clr) in enumerate([
                        ("⊕","INGEST","Transaction",CYAN), ("◈","EMBED","MiniLM-L6-v2",PURP),
                        ("⊞","INDEX","FAISS IVF",GREEN), ("◎","PERSIST","SQLite",AMBER),
                        ("🔍","RETRIEVE","Vector Search",CYAN), ("@","REASON","Gemini Flash",RED),
                    ])],
                    spacing="0", justify="center", width="100%", flex_wrap="wrap",
                ),
                spacing="4", width="100%", align="center",
            ),
            width="100%", padding="20px 24px",
        ),
        spacing="4", width="100%", padding_bottom="40px",
    )


# ── Root — auth gate ──────────────────────────────────────────────────────────

def index():
    return rx.cond(
        AuthState.is_logged_in,
        rx.box(
            rx.hstack(
                sidebar(),
                rx.box(
                    rx.cond(AppState.active_tab == "dashboard",    dashboard_page(),    rx.box()),
                    rx.cond(AppState.active_tab == "transactions", transactions_page(), rx.box()),
                    rx.cond(AppState.active_tab == "insights",     insights_page(),     rx.box()),
                    rx.cond(AppState.active_tab == "anomalies",    anomalies_page(),    rx.box()),
                    rx.cond(AppState.active_tab == "add",          add_page(),          rx.box()),
                    padding="36px 44px", flex="1", overflow_y="auto", min_height="100vh",
                ),
                spacing="0", width="100%", align="start",
            ),
            overflow_x="hidden", background=BG, min_height="100vh", color=TEXT,
        ),
        login_page(),
    )


# ── Google OAuth callback ─────────────────────────────────────────────────────

class GoogleCallbackState(rx.State):
    def on_load(self):
        code = self.router.page.params.get("code", "")
        if code:
            return AuthState.process_google_code(code)
        return rx.redirect("/")

def google_callback_page():
    return rx.box(
        rx.vstack(
            rx.spinner(color=CYAN, size="3"),
            rx.text("Signing in with Google…", font_size="14px", color=MUTED, font_family=MONO),
            spacing="4", align="center",
        ),
        display="flex", align_items="center", justify_content="center",
        min_height="100vh", background=BG,
        on_mount=GoogleCallbackState.on_load,
    )


# ── Email verify ──────────────────────────────────────────────────────────────

class VerifyState(rx.State):
    ok: bool = False
    msg: str = ""

    def on_load(self):
        token = self.router.page.params.get("token", "")
        if not token:
            self.msg = "Invalid or missing token."; return
        from .auth_db import verify_email_token
        if verify_email_token(token):
            self.ok = True; self.msg = "Email verified!"
        else:
            self.msg = "This link has expired or was already used."

def verify_email_page():
    return rx.cond(
        VerifyState.ok,
        verified_page(),
        rx.box(
            rx.vstack(
                rx.text("◈", font_size="40px", color=CYAN),
                rx.text(VerifyState.msg, font_size="15px", color=RED, font_family=MONO, text_align="center"),
                rx.button("→ Back to Login", on_click=rx.redirect("/"), background=PURP, color="white",
                          border_radius="8px", padding="10px 24px", cursor="pointer", _hover={"background": "#6d28d9"}),
                spacing="4", align="center",
            ),
            display="flex", align_items="center", justify_content="center", min_height="100vh", background=BG,
        ),
    )


# ── App ───────────────────────────────────────────────────────────────────────

app = rx.App()
app.add_page(index,                on_load=AuthState.check_session)
app.add_page(google_callback_page, route="/auth/google/callback",
             on_load=GoogleCallbackState.on_load)
app.add_page(verify_email_page,    route="/verify-email",
             on_load=VerifyState.on_load)