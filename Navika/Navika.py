# finance_ai/finance_ai.py
import reflex as rx
import random
from datetime import datetime
from typing import List, Dict, Any

from .database import get_all_transactions
from .analytics import detect_anomalies
from .auth_state import AuthState
from .login_page import login_page, verified_page, reset_password_page

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


def format_currency(val: float) -> str:
    try:
        val = float(val)
        if abs(val) >= 1_000_000_000_000:
            return f"{val / 1_000_000_000_000:.2f}T"
        elif abs(val) >= 1_000_000_000:
            return f"{val / 1_000_000_000:.2f}B"
        elif abs(val) >= 10_000_000:
            return f"{val / 10_000_000:.2f}Cr"
        elif abs(val) >= 100_000:
            return f"{val / 100_000:.2f}L"
        elif abs(val) >= 1_000:
            return f"{val / 1_000:.2f}k"
        return f"{val:,.2f}"
    except Exception:
        return str(val)


class AppState(rx.State):
    active_tab: str = "dashboard"

    total_spent: float = 0.0
    total_spent_display: str = "0.00"
    avg_spent: float = 0.0
    avg_spent_display: str = "0.00"
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

    # ── Custom Dynamic Budgets ────────────────────────────────────────────────
    monthly_budget_cap: float = 25000.0
    food_budget_cap: float = 8000.0
    shopping_budget_cap: float = 10000.0
    transport_budget_cap: float = 4000.0
    ent_budget_cap: float = 3000.0

    edit_monthly_cap: str = "25000"
    edit_food_cap: str = "8000"
    edit_shopping_cap: str = "10000"
    edit_transport_cap: str = "4000"
    edit_ent_cap: str = "3000"

    budget_modal_open: bool = False
    budget_msg: str = ""

    # Computed Budget Display
    monthly_budget_display: str = "₹25,000"
    remaining_budget_display: str = "₹25,000"
    food_spent_amt: float = 0.0
    shopping_spent_amt: float = 0.0
    transport_spent_amt: float = 0.0
    ent_spent_amt: float = 0.0

    def set_edit_monthly_cap(self, v: str):   self.edit_monthly_cap = v
    def set_edit_food_cap(self, v: str):      self.edit_food_cap = v
    def set_edit_shopping_cap(self, v: str):  self.edit_shopping_cap = v
    def set_edit_transport_cap(self, v: str): self.edit_transport_cap = v
    def set_edit_ent_cap(self, v: str):       self.edit_ent_cap = v

    def open_budget_modal(self):
        self.edit_monthly_cap = str(int(self.monthly_budget_cap))
        self.edit_food_cap = str(int(self.food_budget_cap))
        self.edit_shopping_cap = str(int(self.shopping_budget_cap))
        self.edit_transport_cap = str(int(self.transport_budget_cap))
        self.edit_ent_cap = str(int(self.ent_budget_cap))
        self.budget_msg = ""
        self.budget_modal_open = True

    def close_budget_modal(self):
        self.budget_modal_open = False

    def save_custom_budgets(self):
        try:
            m = float(self.edit_monthly_cap)
            f = float(self.edit_food_cap)
            s = float(self.edit_shopping_cap)
            t = float(self.edit_transport_cap)
            e = float(self.edit_ent_cap)
            assert m > 0 and f >= 0 and s >= 0 and t >= 0 and e >= 0
        except Exception:
            self.budget_msg = "Please enter valid numeric amounts"
            return
        self.monthly_budget_cap = m
        self.food_budget_cap = f
        self.shopping_budget_cap = s
        self.transport_budget_cap = t
        self.ent_budget_cap = e
        uid = self._get_uid()
        from .auth_db import save_user_budget
        save_user_budget(uid, m, f, s, t, e)
        self.budget_modal_open = False
        self._refresh()

    def _load_budgets(self):
        uid = self._get_uid()
        from .auth_db import get_user_budget
        b = get_user_budget(uid)
        self.monthly_budget_cap = b.get("monthly_cap", 25000.0)
        self.food_budget_cap = b.get("food_cap", 8000.0)
        self.shopping_budget_cap = b.get("shopping_cap", 10000.0)
        self.transport_budget_cap = b.get("transport_cap", 4000.0)
        self.ent_budget_cap = b.get("ent_cap", 3000.0)

    # ── Sidebar collapse toggle ───────────────────────────────────────────────
    sidebar_collapsed: bool = False

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed

    def load_transactions(self): self._load_tx()
    def load_anomalies(self):    self._load_anomalies()

    def go_tab(self, tab: str):
        self.active_tab = tab
        if tab == "dashboard":      self._refresh()
        elif tab == "transactions": self._load_tx()
        elif tab == "budgets":      self._load_budgets(); self._refresh()
        elif tab == "anomalies":    self._load_anomalies()
        elif tab == "profile":      pass
        elif tab == "notes":        pass

    def _get_uid(self) -> int:
        try:
            auth = self.get_state(AuthState)
            if auth.user_id:
                return int(auth.user_id)
            if auth.session_token:
                from .auth_db import get_user_from_session
                u = get_user_from_session(str(auth.session_token))
                if u:
                    return u.id
        except Exception:
            pass
        return 1

    def _refresh(self):
        from .rag_engine import compute_stats
        txs = get_all_transactions()
        self.tx_count = len(txs); self.has_data = self.tx_count > 0
        self.transactions = txs
        stats = compute_stats()
        if stats and self.has_data:
            self.total_spent = round(stats.get("total_spent", 0), 2)
            self.total_spent_display = format_currency(self.total_spent)
            self.avg_spent   = round(stats.get("average_spent", 0), 2)
            self.avg_spent_display   = format_currency(self.avg_spent)
            cat   = stats.get("category_totals", {})
            self.food_spent_amt        = round(cat.get("Food", 0), 2)
            self.shopping_spent_amt    = round(cat.get("Shopping", 0), 2)
            self.transport_spent_amt   = round(cat.get("Transport", 0), 2)
            self.ent_spent_amt         = round(cat.get("Entertainment", 0), 2)

            f_cap = self.food_budget_cap or 1
            s_cap = self.shopping_budget_cap or 1
            t_cap = self.transport_budget_cap or 1
            e_cap = self.ent_budget_cap or 1

            self.food_pct          = min(100.0, round(self.food_spent_amt        / f_cap * 100, 1))
            self.shopping_pct      = min(100.0, round(self.shopping_spent_amt    / s_cap * 100, 1))
            self.transport_pct     = min(100.0, round(self.transport_spent_amt   / t_cap * 100, 1))
            self.entertainment_pct = min(100.0, round(self.ent_spent_amt         / e_cap * 100, 1))
            self.top_category      = max(cat, key=cat.get) if cat else ""
        else:
            self.total_spent_display = "0.00"
            self.avg_spent_display   = "0.00"
            self.food_pct = 0.0
            self.shopping_pct = 0.0
            self.transport_pct = 0.0
            self.entertainment_pct = 0.0

        rem = max(0.0, round(self.monthly_budget_cap - self.total_spent, 2))
        self.monthly_budget_display   = format_currency(self.monthly_budget_cap)
        self.remaining_budget_display = format_currency(rem)
        self.risk_score = (
            "High"   if self.total_spent > self.monthly_budget_cap else
            "Medium" if self.total_spent > (self.monthly_budget_cap * 0.6)  else "Low"
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
        uid = self._get_uid()
        from .rag_engine import add_transaction_to_rag
        add_transaction_to_rag(m, pool[m], a, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id=uid)
        self.add_status = f"✓  {m}  ₹{a}"; self.add_ok = True
        self._refresh()

    def add_custom(self):
        if not self.custom_merchant.strip() or not self.custom_amount.strip():
            self.add_status = "✗  Merchant and amount required"; self.add_ok = False; return
        try:
            a = float(self.custom_amount); assert a > 0
        except Exception:
            self.add_status = "✗  Enter a valid positive amount"; self.add_ok = False; return
        uid = self._get_uid()
        from .rag_engine import add_transaction_to_rag
        add_transaction_to_rag(
            self.custom_merchant.strip(), self.custom_category,
            round(a, 2), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id=uid,
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

def pbar(label, pct, color):
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_size="13px", color="#e2e8f0", font_weight="600"),
            rx.spacer(),
            rx.text(pct.to_string() + "%", font_size="12px", color=color,
                    font_weight="800", font_family=MONO),
            width="100%",
        ),
        rx.box(
            rx.box(
                height="8px", width=pct.to_string() + "%",
                background=f"linear-gradient(90deg, {color}, {color}dd)",
                border_radius="6px", transition="width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
                box_shadow=f"0 0 10px {color}44",
            ),
            width="100%", height="8px", background="#070e1e", border_radius="6px",
            border="1px solid rgba(255, 255, 255, 0.05)",
        ),
        spacing="2", width="100%",
    )


def stat_card(label, value, prefix, color, svg_icon):
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(label, font_size="11px", font_weight="700", color="#64748b",
                        letter_spacing="0.1em", font_family=MONO),
                rx.spacer(),
                rx.box(
                    rx.html(svg_icon),
                    padding="6px",
                    background=f"{color}15",
                    border=f"1px solid {color}33",
                    border_radius="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    prefix != "",
                    rx.text(prefix, font_size="16px", color=color, font_weight="800",
                            align_self="flex-end", padding_bottom="4px"),
                    rx.box(),
                ),
                rx.text(
                    value,
                    font_size="22px",
                    font_weight="900",
                    color="#ffffff",
                    letter_spacing="-0.02em",
                    font_family="'Plus Jakarta Sans', sans-serif",
                    max_width="100%",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                spacing="1", align="end", width="100%", overflow="hidden",
            ),
            spacing="2", align_items="start", width="100%",
        ),
        padding="20px",
        background="rgba(11, 18, 33, 0.75)",
        border="1px solid rgba(255, 255, 255, 0.08)",
        border_radius="16px",
        min_width="0",
        flex="1 1 200px",
        box_shadow="0 12px 30px rgba(0,0,0,0.35)",
        transition="all 0.2s ease",
        _hover={"border-color": f"{color}66", "transform": "translateY(-2px)"},
    )

def cat_pill(cat):
    M = {"Food":(AMBER,"#160e00"),"Shopping":(PURP,"#100818"),
         "Transport":(CYAN,"#001318"),"Entertainment":("#ec4899","#160010"),
         "Healthcare":(GREEN,"#031310")}
    clr, bg = M.get(cat, (MUTED, "#0d141e"))
    return rx.box(
        rx.text(cat, font_size="10.5px", font_weight="700", color=clr, letter_spacing="0.06em"),
        padding="3px 10px", background=bg, border_radius="5px", display="inline-block",
    )

def sh(title, sub=""):
    return rx.vstack(
        rx.text(title, font_size="18px", font_weight="800", color=TEXT),
        rx.cond(sub != "", rx.text(sub, font_size="12px", color=MUTED), rx.box(height="0")),
        spacing="1", margin_bottom="16px", align_items="start",
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


# ── Vector SVGs for Sidebar & Dashboard ───────────────────────────────────────
NAV_ICONS = {
    "dashboard": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7"></rect>
      <rect x="14" y="3" width="7" height="7"></rect>
      <rect x="14" y="14" width="7" height="7"></rect>
      <rect x="3" y="14" width="7" height="7"></rect>
    </svg>""",
    "transactions": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="8" y1="6" x2="21" y2="6"></line>
      <line x1="8" y1="12" x2="21" y2="12"></line>
      <line x1="8" y1="18" x2="21" y2="18"></line>
      <line x1="3" y1="6" x2="3.01" y2="6"></line>
      <line x1="3" y1="12" x2="3.01" y2="12"></line>
      <line x1="3" y1="18" x2="3.01" y2="18"></line>
    </svg>""",
    "insights": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
    </svg>""",
    "anomalies": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
    </svg>""",
    "add": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="8" x2="12" y2="16"></line>
      <line x1="8" y1="12" x2="16" y2="12"></line>
    </svg>""",
    "budgets": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
      <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
    </svg>""",
    "notes": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>""",
    "profile": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>""",
    "collapse": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="9" y1="3" x2="9" y2="21"></line>
      <path d="m14 9-3 3 3 3"></path>
    </svg>""",
    "expand": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="9" y1="3" x2="9" y2="21"></line>
      <path d="m13 15 3-3-3-3"></path>
    </svg>""",
    "signout": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
      <polyline points="16 17 21 12 16 7"></polyline>
      <line x1="21" y1="12" x2="9" y2="12"></line>
    </svg>"""
}

# ── User Avatar Helper ────────────────────────────────────────────────────────

def user_avatar(size: str = "36px", font_size: str = "14px"):
    return rx.cond(
        AuthState.avatar_url != "",
        rx.image(
            src=AuthState.avatar_url,
            width=size,
            height=size,
            border_radius="10px",
            object_fit="cover",
            border="1px solid rgba(0, 212, 255, 0.4)",
            box_shadow="0 0 10px rgba(0, 212, 255, 0.2)",
        ),
        rx.box(
            rx.html("""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>"""),
            width=size,
            height=size,
            border_radius="10px",
            background="rgba(0, 212, 255, 0.12)",
            border="1px solid rgba(0, 212, 255, 0.25)",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )

# ── Sidebar ───────────────────────────────────────────────────────────────────

def nbtn(label, tab, badge=""):
    is_active = AppState.active_tab == tab
    return rx.button(
        rx.cond(
            AppState.sidebar_collapsed,
            # Collapsed mode: perfectly centered 44px icon tile
            rx.box(
                rx.html(NAV_ICONS[tab]),
                color=rx.cond(is_active, CYAN, "#94a3b8"),
                display="flex",
                align_items="center",
                justify_content="center",
                width="100%",
                height="100%",
            ),
            # Expanded mode: icon + label + badge
            rx.hstack(
                rx.box(
                    rx.html(NAV_ICONS[tab]),
                    color=rx.cond(is_active, CYAN, "#94a3b8"),
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(
                    label,
                    font_size="13.5px",
                    font_weight=rx.cond(is_active, "700", "500"),
                    color=rx.cond(is_active, "#ffffff", "#94a3b8"),
                    white_space="nowrap",
                ),
                rx.spacer(),
                rx.cond(
                    badge != "",
                    rx.box(
                        rx.text(badge, font_size="10px", font_weight="800",
                                color=rx.cond(is_active, "#ffffff", CYAN), font_family=MONO),
                        padding="2px 7px",
                        background=rx.cond(is_active, "rgba(0, 212, 255, 0.3)", "rgba(0, 212, 255, 0.1)"),
                        border_radius="6px",
                    ),
                    rx.box(),
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
        ),
        on_click=AppState.go_tab(tab),
        background=rx.cond(is_active, "rgba(0, 212, 255, 0.12)", "transparent"),
        border_radius="12px",
        height="44px",
        width=rx.cond(AppState.sidebar_collapsed, "44px", "100%"),
        padding=rx.cond(AppState.sidebar_collapsed, "0", "0 14px"),
        display="flex",
        align_items="center",
        justify_content="center",
        cursor="pointer",
        transition="all 0.2s ease",
        style={
            "border": rx.cond(is_active, f"1px solid rgba(0, 212, 255, 0.35)", "1px solid transparent"),
        },
        _hover={
            "background": rx.cond(is_active, "rgba(0, 212, 255, 0.16)", "rgba(255, 255, 255, 0.06)"),
            "border": f"1px solid rgba(255, 255, 255, 0.12)",
        },
    )

def sidebar():
    return rx.box(
        rx.vstack(
            # Brand Header & Interactive Toggle
            rx.cond(
                AppState.sidebar_collapsed,
                # Collapsed Mode: Single perfectly centered 44px brand tile
                rx.box(
                    rx.box(
                        rx.html("""<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>"""),
                        width="44px",
                        height="44px",
                        background="rgba(0, 212, 255, 0.12)",
                        border="1px solid rgba(0, 212, 255, 0.3)",
                        border_radius="12px",
                        box_shadow="0 0 15px rgba(0, 212, 255, 0.25)",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        cursor="pointer",
                        on_click=AppState.toggle_sidebar,
                    ),
                    padding="16px 0",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    width="100%",
                    style={"border-bottom": "1px solid rgba(255, 255, 255, 0.08)"},
                ),
                # Expanded Mode: Full header with brand name + collapse button
                rx.box(
                    rx.hstack(
                        rx.hstack(
                            rx.box(
                                rx.html("""<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>"""),
                                width="44px",
                                height="44px",
                                background="rgba(0, 212, 255, 0.12)",
                                border="1px solid rgba(0, 212, 255, 0.3)",
                                border_radius="12px",
                                box_shadow="0 0 15px rgba(0, 212, 255, 0.25)",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                cursor="pointer",
                                on_click=AppState.toggle_sidebar,
                                flex_shrink="0",
                            ),
                            rx.vstack(
                                rx.text("NAVIKA", font_size="17px", font_weight="900",
                                        color="#ffffff", letter_spacing="0.18em", font_family="'Plus Jakarta Sans', sans-serif"),
                                rx.text("AI FINANCIAL OS", font_size="9px",
                                        color=CYAN, letter_spacing="0.12em", font_weight="800", font_family=MONO),
                                spacing="0", align_items="start",
                            ),
                            spacing="3", align="center",
                        ),
                        rx.spacer(),
                        rx.box(
                            rx.html(NAV_ICONS["collapse"]),
                            color="#64748b",
                            cursor="pointer",
                            padding="6px",
                            border_radius="6px",
                            _hover={"color": "#ffffff", "background": "rgba(255,255,255,0.08)"},
                            on_click=AppState.toggle_sidebar,
                            transition="all 0.15s ease",
                        ),
                        width="100%", align="center",
                    ),
                    padding="20px 16px",
                    style={"border-bottom": "1px solid rgba(255, 255, 255, 0.08)"},
                    width="100%",
                ),
            ),

            # Navigation Links
            rx.vstack(
                # Section 1: Main Overview
                rx.cond(
                    ~AppState.sidebar_collapsed,
                    rx.text("FINANCIAL TELEMETRY", font_size="10px", color="#475569",
                            font_weight="800", letter_spacing="0.12em", font_family=MONO,
                            padding_x="14px", margin_top="10px", margin_bottom="4px"),
                    rx.box(height="6px"),
                ),
                nbtn("Dashboard",       "dashboard"),
                nbtn("Transactions",    "transactions"),
                nbtn("Budgets & Goals", "budgets", badge="NEW"),
                nbtn("Event Notes",     "notes"),

                # Section 2: AI & Analytics
                rx.cond(
                    ~AppState.sidebar_collapsed,
                    rx.text("INTELLIGENCE ENGINE", font_size="10px", color="#475569",
                            font_weight="800", letter_spacing="0.12em", font_family=MONO,
                            padding_x="14px", margin_top="14px", margin_bottom="4px"),
                    rx.box(height="6px"),
                ),
                nbtn("AI Insights",     "insights", badge="RAG"),
                nbtn("Anomalies",       "anomalies"),
                nbtn("Add Data",        "add"),

                # Section 3: User Management
                rx.cond(
                    ~AppState.sidebar_collapsed,
                    rx.text("ACCOUNT & PREFERENCES", font_size="10px", color="#475569",
                            font_weight="800", letter_spacing="0.12em", font_family=MONO,
                            padding_x="14px", margin_top="14px", margin_bottom="4px"),
                    rx.box(height="6px"),
                ),
                nbtn("Profile Settings", "profile"),

                spacing="2",
                padding=rx.cond(AppState.sidebar_collapsed, "10px 0", "10px 14px"),
                width="100%",
                align_items="center",
            ),

            rx.spacer(),

            # Bottom: Engine Health & User Profile
            rx.box(
                rx.vstack(
                    # Engine Badge
                    rx.cond(
                        ~AppState.sidebar_collapsed,
                        rx.box(
                            rx.hstack(
                                rx.box(width="7px", height="7px", background=GREEN,
                                       border_radius="50%", box_shadow=f"0 0 10px {GREEN}"),
                                rx.text("Engine Online", font_size="11.5px", color=GREEN, font_weight="800"),
                                rx.spacer(),
                                rx.box(
                                    rx.text("v2.5", font_size="9.5px", color="#94a3b8", font_family=MONO, font_weight="700"),
                                    padding="1px 5px", background="rgba(255,255,255,0.05)", border_radius="4px",
                                ),
                                width="100%", align="center",
                            ),
                            padding="8px 12px",
                            background="rgba(34, 197, 94, 0.08)",
                            border="1px solid rgba(34, 197, 94, 0.2)",
                            border_radius="10px",
                            width="100%",
                            margin_bottom="12px",
                        ),
                        rx.box(),
                    ),
                    # User Avatar & Info
                    rx.hstack(
                        user_avatar("40px", "14px"),
                        rx.cond(
                            ~AppState.sidebar_collapsed,
                            rx.vstack(
                                rx.text(AuthState.user_name, font_size="13px", color="#ffffff",
                                        font_weight="700", line_height="1.2"),
                                rx.text(AuthState.user_email, font_size="10.5px", color="#64748b",
                                        line_height="1.2", max_width="140px", overflow="hidden", text_overflow="ellipsis"),
                                spacing="0", align_items="start", flex="1",
                            ),
                            rx.box(),
                        ),
                        spacing="2",
                        align="center",
                        justify="center",
                        width="100%",
                        cursor="pointer",
                        on_click=AppState.go_tab("profile"),
                    ),
                    # Sign Out Button
                    rx.button(
                        rx.hstack(
                            rx.html(NAV_ICONS["signout"]),
                            rx.cond(~AppState.sidebar_collapsed, rx.text("Sign Out", font_size="12px", font_weight="600"), rx.box()),
                            spacing="2",
                            align="center",
                            justify="center",
                        ),
                        on_click=AuthState.logout,
                        background="rgba(239, 68, 68, 0.08)",
                        border="1px solid rgba(239, 68, 68, 0.2)",
                        color="#f87171",
                        border_radius="10px",
                        cursor="pointer",
                        height="40px",
                        width=rx.cond(AppState.sidebar_collapsed, "40px", "100%"),
                        padding=rx.cond(AppState.sidebar_collapsed, "0", "6px 12px"),
                        margin_top="10px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        _hover={"background": "rgba(239, 68, 68, 0.15)", "color": "#ef4444"},
                        transition="all 0.15s ease",
                    ),
                    spacing="1",
                    align_items="center",
                    width="100%",
                ),
                padding=rx.cond(AppState.sidebar_collapsed, "14px 0", "16px"),
                display="flex",
                align_items="center",
                justify_content="center",
                style={"border-top": "1px solid rgba(255, 255, 255, 0.08)"},
                width="100%",
            ),
            spacing="0", height="100vh", align_items="center", width="100%",
        ),
        width=rx.cond(AppState.sidebar_collapsed, "70px", "250px"),
        height="100vh",
        max_height="100vh",
        background="#060c18",
        flex_shrink="0",
        position="sticky",
        top="0",
        left="0",
        overflow="hidden",
        z_index="100",
        transition="width 0.22s cubic-bezier(0.4, 0, 0.2, 1)",
        style={"border-right": "1px solid rgba(255, 255, 255, 0.08)"},
    )


# ── Pages ────────────────────────────────────────────────────────────────────

def dashboard_page():
    return rx.vstack(
        # Dashboard Header
        rx.hstack(
            rx.vstack(
                rx.text("Financial Intelligence Dashboard", font_size="28px", font_weight="900",
                        color=TEXT, letter_spacing="-0.025em"),
                rx.text("Real-time telemetry, semantic vector context, and statistical overview", font_size="13.5px", color=MUTED),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                AppState.has_data,
                rx.hstack(
                    rx.box(
                        rx.hstack(
                            rx.text("PORTFOLIO RISK", font_size="10px", color="#64748b", font_weight="800", letter_spacing="0.1em", font_family=MONO),
                            risk_badge(AppState.risk_score),
                            spacing="2", align="center",
                        ),
                        padding="6px 12px",
                        background="rgba(15, 23, 42, 0.6)",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                        border_radius="10px",
                    ),
                    rx.box(
                        rx.hstack(
                            rx.box(width="6px", height="6px", border_radius="50%", background=RED),
                            rx.text(AppState.anomaly_count.to_string() + " ANOMALIES",
                                    font_size="10.5px", font_weight="800", color=RED, letter_spacing="0.1em", font_family=MONO),
                            spacing="2", align="center",
                        ),
                        padding="6px 12px",
                        background="rgba(239, 68, 68, 0.1)",
                        border="1px solid rgba(239, 68, 68, 0.25)",
                        border_radius="10px",
                    ),
                    spacing="3", align="center",
                ),
                rx.box(),
            ),
            width="100%", margin_bottom="24px", align="center",
        ),
        rx.cond(
            AppState.has_data,
            rx.vstack(
                # Top 4 KPI Metrics
                rx.hstack(
                    stat_card("TOTAL SPENT",     AppState.total_spent_display, "₹", CYAN,  NAV_ICONS["dashboard"]),
                    stat_card("TRANSACTIONS",    AppState.tx_count.to_string(),    "#", PURP,  NAV_ICONS["transactions"]),
                    stat_card("AVG TRANSACTION", AppState.avg_spent_display,   "₹", GREEN, NAV_ICONS["insights"]),
                    stat_card("TOP CATEGORY",    AppState.top_category,            "",  AMBER, NAV_ICONS["anomalies"]),
                    spacing="4", width="100%", flex_wrap="wrap",
                ),
                # Middle Row: Category Breakdown + AI Insights
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            sh("Spending Breakdown", "Category distribution"),
                            pbar("Food & Dining",       AppState.food_pct,          AMBER),
                            pbar("Shopping & Retail",   AppState.shopping_pct,      PURP),
                            pbar("Transport & Commute", AppState.transport_pct,     CYAN),
                            pbar("Entertainment",       AppState.entertainment_pct, "#ec4899"),
                            spacing="4", width="100%",
                        ),
                        padding="24px",
                        background="rgba(11, 18, 33, 0.75)",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                        border_radius="18px",
                        box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                        flex="1.2",
                    ),
                    rx.box(
                        rx.vstack(
                            sh("Latest AI Analysis", "From Gemini Intelligence Engine"),
                            rx.cond(
                                AppState.risk_level != "",
                                rx.vstack(
                                    rx.hstack(rx.text("Risk Assessment:", font_size="12px", color=MUTED, font_weight="700"),
                                              risk_badge(AppState.risk_level), spacing="2", align="center"),
                                    rx.box(rx.text(AppState.main_issue, font_size="13.5px", color=TEXT, line_height="1.7"),
                                           padding="14px", background="#070e1e", border_radius="10px", width="100%",
                                           border="1px solid rgba(0, 212, 255, 0.25)", style={"border-left": f"4px solid {CYAN}"}),
                                    rx.button(
                                        rx.hstack(
                                            rx.text("Open Full AI Insights", font_weight="700", font_size="13px"),
                                            rx.text("→", font_size="14px"),
                                            spacing="2", align="center",
                                        ),
                                        on_click=AppState.go_tab("insights"),
                                        background="rgba(0, 212, 255, 0.1)",
                                        color=CYAN,
                                        border="1px solid rgba(0, 212, 255, 0.3)",
                                        border_radius="8px",
                                        padding="10px 16px",
                                        cursor="pointer",
                                        _hover={"background": "rgba(0, 212, 255, 0.2)"},
                                    ),
                                    spacing="3", width="100%",
                                ),
                                rx.vstack(
                                    rx.box(
                                        rx.html(NAV_ICONS["insights"]),
                                        padding="12px",
                                        background="rgba(0, 212, 255, 0.1)",
                                        border="1px solid rgba(0, 212, 255, 0.25)",
                                        border_radius="50%",
                                        color=CYAN,
                                    ),
                                    rx.text("No query analyzed yet", font_size="14px", color="#f8fafc", text_align="center", font_weight="700"),
                                    rx.text("Run a statistical RAG analysis to generate recommendations.", font_size="12px", color=MUTED, text_align="center"),
                                    rx.button(
                                        "Explore AI Insights →",
                                        on_click=AppState.go_tab("insights"),
                                        background="linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)",
                                        color="#ffffff",
                                        font_size="13px",
                                        font_weight="700",
                                        cursor="pointer",
                                        border="none",
                                        border_radius="8px",
                                        padding="10px 18px",
                                        margin_top="6px",
                                    ),
                                    spacing="2", align="center", padding="16px", width="100%",
                                ),
                            ),
                            width="100%",
                        ),
                        padding="24px",
                        background="rgba(11, 18, 33, 0.75)",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                        border_radius="18px",
                        box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                        flex="1",
                    ),
                    spacing="4", width="100%", align="start", flex_wrap="wrap",
                ),
                # Bottom: Recent Transactions Table
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            sh("Recent Transactions", "Latest telemetry records"),
                            rx.spacer(),
                            rx.button(
                                "View All Ledger →",
                                on_click=AppState.go_tab("transactions"),
                                background="transparent",
                                color=CYAN,
                                border="none",
                                font_size="12.5px",
                                font_weight="700",
                                cursor="pointer",
                                _hover={"text_decoration": "underline"},
                            ),
                            width="100%", align="center",
                        ),
                        rx.vstack(
                            rx.foreach(
                                AppState.transactions,
                                lambda tx: rx.hstack(
                                    cat_pill(tx["category"]),
                                    rx.text(tx["merchant"], font_size="14px", color="#ffffff", font_weight="700", flex="1"),
                                    rx.text(tx["timestamp"], font_size="12px", color=MUTED, font_family=MONO),
                                    rx.text("₹" + tx["amount"].to_string(), font_size="15px", color=CYAN,
                                            font_weight="800", font_family=MONO, min_width="100px", text_align="right"),
                                    spacing="4", width="100%", padding="12px 14px",
                                    background="rgba(15, 23, 42, 0.4)",
                                    border="1px solid rgba(255, 255, 255, 0.04)",
                                    border_radius="10px",
                                    margin_bottom="6px",
                                    align="center",
                                    _hover={"background": "rgba(15, 23, 42, 0.8)", "border-color": "rgba(0, 212, 255, 0.2)"},
                                    transition="all 0.15s ease",
                                ),
                            ),
                            spacing="0", width="100%",
                        ),
                        width="100%",
                    ),
                    padding="24px",
                    background="rgba(11, 18, 33, 0.75)",
                    border="1px solid rgba(255, 255, 255, 0.08)",
                    border_radius="18px",
                    box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                spacing="5", width="100%",
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
        rx.hstack(
            rx.vstack(
                rx.text("AI Financial Intelligence Engine", font_size="28px", font_weight="900",
                        color="#ffffff", letter_spacing="-0.025em"),
                rx.text("Deep vector search  ·  Statistical aggregations  ·  Gemini 2.5 Flash reasoning",
                        font_size="13.5px", color="#94a3b8"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.box(
                rx.hstack(
                    rx.box(width="8px", height="8px", border_radius="50%", background=CYAN,
                           box_shadow=f"0 0 10px {CYAN}"),
                    rx.text("RAG ONNX ACTIVE", font_size="11px", font_weight="800",
                            color=CYAN, letter_spacing="0.1em", font_family=MONO),
                    spacing="2", align="center",
                ),
                padding="8px 16px",
                background="rgba(0, 212, 255, 0.08)",
                border="1px solid rgba(0, 212, 255, 0.25)",
                border_radius="12px",
            ),
            width="100%", margin_bottom="20px", align="center",
        ),
        # Interactive Query Box
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("QUERY THE INTELLIGENCE ENGINE", font_size="11px", color="#64748b",
                            font_weight="800", letter_spacing="0.12em", font_family=MONO),
                    rx.spacer(),
                    rx.text("Enter natural language prompt", font_size="11px", color="#64748b"),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="e.g. 'Analyze my spending risk' · 'Where am I overspending?' · 'How to save ₹5000 this month?'",
                        on_change=AppState.set_question,
                        value=AppState.question,
                        background="rgba(5, 10, 24, 0.8)",
                        border="1px solid rgba(255, 255, 255, 0.12)",
                        border_radius="12px",
                        height="52px",
                        font_size="14.5px",
                        color="#ffffff",
                        padding_x="18px",
                        flex="1",
                        style={"outline": "none"},
                        _focus={"border-color": CYAN, "box-shadow": f"0 0 0 1px {CYAN}"},
                        _placeholder={"color": "#64748b"},
                    ),
                    rx.button(
                        rx.cond(
                            AppState.is_loading,
                            rx.hstack(
                                rx.spinner(color="#ffffff", size="2"),
                                rx.text("Reasoning…", font_size="13.5px", font_weight="700"),
                                spacing="2", align="center",
                            ),
                            rx.hstack(
                                rx.html("""<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path></svg>"""),
                                rx.text("Analyze", font_size="14px", font_weight="700"),
                                spacing="2", align="center",
                            ),
                        ),
                        on_click=AppState.run_analysis,
                        background=f"linear-gradient(135deg, {PURP}, #4338ca)",
                        color="white",
                        border_radius="12px",
                        height="52px",
                        padding="0 28px",
                        cursor="pointer",
                        border="1px solid rgba(255, 255, 255, 0.15)",
                        box_shadow=f"0 8px 24px {PURP}44",
                        _hover={"opacity": 0.9, "transform": "translateY(-1px)"},
                        disabled=AppState.is_loading,
                        transition="all 0.15s ease",
                    ),
                    spacing="3", width="100%", align="center",
                ),
                # Suggested Prompt Chips
                rx.hstack(
                    rx.text("Try asking:", font_size="11.5px", color="#64748b", font_weight="600"),
                    *[
                        rx.box(
                            rx.text(q, font_size="11.5px", color="#38bdf8", font_weight="600"),
                            padding="5px 12px",
                            background="rgba(56, 189, 248, 0.08)",
                            border="1px solid rgba(56, 189, 248, 0.2)",
                            border_radius="8px",
                            cursor="pointer",
                            transition="all 0.15s ease",
                            _hover={"background": "rgba(56, 189, 248, 0.16)", "border-color": "#38bdf8"},
                            on_click=AppState.set_question(q),
                        )
                        for q in [
                            "Analyze my overall spending risk",
                            "Where am I overspending?",
                            "Is there unusual activity?",
                            "Break down my food expenses",
                        ]
                    ],
                    spacing="2", flex_wrap="wrap", align="center", margin_top="6px",
                ),
                spacing="3", width="100%",
            ),
            padding="24px",
            background="rgba(11, 18, 33, 0.75)",
            border="1px solid rgba(255, 255, 255, 0.08)",
            border_radius="18px",
            box_shadow="0 16px 40px rgba(0,0,0,0.4)",
            width="100%",
        ),
        # Error state if any
        rx.cond(
            AppState.analysis_error != "",
            rx.box(
                rx.text(AppState.analysis_error, font_size="13px", color="#f87171", font_weight="600"),
                padding="14px 20px", background="rgba(239, 68, 68, 0.1)",
                border="1px solid rgba(239, 68, 68, 0.3)", border_radius="12px", width="100%",
            ),
            rx.box(),
        ),
        # Analysis Output Results
        rx.cond(
            AppState.risk_level != "",
            rx.vstack(
                # Synthesis Banner
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            rx.text("PORTFOLIO RISK EVALUATION", font_size="10px", color="#64748b",
                                    font_weight="800", letter_spacing="0.1em", font_family=MONO),
                            risk_badge(AppState.risk_level),
                            spacing="2", align_items="start",
                        ),
                        rx.box(style={"border-left": "1px solid rgba(255, 255, 255, 0.1)"}, height="48px", margin_x="24px"),
                        rx.vstack(
                            rx.text("PRIMARY SYNTHESIS & FINDING", font_size="10px", color="#64748b",
                                    font_weight="800", letter_spacing="0.1em", font_family=MONO),
                            rx.text(AppState.main_issue, font_size="14.5px", color="#ffffff",
                                    line_height="1.6", font_weight="500"),
                            spacing="1", align_items="start", flex="1",
                        ),
                        spacing="0", width="100%", align="center",
                    ),
                    padding="22px 26px",
                    background="rgba(15, 23, 42, 0.75)",
                    border="1px solid rgba(255, 255, 255, 0.1)",
                    border_radius="18px",
                    box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                # Two Column Grid: Context & Action Plan
                rx.hstack(
                    # Left: Retrieved FAISS Vectors
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("RETRIEVED CONTEXT", font_size="10px", color="#64748b",
                                        font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                rx.spacer(),
                                rx.box(
                                    rx.text("FAISS · TOP 5", font_size="9.5px", color=CYAN, font_weight="800", font_family=MONO),
                                    padding="3px 8px", background="rgba(0, 212, 255, 0.1)",
                                    border="1px solid rgba(0, 212, 255, 0.25)", border_radius="6px",
                                ),
                                width="100%", align="center",
                            ),
                            rx.text("Dense 384-dim semantic matches retrieved locally via ONNX FastEmbed",
                                    font_size="11.5px", color="#94a3b8", margin_bottom="12px"),
                            rx.vstack(
                                rx.foreach(
                                    AppState.retrieved_context,
                                    lambda ctx: rx.box(
                                        rx.text(ctx, font_size="11.5px", color="#38bdf8", font_family=MONO, line_height="1.6"),
                                        padding="10px 14px",
                                        background="rgba(6, 18, 38, 0.8)",
                                        border="1px solid rgba(56, 189, 248, 0.2)",
                                        border_left="3px solid #38bdf8",
                                        border_radius="0 10px 10px 0",
                                        margin_bottom="8px",
                                        width="100%",
                                    ),
                                ),
                                spacing="0", width="100%",
                            ),
                            spacing="0", width="100%", align_items="start",
                        ),
                        padding="24px",
                        background="rgba(11, 18, 33, 0.75)",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                        border_radius="18px",
                        box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                        flex="1",
                        min_width="280px",
                    ),
                    # Right: Key Observations & Action Plan
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("KEY OBSERVATIONS", font_size="10px", color="#64748b",
                                        font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                rx.spacer(),
                                rx.box(
                                    rx.text("Gemini 2.5 Flash", font_size="9.5px", color=PURP, font_weight="800", font_family=MONO),
                                    padding="3px 8px", background=f"{PURP}18",
                                    border=f"1px solid {PURP}44", border_radius="6px",
                                ),
                                width="100%", align="center",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    AppState.key_observations,
                                    lambda obs: rx.hstack(
                                        rx.box(
                                            rx.text("◈", font_size="11px", color=CYAN, font_weight="900"),
                                            min_width="20px",
                                        ),
                                        rx.text(obs, font_size="13px", color="#ffffff", line_height="1.6"),
                                        spacing="2", align="start", width="100%",
                                    ),
                                ),
                                spacing="3", width="100%", margin_bottom="20px",
                            ),
                            rx.hstack(
                                rx.text("RECOMMENDED ACTIONS", font_size="10px", color="#64748b",
                                        font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                width="100%", align="center",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    AppState.recommended_actions,
                                    lambda act: rx.hstack(
                                        rx.box(
                                            rx.text("✓", font_size="12px", color=GREEN, font_weight="900"),
                                            min_width="20px",
                                        ),
                                        rx.text(act, font_size="13px", color="#cbd5e1", line_height="1.6"),
                                        spacing="2", align="start", width="100%",
                                    ),
                                ),
                                spacing="3", width="100%",
                            ),
                            spacing="3", align_items="start", width="100%",
                        ),
                        padding="24px",
                        background="rgba(11, 18, 33, 0.75)",
                        border="1px solid rgba(255, 255, 255, 0.08)",
                        border_radius="18px",
                        box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                        flex="1.3",
                        min_width="280px",
                    ),
                    spacing="4", width="100%", align="start", flex_wrap="wrap",
                ),
                spacing="4", width="100%",
            ),
            rx.box(),
        ),
        spacing="5", width="100%", padding_bottom="40px",
    )


def anomalies_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Statistical Outlier & Anomaly Detection", font_size="28px",
                        font_weight="900", color="#ffffff", letter_spacing="-0.025em"),
                rx.text("Standard normal distribution z-score (±2.0σ threshold) outlier scanner",
                        font_size="13.5px", color="#94a3b8"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                AppState.anomaly_count > 0,
                rx.box(
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", background=RED,
                               box_shadow=f"0 0 10px {RED}"),
                        rx.text(AppState.anomaly_count.to_string() + " ANOMALIES FLAGGED",
                                font_size="11px", font_weight="800", color=RED,
                                letter_spacing="0.1em", font_family=MONO),
                        spacing="2", align="center",
                    ),
                    padding="8px 16px",
                    background="rgba(239, 68, 68, 0.1)",
                    border="1px solid rgba(239, 68, 68, 0.3)",
                    border_radius="12px",
                ),
                rx.box(
                    rx.hstack(
                        rx.box(width="8px", height="8px", border_radius="50%", background=GREEN,
                               box_shadow=f"0 0 10px {GREEN}"),
                        rx.text("ALL METRICS NORMAL", font_size="11px", font_weight="800",
                                color=GREEN, letter_spacing="0.1em", font_family=MONO),
                        spacing="2", align="center",
                    ),
                    padding="8px 16px",
                    background="rgba(34, 197, 94, 0.1)",
                    border="1px solid rgba(34, 197, 94, 0.25)",
                    border_radius="12px",
                ),
            ),
            width="100%", margin_bottom="20px", align="center",
        ),
        rx.cond(
            AppState.has_data,
            rx.cond(
                AppState.anomalies.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.anomalies,
                        lambda an: rx.box(
                            rx.hstack(
                                rx.box(
                                    rx.html("""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""),
                                    padding="12px", background="rgba(239, 68, 68, 0.1)",
                                    border="1px solid rgba(239, 68, 68, 0.25)", border_radius="10px",
                                ),
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(an["merchant"], font_size="16px", font_weight="800", color="#ffffff"),
                                        cat_pill(an["category"]),
                                        spacing="2", align="center",
                                    ),
                                    rx.text(an["timestamp"], font_size="11.5px", color="#94a3b8", font_family=MONO),
                                    spacing="1", align_items="start", flex="1",
                                ),
                                rx.vstack(
                                    rx.text("₹" + an["amount"].to_string(), font_size="18px", font_weight="900",
                                            color=RED, font_family=MONO),
                                    rx.text("Z-Score: " + an["z_score"].to_string() + "σ", font_size="11px",
                                            color="#f87171", font_family=MONO, font_weight="700"),
                                    spacing="0", align_items="end",
                                ),
                                spacing="4", width="100%", align="center",
                            ),
                            padding="20px 24px",
                            background="rgba(15, 23, 42, 0.65)",
                            border="1px solid rgba(239, 68, 68, 0.25)",
                            border_radius="16px",
                            box_shadow="0 12px 30px rgba(0,0,0,0.35)",
                            width="100%",
                            margin_bottom="12px",
                        ),
                    ),
                    spacing="0", width="100%",
                ),
                rx.box(
                    rx.vstack(
                        rx.html("""<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>"""),
                        rx.text("No Anomalies Detected", font_size="16px", font_weight="800", color="#ffffff"),
                        rx.text("All transaction amounts fall comfortably within statistical normalcy (±2σ)",
                                font_size="13px", color="#94a3b8", text_align="center"),
                        spacing="3", align="center", padding="60px",
                    ),
                    padding="30px",
                    background="rgba(11, 18, 33, 0.7)",
                    border="1px solid rgba(255, 255, 255, 0.08)",
                    border_radius="18px",
                    width="100%",
                ),
            ),
            empty_state("Add transactions to run anomaly detection"),
        ),
        spacing="4", width="100%", padding_bottom="40px", on_mount=AppState.load_anomalies,
    )


def add_page():
    return rx.vstack(
        rx.vstack(
            rx.text("Data Ingestion", font_size="28px", font_weight="900", color=TEXT, letter_spacing="-0.025em"),
            rx.text("Stream financial telemetry and transactions into the live FAISS vector index & SQLite store", font_size="13.5px", color=MUTED),
            spacing="1", align_items="start", margin_bottom="24px",
        ),
        rx.hstack(
            # Quick Add Card
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.html("""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>"""),
                            padding="8px", background="rgba(124, 58, 237, 0.12)", border="1px solid rgba(124, 58, 237, 0.3)", border_radius="10px",
                        ),
                        rx.vstack(
                            rx.text("QUICK SIMULATION", font_size="10.5px", color="#7c3aed", font_weight="800", letter_spacing="0.14em", font_family=MONO),
                            rx.text("Auto-generate a realistic transaction", font_size="15px", color=TEXT, font_weight="700"),
                            spacing="0", align_items="start",
                        ),
                        spacing="3", align="center",
                    ),
                    rx.text("Randomly generates simulated merchant transactions (Zomato, Uber, Apple, Swiggy, etc.) and indexes them in real-time.",
                            font_size="12.5px", color="#94a3b8", line_height="1.6"),
                    rx.button(
                        rx.hstack(
                            rx.html("""<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>"""),
                            rx.text("Generate Random Transaction", font_weight="700", font_size="13.5px"),
                            spacing="2", align="center",
                        ),
                        on_click=AppState.add_random,
                        background="linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
                        color="white", border_radius="10px",
                        padding="14px 20px", cursor="pointer", width="100%",
                        box_shadow="0 4px 18px rgba(124, 58, 237, 0.35)",
                        _hover={"transform": "translateY(-1px)", "box_shadow": "0 8px 24px rgba(124, 58, 237, 0.5)"},
                        transition="all 0.2s ease",
                    ),
                    rx.cond(
                        AppState.add_status != "",
                        rx.box(
                            rx.text(AppState.add_status, font_size="12.5px", font_weight="600",
                                    font_family=MONO, color=rx.cond(AppState.add_ok, GREEN, RED)),
                            padding="10px 14px",
                            background=rx.cond(AppState.add_ok, "rgba(16, 185, 129, 0.1)", "rgba(239, 68, 68, 0.1)"),
                            border=rx.cond(AppState.add_ok, "1px solid rgba(16, 185, 129, 0.25)", "1px solid rgba(239, 68, 68, 0.25)"),
                            border_radius="10px", width="100%", text_align="center",
                        ),
                        rx.box(),
                    ),
                    spacing="4", width="100%",
                ),
                padding="24px",
                background="rgba(11, 18, 33, 0.7)",
                border="1px solid rgba(255, 255, 255, 0.08)",
                border_radius="18px",
                flex="1",
                box_shadow="0 16px 40px rgba(0,0,0,0.4)",
            ),
            # Custom Transaction Card
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.html("""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>"""),
                            padding="8px", background="rgba(16, 185, 129, 0.12)", border="1px solid rgba(16, 185, 129, 0.3)", border_radius="10px",
                        ),
                        rx.vstack(
                            rx.text("MANUAL ENTRY", font_size="10.5px", color="#10b981", font_weight="800", letter_spacing="0.14em", font_family=MONO),
                            rx.text("Custom Transaction Data", font_size="15px", color=TEXT, font_weight="700"),
                            spacing="0", align_items="start",
                        ),
                        spacing="3", align="center",
                    ),
                    rx.vstack(
                        rx.text("MERCHANT NAME", font_size="10.5px", color="#64748b", font_weight="700", letter_spacing="0.1em", font_family=MONO),
                        rx.input(
                            placeholder="e.g. Starbucks, Amazon, Netflix",
                            on_change=AppState.set_custom_merchant,
                            value=AppState.custom_merchant,
                            background="#070e1e",
                            border="1.5px solid #1a2f50",
                            border_radius="10px",
                            color="#f8fafc",
                            font_size="14px",
                            height="44px",
                            padding="0 14px",
                            width="100%",
                            _focus={"border": "1.5px solid #00d4ff", "box-shadow": "0 0 0 3px rgba(0, 212, 255, 0.15)"},
                            _placeholder={"color": "#475569"},
                        ),
                        spacing="1", width="100%", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("CATEGORY", font_size="10.5px", color="#64748b", font_weight="700", letter_spacing="0.1em", font_family=MONO),
                        rx.select(
                            ["Food", "Shopping", "Transport", "Entertainment", "Healthcare", "Other"],
                            on_change=AppState.set_custom_category,
                            value=AppState.custom_category,
                            background="#070e1e",
                            border="1.5px solid #1a2f50",
                            border_radius="10px",
                            color="#f8fafc",
                            font_size="14px",
                            height="44px",
                            width="100%",
                            padding="0 14px",
                            _focus={"border": "1.5px solid #00d4ff"},
                        ),
                        spacing="1", width="100%", align_items="start",
                    ),
                    rx.vstack(
                        rx.text("AMOUNT (₹)", font_size="10.5px", color="#64748b", font_weight="700", letter_spacing="0.1em", font_family=MONO),
                        rx.input(
                            placeholder="e.g. 750.00",
                            on_change=AppState.set_custom_amount,
                            value=AppState.custom_amount,
                            background="#070e1e",
                            border="1.5px solid #1a2f50",
                            border_radius="10px",
                            color="#f8fafc",
                            font_size="14px",
                            height="44px",
                            padding="0 14px",
                            width="100%",
                            _focus={"border": "1.5px solid #00d4ff", "box-shadow": "0 0 0 3px rgba(0, 212, 255, 0.15)"},
                            _placeholder={"color": "#475569"},
                        ),
                        spacing="1", width="100%", align_items="start",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.html("""<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>"""),
                            rx.text("Add to Pipeline", font_weight="700", font_size="13.5px"),
                            spacing="2", align="center",
                        ),
                        on_click=AppState.add_custom,
                        background="linear-gradient(135deg, #10b981 0%, #059669 100%)",
                        color="white", border_radius="10px",
                        padding="14px 20px", cursor="pointer", width="100%",
                        box_shadow="0 4px 18px rgba(16, 185, 129, 0.3)",
                        _hover={"transform": "translateY(-1px)", "box_shadow": "0 8px 24px rgba(16, 185, 129, 0.45)"},
                        transition="all 0.2s ease",
                    ),
                    spacing="3", width="100%",
                ),
                padding="24px",
                background="rgba(11, 18, 33, 0.7)",
                border="1px solid rgba(255, 255, 255, 0.08)",
                border_radius="18px",
                flex="1",
                box_shadow="0 16px 40px rgba(0,0,0,0.4)",
            ),
            spacing="5", width="100%", align="start", flex_wrap="wrap",
        ),
        # Architecture Showcase Card
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("INTELLIGENCE ARCHITECTURE", font_size="11px", color=CYAN, font_weight="800", letter_spacing="0.14em", font_family=MONO),
                    rx.spacer(),
                    rx.text("End-to-End Pipeline Flow", font_size="11.5px", color=MUTED),
                    width="100%", align="center",
                ),
                rx.divider(color="rgba(255, 255, 255, 0.06)", margin_y="12px"),
                rx.hstack(
                    *[rx.hstack(
                        rx.box(
                            rx.vstack(
                                rx.box(
                                    rx.text(num, font_size="11px", font_weight="800", color=clr, font_family=MONO),
                                    padding="4px 8px", background="rgba(0,0,0,0.4)", border_radius="6px",
                                    border=f"1px solid {clr}44",
                                ),
                                rx.text(lbl, font_size="11px", color=clr, font_weight="800", text_align="center", letter_spacing="0.08em"),
                                rx.text(tech, font_size="10px", color="#94a3b8", text_align="center"),
                                spacing="1", align="center", min_width="95px",
                            ),
                            padding="12px 14px",
                            background="rgba(15, 23, 42, 0.5)",
                            border="1px solid rgba(255, 255, 255, 0.06)",
                            border_radius="12px",
                        ),
                        rx.text("→", font_size="16px", color="#475569") if i < 5 else rx.box(),
                        spacing="3", align="center",
                    ) for i, (num, lbl, tech, clr) in enumerate([
                        ("01","INGEST","Transaction",CYAN), ("02","EMBED","ONNX MiniLM",PURP),
                        ("03","INDEX","FAISS FlatL2",GREEN), ("04","PERSIST","SQLite DB",AMBER),
                        ("05","RETRIEVE","Vector Search",CYAN), ("06","REASON","Gemini Flash",RED),
                    ])],
                    spacing="0", justify="center", width="100%", flex_wrap="wrap",
                ),
                spacing="3", width="100%", align="center",
            ),
            padding="24px",
            background="rgba(11, 18, 33, 0.7)",
            border="1px solid rgba(255, 255, 255, 0.08)",
            border_radius="18px",
            width="100%",
            box_shadow="0 16px 40px rgba(0,0,0,0.4)",
        ),
        spacing="5", width="100%", padding_bottom="40px",
    )


def budgets_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Financial Budgets & Spending Limits", font_size="28px", font_weight="900",
                        color="#ffffff", letter_spacing="-0.025em"),
                rx.text("Category threshold tracking, automated spend forecasting, and savings telemetry",
                        font_size="13.5px", color="#94a3b8"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.button(
                "⚙ Customize Limits",
                on_click=AppState.open_budget_modal,
                background=f"linear-gradient(135deg, {CYAN}, #0284c7)",
                color="#000000",
                font_weight="800",
                font_size="13px",
                border_radius="10px",
                padding="10px 18px",
                cursor="pointer",
                _hover={"opacity": 0.9, "transform": "translateY(-1px)"},
                transition="all 0.15s ease",
            ),
            width="100%", margin_bottom="20px", align="center",
        ),
        # 3 Budget Summary Tiles (Dynamic)
        rx.hstack(
            stat_card("MONTHLY BUDGET", AppState.monthly_budget_display, "₹", CYAN, NAV_ICONS["budgets"]),
            stat_card("TOTAL UTILIZED", AppState.total_spent_display, "₹", PURP, NAV_ICONS["transactions"]),
            stat_card("REMAINING CAP", AppState.remaining_budget_display, "₹", GREEN, NAV_ICONS["dashboard"]),
            spacing="4", width="100%", margin_bottom="8px",
        ),
        # Category Progress Tracker Cards (Dynamic)
        rx.box(
            rx.vstack(
                rx.hstack(
                    sh("Active Category Allowances", "Real-time consumption vs your custom monthly targets"),
                    rx.spacer(),
                    rx.button(
                        "Edit Targets",
                        on_click=AppState.open_budget_modal,
                        background="rgba(255,255,255,0.06)",
                        color=CYAN,
                        font_size="11.5px",
                        font_weight="700",
                        border_radius="8px",
                        padding="4px 12px",
                        cursor="pointer",
                    ),
                    width="100%", align="center",
                ),
                rx.vstack(
                    pbar("Food & Dining (Spent: ₹" + AppState.food_spent_amt.to_string() + " / Cap: ₹" + AppState.food_budget_cap.to_string() + ")", AppState.food_pct, AMBER),
                    pbar("Shopping & Retail (Spent: ₹" + AppState.shopping_spent_amt.to_string() + " / Cap: ₹" + AppState.shopping_budget_cap.to_string() + ")", AppState.shopping_pct, PURP),
                    pbar("Transport & Commute (Spent: ₹" + AppState.transport_spent_amt.to_string() + " / Cap: ₹" + AppState.transport_budget_cap.to_string() + ")", AppState.transport_pct, CYAN),
                    pbar("Entertainment & OTT (Spent: ₹" + AppState.ent_spent_amt.to_string() + " / Cap: ₹" + AppState.ent_budget_cap.to_string() + ")", AppState.entertainment_pct, "#ec4899"),
                    spacing="4", width="100%", margin_top="10px",
                ),
                spacing="2", width="100%",
            ),
            padding="26px",
            background="rgba(11, 18, 33, 0.75)",
            border="1px solid rgba(255, 255, 255, 0.08)",
            border_radius="18px",
            box_shadow="0 16px 40px rgba(0,0,0,0.4)",
            width="100%",
        ),

        # Custom Budget Limits Dialog / Modal
        rx.cond(
            AppState.budget_modal_open,
            rx.box(
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Customize Financial Limits", font_size="20px", font_weight="900", color="#ffffff"),
                            rx.spacer(),
                            rx.box(
                                rx.text("✕", font_size="16px", color="#94a3b8", cursor="pointer"),
                                on_click=AppState.close_budget_modal,
                            ),
                            width="100%", align="center",
                        ),
                        rx.text("Set your monthly allowance and category spending caps (in ₹):", font_size="13px", color="#94a3b8"),
                        rx.cond(
                            AppState.budget_msg != "",
                            rx.text(AppState.budget_msg, font_size="12.5px", color=RED, font_weight="700"),
                            rx.box(),
                        ),
                        # Monthly Total Cap
                        rx.vstack(
                            rx.text("TOTAL MONTHLY BUDGET CAP (₹)", font_size="10.5px", color="#64748b", font_weight="800", font_family=MONO),
                            rx.input(
                                value=AppState.edit_monthly_cap,
                                on_change=AppState.set_edit_monthly_cap,
                                placeholder="e.g. 25000",
                                background="rgba(5, 10, 24, 0.8)",
                                border="1px solid rgba(255, 255, 255, 0.12)",
                                border_radius="10px",
                                height="44px",
                                color="#ffffff",
                                width="100%",
                            ),
                            spacing="1", width="100%", align_items="start",
                        ),
                        # 2 Column Category Caps
                        rx.hstack(
                            rx.vstack(
                                rx.text("FOOD & DINING (₹)", font_size="10.5px", color="#64748b", font_weight="800", font_family=MONO),
                                rx.input(
                                    value=AppState.edit_food_cap,
                                    on_change=AppState.set_edit_food_cap,
                                    placeholder="8000",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="44px",
                                    color="#ffffff",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            rx.vstack(
                                rx.text("SHOPPING (₹)", font_size="10.5px", color="#64748b", font_weight="800", font_family=MONO),
                                rx.input(
                                    value=AppState.edit_shopping_cap,
                                    on_change=AppState.set_edit_shopping_cap,
                                    placeholder="10000",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="44px",
                                    color="#ffffff",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            spacing="3", width="100%",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("TRANSPORT (₹)", font_size="10.5px", color="#64748b", font_weight="800", font_family=MONO),
                                rx.input(
                                    value=AppState.edit_transport_cap,
                                    on_change=AppState.set_edit_transport_cap,
                                    placeholder="4000",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="44px",
                                    color="#ffffff",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            rx.vstack(
                                rx.text("ENTERTAINMENT (₹)", font_size="10.5px", color="#64748b", font_weight="800", font_family=MONO),
                                rx.input(
                                    value=AppState.edit_ent_cap,
                                    on_change=AppState.set_edit_ent_cap,
                                    placeholder="3000",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="44px",
                                    color="#ffffff",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            spacing="3", width="100%",
                        ),
                        # Action Buttons
                        rx.hstack(
                            rx.button(
                                "Cancel",
                                on_click=AppState.close_budget_modal,
                                background="transparent",
                                color="#94a3b8",
                                font_weight="600",
                                border_radius="10px",
                                height="44px",
                                padding="0 18px",
                                cursor="pointer",
                                _hover={"color": "#ffffff"},
                            ),
                            rx.spacer(),
                            rx.button(
                                "Save Custom Targets",
                                on_click=AppState.save_custom_budgets,
                                background=f"linear-gradient(135deg, {CYAN}, #0284c7)",
                                color="#000000",
                                font_weight="800",
                                font_size="13px",
                                border_radius="10px",
                                height="44px",
                                padding="0 22px",
                                cursor="pointer",
                                _hover={"opacity": 0.9},
                            ),
                            width="100%", align="center", margin_top="10px",
                        ),
                        spacing="4", width="100%", align_items="start",
                    ),
                    padding="30px",
                    background="#0b1324",
                    border="1px solid rgba(0, 212, 255, 0.3)",
                    border_radius="20px",
                    box_shadow="0 24px 60px rgba(0,0,0,0.8)",
                    max_width="480px",
                    width="92vw",
                ),
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                background="rgba(3, 7, 18, 0.75)",
                backdrop_filter="blur(8px)",
                z_index="999",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.box(),
        ),

        spacing="5", width="100%", padding_bottom="40px", on_mount=AppState.on_page_load,
    )


def notes_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Financial Event Notes & Memos", font_size="28px", font_weight="900",
                        color="#ffffff", letter_spacing="-0.025em"),
                rx.text("Document key transaction reasons, tax annotations, and expense memos",
                        font_size="13.5px", color="#94a3b8"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.box(
                rx.text("Auto-saved to Local SQLite", font_size="11px", color=GREEN, font_weight="800", font_family=MONO),
                padding="6px 14px", background="rgba(34, 197, 94, 0.1)",
                border="1px solid rgba(34, 197, 94, 0.25)", border_radius="10px",
            ),
            width="100%", margin_bottom="20px", align="center",
        ),
        # New Note Creator Card
        rx.box(
            rx.vstack(
                sh("Create New Financial Memo", "Attach notes to major spending events or milestones"),
                rx.hstack(
                    rx.input(
                        placeholder="Note Title (e.g. 'Flipkart Laptop Purchase EMI', 'Apollo Medical Claim')",
                        value=AuthState.note_title,
                        on_change=AuthState.set_note_title,
                        background="rgba(5, 10, 24, 0.8)",
                        border="1px solid rgba(255, 255, 255, 0.12)",
                        border_radius="10px",
                        height="48px",
                        font_size="14px",
                        color="#ffffff",
                        padding_x="16px",
                        flex="2",
                        _placeholder={"color": "#64748b"},
                    ),
                    rx.select(
                        ["General", "Tax Deduction", "Major Purchase", "Subscription", "Reimbursement", "Medical"],
                        value=AuthState.note_tag,
                        on_change=AuthState.set_note_tag,
                        background="rgba(5, 10, 24, 0.8)",
                        border="1px solid rgba(255, 255, 255, 0.12)",
                        border_radius="10px",
                        height="48px",
                        font_size="13px",
                        color="#ffffff",
                        flex="1",
                    ),
                    spacing="3", width="100%",
                ),
                rx.text_area(
                    placeholder="Enter detailed notes, invoice numbers, warranty details, or tax justification...",
                    value=AuthState.note_content,
                    on_change=AuthState.set_note_content,
                    background="rgba(5, 10, 24, 0.8)",
                    border="1px solid rgba(255, 255, 255, 0.12)",
                    border_radius="10px",
                    min_height="90px",
                    font_size="13.5px",
                    color="#ffffff",
                    padding="14px",
                    width="100%",
                    _placeholder={"color": "#64748b"},
                ),
                rx.hstack(
                    rx.cond(
                        AuthState.note_msg != "",
                        rx.text(AuthState.note_msg, font_size="12px", color=RED, font_weight="600"),
                        rx.box(),
                    ),
                    rx.spacer(),
                    rx.button(
                        "+ Save Memo",
                        on_click=AuthState.add_note,
                        background=f"linear-gradient(135deg, {CYAN}, #0284c7)",
                        color="#000000",
                        font_weight="800",
                        font_size="13px",
                        border_radius="10px",
                        padding="10px 24px",
                        cursor="pointer",
                        _hover={"opacity": 0.9, "transform": "translateY(-1px)"},
                        transition="all 0.15s ease",
                    ),
                    width="100%", align="center",
                ),
                spacing="3", width="100%",
            ),
            padding="24px",
            background="rgba(11, 18, 33, 0.75)",
            border="1px solid rgba(255, 255, 255, 0.08)",
            border_radius="18px",
            box_shadow="0 16px 40px rgba(0,0,0,0.4)",
            width="100%",
        ),
        # Saved Notes List
        rx.vstack(
            rx.cond(
                AuthState.notes.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AuthState.notes,
                        lambda n: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.box(
                                        rx.text(n["tag"], font_size="10.5px", font_weight="800", color=CYAN, font_family=MONO),
                                        padding="3px 10px", background="rgba(0, 212, 255, 0.1)",
                                        border="1px solid rgba(0, 212, 255, 0.25)", border_radius="6px",
                                    ),
                                    rx.text(n["title"], font_size="16px", font_weight="800", color="#ffffff", flex="1"),
                                    rx.text(n["created_at"], font_size="11.5px", color="#64748b", font_family=MONO),
                                    rx.button(
                                        "Delete",
                                        on_click=AuthState.remove_note(n["id"]),
                                        background="transparent",
                                        color="#f87171",
                                        border="none",
                                        font_size="11px",
                                        cursor="pointer",
                                        _hover={"text_decoration": "underline"},
                                    ),
                                    spacing="3", width="100%", align="center",
                                ),
                                rx.text(n["content"], font_size="13.5px", color="#cbd5e1", line_height="1.6"),
                                spacing="2", width="100%", align_items="start",
                            ),
                            padding="20px 24px",
                            background="rgba(15, 23, 42, 0.65)",
                            border="1px solid rgba(255, 255, 255, 0.08)",
                            border_radius="16px",
                            width="100%",
                            margin_bottom="12px",
                        ),
                    ),
                    spacing="0", width="100%",
                ),
                rx.box(
                    rx.vstack(
                        rx.html("""<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>"""),
                        rx.text("No Memos Created Yet", font_size="15px", font_weight="700", color="#94a3b8"),
                        rx.text("Keep track of tax exemptions, warranty receipts, and expense context.", font_size="12.5px", color="#64748b"),
                        spacing="2", align="center", padding="40px",
                    ),
                    padding="20px",
                    background="rgba(11, 18, 33, 0.5)",
                    border="1px solid rgba(255, 255, 255, 0.06)",
                    border_radius="16px",
                    width="100%",
                ),
            ),
            width="100%",
        ),
        spacing="5", width="100%", padding_bottom="40px", on_mount=AuthState.load_notes,
    )


def profile_page():
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("User Profile & Account Identity", font_size="28px", font_weight="900",
                        color="#ffffff", letter_spacing="-0.025em"),
                rx.text("Manage display identity, upload profile pictures, and review security telemetry",
                        font_size="13.5px", color="#94a3b8"),
                spacing="1", align_items="start",
            ),
            rx.spacer(),
            rx.box(
                rx.hstack(
                    rx.box(width="8px", height="8px", border_radius="50%", background=GREEN, box_shadow=f"0 0 10px {GREEN}"),
                    rx.text("SECURE STORAGE", font_size="10.5px", color=GREEN, font_weight="800", font_family=MONO),
                    spacing="2", align="center",
                ),
                padding="8px 14px", background="rgba(34, 197, 94, 0.1)",
                border="1px solid rgba(34, 197, 94, 0.25)", border_radius="10px",
            ),
            width="100%", margin_bottom="20px", align="center",
        ),
        rx.hstack(
            # Left: Unified Clickable Avatar Profile Card
            rx.box(
                rx.vstack(
                    rx.box(
                        rx.html(
                            """
                            <div style="position:relative; display:inline-block; cursor:pointer;" onclick="document.getElementById('native_avatar_input').click()">
                                <input type="file" id="native_avatar_input" accept="image/png, image/jpeg, image/webp" style="display:none;" onchange="
                                    const file = this.files[0];
                                    if (file) {
                                        const loader = document.getElementById('avatar_loading_indicator');
                                        if (loader) loader.style.display = 'flex';
                                        const reader = new FileReader();
                                        reader.onload = function(e) {
                                            const b64 = e.target.result;
                                            const bridgeInput = document.getElementById('avatar_bridge_input');
                                            if (bridgeInput) {
                                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                                nativeInputValueSetter.call(bridgeInput, b64);
                                                const ev = new Event('input', { bubbles: true });
                                                bridgeInput.dispatchEvent(ev);
                                            }
                                            setTimeout(() => {
                                                if (loader) loader.style.display = 'none';
                                            }, 400);
                                        };
                                        reader.readAsDataURL(file);
                                    }
                                " />
                                <div id="avatar_loading_indicator" style="display:none; position:absolute; top:0; left:0; width:100%; height:100%; border-radius:24px; background:rgba(6,12,24,0.85); backdrop-filter:blur(4px); z-index:20; align-items:center; justify-content:center; flex-direction:column; gap:6px;">
                                    <div style="width:28px; height:28px; border:3px solid rgba(0,212,255,0.2); border-top-color:#00d4ff; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
                                    <span style="font-size:10.5px; color:#00d4ff; font-weight:700; font-family:'Plus Jakarta Sans',sans-serif;">Uploading...</span>
                                </div>
                                <style>
                                @keyframes spin { to { transform: rotate(360deg); } }
                                </style>
                            </div>
                            """
                        ),
                        # Direct Clickable Photo Frame with overlay hover
                        rx.box(
                            rx.cond(
                                AuthState.avatar_url != "",
                                rx.box(
                                    rx.image(
                                        src=AuthState.avatar_url,
                                        width="120px",
                                        height="120px",
                                        border_radius="24px",
                                        object_fit="cover",
                                    ),
                                    rx.box(
                                        rx.html("""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>"""),
                                        position="absolute",
                                        bottom="8px",
                                        right="8px",
                                        padding="6px",
                                        background="rgba(0,0,0,0.8)",
                                        border_radius="50%",
                                        border="1px solid rgba(255,255,255,0.25)",
                                    ),
                                    position="relative",
                                ),
                                rx.vstack(
                                    rx.html("""<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>"""),
                                    rx.text("Click to Upload", font_size="11.5px", color=CYAN, font_weight="700"),
                                    spacing="2", align="center", justify="center", width="120px", height="120px",
                                ),
                            ),
                            cursor="pointer",
                            padding="4px",
                            border="2px dashed rgba(0, 212, 255, 0.4)",
                            border_radius="28px",
                            _hover={"border-color": CYAN, "box-shadow": "0 0 20px rgba(0, 212, 255, 0.3)", "transform": "scale(1.02)"},
                            transition="all 0.2s ease",
                            on_click=rx.call_script("document.getElementById('native_avatar_input').click()"),
                        ),
                        # Hidden input bridging client-side Base64 to Reflex State
                        rx.input(
                            id="avatar_bridge_input",
                            on_change=AuthState.set_avatar_b64,
                            style={"display": "none"},
                        ),
                        position="relative",
                    ),
                    rx.text(AuthState.user_name, font_size="20px", font_weight="900", color="#ffffff", margin_top="12px"),
                    rx.text("@" + AuthState.username, font_size="12px", color=CYAN, font_family=MONO, font_weight="700"),
                    rx.text(AuthState.user_email, font_size="11.5px", color="#64748b", font_family=MONO),
                    rx.hstack(
                        rx.button(
                            "Reset to Default Icon",
                            on_click=AuthState.reset_avatar,
                            background="transparent",
                            color="#f87171",
                            font_size="11px",
                            padding="4px 8px",
                            cursor="pointer",
                            _hover={"text_decoration": "underline"},
                        ),
                        spacing="2", align="center", margin_top="4px",
                    ),
                    rx.divider(color="rgba(255, 255, 255, 0.08)", margin_y="12px"),
                    # User stats badges
                    rx.vstack(
                        rx.hstack(
                            rx.text("Security Tier", font_size="11.5px", color="#94a3b8"),
                            rx.spacer(),
                            rx.text("AES-256 / SHA-256", font_size="11px", color=CYAN, font_family=MONO, font_weight="700"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Session Lifetime", font_size="11.5px", color="#94a3b8"),
                            rx.spacer(),
                            rx.text("30 Days (Active)", font_size="11px", color=GREEN, font_family=MONO, font_weight="700"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Vector DB Profile", font_size="11.5px", color="#94a3b8"),
                            rx.spacer(),
                            rx.text("FAISS Linked", font_size="11px", color=PURP, font_family=MONO, font_weight="700"),
                            width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                    spacing="1", align="center", width="100%",
                ),
                padding="26px",
                background="rgba(11, 18, 33, 0.75)",
                border="1px solid rgba(255, 255, 255, 0.08)",
                border_radius="18px",
                box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                width="310px",
            ),
            # Right: Edit Profile Form + Account Telemetry
            rx.vstack(
                rx.box(
                    rx.vstack(
                        sh("Edit Identity Details", "Update your personal credentials and public handle"),
                        rx.cond(
                            AuthState.profile_msg != "",
                            rx.box(
                                rx.text(AuthState.profile_msg, font_size="13px",
                                        color=rx.cond(AuthState.profile_ok, GREEN, RED), font_weight="700"),
                                padding="10px 16px",
                                background=rx.cond(AuthState.profile_ok, "rgba(34, 197, 94, 0.1)", "rgba(239, 68, 68, 0.1)"),
                                border=rx.cond(AuthState.profile_ok, "1px solid rgba(34, 197, 94, 0.25)", "1px solid rgba(239, 68, 68, 0.25)"),
                                border_radius="10px", width="100%",
                            ),
                            rx.box(),
                        ),
                        # First Name & Last Name Row
                        rx.hstack(
                            rx.vstack(
                                rx.text("FIRST NAME", font_size="10.5px", color="#64748b", font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                rx.input(
                                    value=AuthState.first_name,
                                    on_change=AuthState.set_first_name,
                                    placeholder="e.g. Nitanshu",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="48px",
                                    font_size="14px",
                                    color="#ffffff",
                                    padding_x="16px",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            rx.vstack(
                                rx.text("LAST NAME", font_size="10.5px", color="#64748b", font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                rx.input(
                                    value=AuthState.last_name,
                                    on_change=AuthState.set_last_name,
                                    placeholder="e.g. Tak",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="48px",
                                    font_size="14px",
                                    color="#ffffff",
                                    padding_x="16px",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            spacing="3", width="100%",
                        ),
                        # Username & Linked Email Row
                        rx.hstack(
                            rx.vstack(
                                rx.text("USERNAME", font_size="10.5px", color="#64748b", font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                rx.input(
                                    value=AuthState.username,
                                    on_change=AuthState.set_username,
                                    placeholder="e.g. nitanshutak",
                                    background="rgba(5, 10, 24, 0.8)",
                                    border="1px solid rgba(255, 255, 255, 0.12)",
                                    border_radius="10px",
                                    height="48px",
                                    font_size="14px",
                                    color="#ffffff",
                                    padding_x="16px",
                                    width="100%",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            rx.vstack(
                                rx.hstack(
                                    rx.text("LINKED EMAIL", font_size="10.5px", color="#64748b", font_weight="800", letter_spacing="0.1em", font_family=MONO),
                                    rx.box(
                                        rx.text("READ ONLY", font_size="9px", font_weight="800", color="#94a3b8", font_family=MONO),
                                        padding="1px 6px", background="rgba(255,255,255,0.06)", border_radius="4px",
                                    ),
                                    spacing="2", align="center",
                                ),
                                rx.box(
                                    rx.hstack(
                                        rx.text(AuthState.user_email, font_size="13.5px", color="#94a3b8", font_family=MONO),
                                        rx.spacer(),
                                        rx.html("""<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>"""),
                                        width="100%", align="center",
                                    ),
                                    height="48px",
                                    padding="0 16px",
                                    display="flex",
                                    align_items="center",
                                    background="rgba(15, 23, 42, 0.4)",
                                    border="1px solid rgba(255, 255, 255, 0.06)",
                                    border_radius="10px",
                                    width="100%",
                                    user_select="none",
                                    cursor="not-allowed",
                                ),
                                spacing="1", flex="1", align_items="start",
                            ),
                            spacing="3", width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "Save Profile Changes",
                                on_click=AuthState.save_profile,
                                background=f"linear-gradient(135deg, {PURP}, #4338ca)",
                                color="#ffffff",
                                font_weight="800",
                                font_size="13.5px",
                                border_radius="10px",
                                height="46px",
                                padding="0 26px",
                                cursor="pointer",
                                margin_top="10px",
                                box_shadow=f"0 8px 24px {PURP}44",
                                _hover={"opacity": 0.9, "transform": "translateY(-1px)"},
                                transition="all 0.15s ease",
                            ),
                            spacing="3", align="center",
                        ),
                        spacing="4", width="100%", align_items="start",
                    ),
                    padding="28px",
                    background="rgba(11, 18, 33, 0.75)",
                    border="1px solid rgba(255, 255, 255, 0.08)",
                    border_radius="18px",
                    box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                # Financial Account Telemetry Card
                rx.box(
                    rx.vstack(
                        sh("System & Telemetry Stats", "Active services linked to your profile"),
                        rx.hstack(
                            stat_card("TOTAL TRANSACTIONS", AppState.tx_count.to_string(), "#", PURP, NAV_ICONS["transactions"]),
                            stat_card("SAVED MEMOS", AuthState.notes.length().to_string(), "#", CYAN, NAV_ICONS["notes"]),
                            stat_card("OUTLIERS FLAGGED", AppState.anomaly_count.to_string(), "!", RED, NAV_ICONS["anomalies"]),
                            spacing="3", width="100%", flex_wrap="wrap",
                        ),
                        spacing="3", width="100%", align_items="start",
                    ),
                    padding="26px",
                    background="rgba(11, 18, 33, 0.75)",
                    border="1px solid rgba(255, 255, 255, 0.08)",
                    border_radius="18px",
                    box_shadow="0 16px 40px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                spacing="4", flex="1",
            ),
            spacing="5", width="100%", align="start", flex_wrap="wrap",
        ),
        spacing="5", width="100%", padding_bottom="40px", on_mount=AuthState.init_profile_fields,
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
                    rx.cond(AppState.active_tab == "budgets",      budgets_page(),      rx.box()),
                    rx.cond(AppState.active_tab == "notes",        notes_page(),        rx.box()),
                    rx.cond(AppState.active_tab == "insights",     insights_page(),     rx.box()),
                    rx.cond(AppState.active_tab == "anomalies",    anomalies_page(),    rx.box()),
                    rx.cond(AppState.active_tab == "add",          add_page(),          rx.box()),
                    rx.cond(AppState.active_tab == "profile",      profile_page(),      rx.box()),
                    padding="36px 44px",
                    flex="1",
                    height="100vh",
                    overflow_y="auto",
                    overflow_x="hidden",
                ),
                spacing="0", width="100%", height="100vh", align="start",
            ),
            overflow="hidden",
            height="100vh",
            width="100vw",
            background=BG,
            color=TEXT,
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
        from .auth_db import verify_email_token, get_user_by_id
        result = verify_email_token(token)   # returns user_id on success, None on failure
        if result:
            self.ok = True; self.msg = "Email verified!"
            # Send welcome email now that the account is confirmed
            try:
                u = get_user_by_id(result)
                if u:
                    from .email_service import send_welcome_email
                    send_welcome_email(u.email, u.name)
            except Exception:
                pass
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

app.add_page(reset_password_page,  route="/reset-password", on_load=AuthState.load_reset_page)