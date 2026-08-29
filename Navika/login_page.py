# finance_ai/login_page.py
import reflex as rx
from .auth_state import AuthState

# ─────────────────────────────────────────────────────────────────────────────
# VECTOR SVGS (NO EMOJIS)
# ─────────────────────────────────────────────────────────────────────────────
SVG_BOT = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="11" width="18" height="10" rx="3"></rect>
  <circle cx="12" cy="5" r="2"></circle>
  <path d="M12 7v4"></path>
  <line x1="8" y1="16" x2="8.01" y2="16"></line>
  <line x1="16" y1="16" x2="16.01" y2="16"></line>
</svg>"""

SVG_BOLT = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
</svg>"""

SVG_SHIELD = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
</svg>"""

SVG_LOCK = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
</svg>"""

SVG_CHECK = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>"""

# ─────────────────────────────────────────────────────────────────────────────
# STYLES & ANIMATIONS
# ─────────────────────────────────────────────────────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body {
  margin: 0;
  padding: 0;
  background: #030712;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #f1f5f9;
  min-height: 100vh;
  width: 100%;
}

@keyframes pulseGlow {
  0%, 100% { transform: scale(1); opacity: 0.4; }
  50% { transform: scale(1.15); opacity: 0.7; }
}

@keyframes floatCard {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

.glow-orb-cyan {
  position: fixed;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.18) 0%, rgba(124, 58, 237, 0.08) 50%, transparent 70%);
  filter: blur(100px);
  top: -150px;
  left: -150px;
  pointer-events: none;
  z-index: 0;
  animation: pulseGlow 14s ease-in-out infinite;
}

.glow-orb-purple {
  position: fixed;
  width: 550px;
  height: 550px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.22) 0%, rgba(16, 185, 129, 0.06) 50%, transparent 70%);
  filter: blur(100px);
  bottom: -150px;
  right: -100px;
  pointer-events: none;
  z-index: 0;
  animation: pulseGlow 12s ease-in-out infinite 3s;
}

.grid-bg-pattern {
  position: fixed;
  inset: 0;
  background-image: 
    linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

.custom-glass-panel {
  background: rgba(11, 18, 33, 0.82) !important;
  backdrop-filter: blur(28px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(28px) saturate(1.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.09) !important;
  border-radius: 20px !important;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

.bot-card-float {
  animation: floatCard 6s ease-in-out infinite;
}

.pill-stat-card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 14px 18px;
  transition: all 0.2s ease;
}

.pill-stat-card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateY(-2px);
}

/* Force pure white text and clean placeholder on all inputs */
input, input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus {
  -webkit-text-fill-color: #ffffff !important;
  -webkit-box-shadow: 0 0 0px 1000px #070e1e inset !important;
  color: #ffffff !important;
  caret-color: #00d4ff !important;
}

input::placeholder {
  -webkit-text-fill-color: #64748b !important;
  color: #64748b !important;
  opacity: 1 !important;
}
</style>"""


def _background():
    return rx.box(
        rx.html(CSS),
        rx.box(class_name="glow-orb-cyan"),
        rx.box(class_name="glow-orb-purple"),
        rx.box(class_name="grid-bg-pattern"),
        position="fixed",
        inset="0",
        z_index="0",
        pointer_events="none",
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEFT HERO SHOWCASE (BRAND, AI CORE BOT & METRICS)
# ─────────────────────────────────────────────────────────────────────────────

def _hero_section():
    return rx.vstack(
        # Brand Logo Header
        rx.hstack(
            rx.box(
                rx.text("◈", font_size="22px", color="#00d4ff", font_weight="900"),
                padding="6px 12px",
                background="rgba(0,212,255,0.12)",
                border="1px solid rgba(0,212,255,0.3)",
                border_radius="10px",
                box_shadow="0 0 16px rgba(0,212,255,0.2)",
            ),
            rx.vstack(
                rx.text("NAVIKA", font_size="22px", font_weight="900", letter_spacing="0.18em", color="#ffffff"),
                rx.text("AI FINANCIAL INTELLIGENCE PLATFORM", font_size="10px", color="#00d4ff", font_weight="700", letter_spacing="0.12em"),
                spacing="0",
                align_items="start",
            ),
            spacing="3",
            align="center",
            margin_bottom="12px",
        ),

        # Main Headline
        rx.vstack(
            rx.text(
                "Clarity over your finances with grounded AI.",
                font_size="34px",
                font_weight="800",
                color="#ffffff",
                line_height="1.2",
                letter_spacing="-0.025em",
            ),
            rx.text(
                "Sub-millisecond FAISS vector search and deterministic Gemini 2.5 Flash analysis — completely grounded on your actual data.",
                font_size="14.5px",
                color="#94a3b8",
                line_height="1.65",
            ),
            spacing="2",
            align_items="start",
            max_width="480px",
        ),

        # AI Assistant Showcase Card
        rx.box(
            rx.hstack(
                rx.box(
                    rx.html(SVG_BOT),
                    padding="12px",
                    background="rgba(0, 212, 255, 0.12)",
                    border="1px solid rgba(0, 212, 255, 0.35)",
                    border_radius="14px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Navika Autonomous Agent", font_size="14px", font_weight="700", color="#f8fafc"),
                        rx.box(
                            rx.hstack(
                                rx.box(width="6px", height="6px", border_radius="50%", background="#10b981"),
                                rx.text("Active", font_size="10.5px", color="#10b981", font_weight="700"),
                                spacing="1",
                                align="center",
                            ),
                            padding="2px 10px",
                            background="rgba(16,185,129,0.12)",
                            border="1px solid rgba(16,185,129,0.3)",
                            border_radius="12px",
                        ),
                        justify="between",
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        "\"Food delivery spending is up 28% this week. Anomaly flagged at Swiggy (₹1,450).\"",
                        font_size="12px",
                        color="#cbd5e1",
                        font_family="'JetBrains Mono', monospace",
                    ),
                    spacing="1",
                    align_items="start",
                    flex="1",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            padding="20px",
            background="rgba(15, 23, 42, 0.8)",
            border="1px solid rgba(0, 212, 255, 0.28)",
            border_radius="18px",
            width="100%",
            max_width="480px",
            class_name="bot-card-float",
            box_shadow="0 14px 40px rgba(0,0,0,0.5)",
            margin_top="12px",
        ),

        # Mini KPI Pill Row
        rx.hstack(
            # Stat 1
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.html(SVG_BOLT),
                        rx.text("FAISS RETRIEVAL", font_size="9.5px", color="#64748b", font_weight="700", font_family="'JetBrains Mono', monospace"),
                        align="center",
                        spacing="1",
                    ),
                    rx.text("< 1ms Latency", font_size="15px", font_weight="800", color="#00d4ff"),
                    spacing="0",
                    align_items="start",
                ),
                class_name="pill-stat-card",
                flex="1",
            ),
            # Stat 2
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.html(SVG_SHIELD),
                        rx.text("ANOMALY DETECTION", font_size="9.5px", color="#64748b", font_weight="700", font_family="'JetBrains Mono', monospace"),
                        align="center",
                        spacing="1",
                    ),
                    rx.text("Z-Score |Z| > 2.0", font_size="15px", font_weight="800", color="#10b981"),
                    spacing="0",
                    align_items="start",
                ),
                class_name="pill-stat-card",
                flex="1",
            ),
            spacing="3",
            width="100%",
            max_width="480px",
        ),

        # Footer Trust Note
        rx.hstack(
            rx.html(SVG_LOCK),
            rx.text("30-Day Encrypted Session Store", font_size="12px", color="#64748b"),
            rx.text("•", font_size="12px", color="#334155"),
            rx.html(SVG_CHECK),
            rx.text("Zero Hallucination Guardrails", font_size="12px", color="#64748b"),
            spacing="2",
            align="center",
            margin_top="12px",
        ),
        spacing="4",
        align_items="start",
        justify="center",
        padding="24px 32px",
        max_width="540px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT FORM COMPONENT (SIGN IN / SIGN UP)
# ─────────────────────────────────────────────────────────────────────────────

def _form_card():
    def tab_btn(label: str, tab_id: str):
        is_active = AuthState.active_tab == tab_id
        return rx.button(
            label,
            on_click=lambda: AuthState.switch_tab(tab_id),
            padding="10px 0",
            flex="1",
            font_size="13.5px",
            font_weight="700",
            border_radius="10px",
            cursor="pointer",
            background=rx.cond(is_active, "linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)", "transparent"),
            color=rx.cond(is_active, "#ffffff", "#64748b"),
            box_shadow=rx.cond(is_active, "0 4px 16px rgba(0, 212, 255, 0.3)", "none"),
            border="none",
            transition="all 0.22s cubic-bezier(0.4, 0, 0.2, 1)",
            _hover={"color": "#ffffff"},
        )

    # Clean Styled Input Helper with Generous Padding & Height
    def custom_input(label: str, placeholder: str, val, on_chg, itype="text", is_pw=False, toggle_fn=None, show_pw_var=False):
        return rx.vstack(
            rx.text(label, font_size="10.5px", font_weight="700", color="#64748b", letter_spacing="0.12em", font_family="'JetBrains Mono', monospace", margin_bottom="2px"),
            rx.box(
                rx.input(
                    placeholder=placeholder,
                    type=rx.cond(show_pw_var, "text", itype) if is_pw else itype,
                    value=val,
                    on_change=on_chg,
                    background="#070e1e",
                    border="1.5px solid #1a2f50",
                    border_radius="12px",
                    color="#f8fafc",
                    font_size="14.5px",
                    height="48px",
                    line_height="1.5",
                    padding="0 48px 0 16px" if is_pw else "0 16px",
                    width="100%",
                    _focus={
                        "border": "1.5px solid #00d4ff",
                        "box-shadow": "0 0 0 3px rgba(0, 212, 255, 0.18)",
                        "background": "#091328",
                    },
                    _placeholder={"color": "#475569", "font_size": "13.5px"},
                ),
                rx.cond(
                    is_pw,
                    rx.text(
                        rx.cond(show_pw_var, "Hide", "Show"),
                        position="absolute",
                        right="14px",
                        top="50%",
                        transform="translateY(-50%)",
                        font_size="12px",
                        color="#00d4ff",
                        cursor="pointer",
                        font_weight="700",
                        on_click=toggle_fn,
                        user_select="none",
                        _hover={"color": "#ffffff"},
                    ),
                    rx.box(),
                ),
                position="relative",
                width="100%",
            ),
            spacing="1",
            align_items="start",
            width="100%",
            margin_bottom="4px",
        )

    # Login View
    login_view = rx.vstack(
        custom_input("EMAIL ADDRESS", "name@example.com", AuthState.login_email, AuthState.set_login_email, itype="email"),
        custom_input("PASSWORD", "Enter your password", AuthState.login_password, AuthState.set_login_password, itype="password", is_pw=True, toggle_fn=AuthState.toggle_pw, show_pw_var=AuthState.show_pw),
        rx.hstack(
            rx.hstack(
                rx.box(
                    width="6px", height="6px", border_radius="50%", background="#10b981",
                    box_shadow="0 0 6px #10b981",
                ),
                rx.text("30-Day Session", font_size="11.5px", color="#94a3b8", font_weight="600"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.text("Forgot password?", font_size="11.5px", font_weight="600"),
                    spacing="1",
                    align="center",
                ),
                on_click=AuthState.forgot_password,
                background="transparent",
                border="none",
                color="#00d4ff",
                cursor="pointer",
                padding="4px 6px",
                border_radius="6px",
                _hover={"color": "#ffffff", "background": "rgba(0, 212, 255, 0.08)"},
                transition="all 0.15s ease",
            ),
            width="100%",
            align="center",
            padding_x="2px",
            margin_y="2px",
        ),
        rx.button(
            rx.cond(
                AuthState.is_loading,
                rx.hstack(rx.spinner(size="2", color="white"), rx.text("Signing In...", font_weight="700"), spacing="2", align="center"),
                rx.text("Sign In to Dashboard →", font_size="14.5px", font_weight="700"),
            ),
            on_click=AuthState.login,
            disabled=AuthState.is_loading,
            background="linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)",
            color="#ffffff",
            border_radius="10px",
            border="none",
            cursor="pointer",
            width="100%",
            padding="13px",
            margin_top="10px",
            box_shadow="0 4px 20px rgba(0, 212, 255, 0.3)",
            _hover={"transform": "translateY(-1px)", "box_shadow": "0 8px 25px rgba(0, 212, 255, 0.45)"},
            transition="all 0.2s ease",
        ),
        spacing="3",
        width="100%",
    )

    # Signup View
    signup_view = rx.vstack(
        custom_input("FULL NAME", "John Doe", AuthState.signup_name, AuthState.set_signup_name),
        custom_input("EMAIL ADDRESS", "name@example.com", AuthState.signup_email, AuthState.set_signup_email, itype="email"),
        custom_input("PASSWORD", "Min 8 chars", AuthState.signup_password, AuthState.set_signup_password, itype="password", is_pw=True, toggle_fn=AuthState.toggle_pw, show_pw_var=AuthState.show_pw),
        # Password strength bar
        rx.hstack(
            rx.box(height="3px", flex="1", border_radius="2px", background=rx.cond(AuthState.pw_strength >= 1, "#ef4444", "#1a2f50")),
            rx.box(height="3px", flex="1", border_radius="2px", background=rx.cond(AuthState.pw_strength >= 2, "#f59e0b", "#1a2f50")),
            rx.box(height="3px", flex="1", border_radius="2px", background=rx.cond(AuthState.pw_strength >= 3, "#10b981", "#1a2f50")),
            width="100%",
            spacing="1",
            margin_top="2px",
        ),
        rx.button(
            rx.cond(
                AuthState.is_loading,
                rx.hstack(rx.spinner(size="2", color="white"), rx.text("Creating Account...", font_weight="700"), spacing="2", align="center"),
                rx.text("Create Account →", font_size="14.5px", font_weight="700"),
            ),
            on_click=AuthState.sign_up,
            disabled=AuthState.is_loading,
            background="linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)",
            color="#ffffff",
            border_radius="10px",
            border="none",
            cursor="pointer",
            width="100%",
            padding="13px",
            margin_top="10px",
            box_shadow="0 4px 20px rgba(0, 212, 255, 0.3)",
            _hover={"transform": "translateY(-1px)", "box_shadow": "0 8px 25px rgba(0, 212, 255, 0.45)"},
            transition="all 0.2s ease",
        ),
        spacing="3",
        width="100%",
    )

    # Status Alert
    status_alert = rx.vstack(
        rx.cond(
            AuthState.error_msg != "",
            rx.box(
                rx.text(AuthState.error_msg, font_size="12px", color="#ef4444", font_weight="600"),
                padding="10px 14px",
                background="rgba(239, 68, 68, 0.12)",
                border="1px solid rgba(239, 68, 68, 0.3)",
                border_radius="8px",
                width="100%",
                text_align="center",
                margin_top="8px",
            ),
            rx.box(),
        ),
        rx.cond(
            AuthState.success_msg != "",
            rx.box(
                rx.text(AuthState.success_msg, font_size="12px", color="#10b981", font_weight="600"),
                padding="10px 14px",
                background="rgba(16, 185, 129, 0.12)",
                border="1px solid rgba(16, 185, 129, 0.3)",
                border_radius="8px",
                width="100%",
                text_align="center",
                margin_top="8px",
            ),
            rx.box(),
        ),
        spacing="0",
        width="100%",
    )

    return rx.box(
        rx.vstack(
            # Top Segmented Tabs
            rx.hstack(
                tab_btn("Sign In", "login"),
                tab_btn("Create Account", "signup"),
                padding="4px",
                background="rgba(6, 12, 26, 0.9)",
                border="1px solid rgba(255, 255, 255, 0.08)",
                border_radius="14px",
                width="100%",
                spacing="1",
            ),

            # Dynamic Form View
            rx.box(
                rx.cond(AuthState.active_tab == "login", login_view, signup_view),
                width="100%",
                margin_top="20px",
            ),

            status_alert,

            # Footer Security note
            rx.text(
                "30-day session persistence · AES-256 encrypted store",
                font_size="11px",
                color="#4a6080",
                text_align="center",
                margin_top="16px",
            ),
            spacing="3",
            width="100%",
        ),
        padding="36px 32px",
        class_name="custom-glass-panel",
        width="100%",
        max_width="420px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXPORTED PAGES
# ─────────────────────────────────────────────────────────────────────────────

def login_page() -> rx.Component:
    return rx.box(
        _background(),
        rx.hstack(
            _hero_section(),
            _form_card(),
            spacing="8",
            align="center",
            justify="center",
            min_height="100vh",
            width="100%",
            padding="24px",
            z_index="1",
            position="relative",
            flex_wrap="wrap",
        ),
        background="#030712",
        min_height="100vh",
        width="100%",
        on_mount=AuthState.check_and_redirect,
    )



def verified_page() -> rx.Component:
    return rx.box(
        _background(),
        rx.box(
            rx.vstack(
                rx.text("✓", font_size="52px", color="#10b981", font_weight="900"),
                rx.text("Email Verified!", font_size="22px", font_weight="800", color="#ffffff"),
                rx.text("Your account is active. You can now access your financial dashboard.", font_size="13px", color="#94a3b8", text_align="center"),
                rx.button(
                    "Open My Dashboard →",
                    on_click=rx.redirect("/"),
                    class_name="btn-primary-action",
                    padding="12px 28px",
                    margin_top="12px",
                ),
                spacing="3",
                align="center",
            ),
            padding="40px",
            class_name="glass-panel",
            max_width="420px",
            margin="auto",
        ),
        display="flex",
        align_items="center",
        justify_content="center",
        min_height="100vh",
        background="#060a14",
    )


def reset_password_page() -> rx.Component:
    return rx.box(
        _background(),
        rx.box(
            rx.vstack(
                rx.text("Reset Password", font_size="20px", font_weight="800", color="#ffffff"),
                rx.text("Enter a strong new password for your account.", font_size="12px", color="#94a3b8"),
                rx.input(
                    placeholder="New password",
                    type="password",
                    value=AuthState.new_password,
                    on_change=AuthState.set_new_password,
                    class_name="input-field",
                    padding="10px 14px",
                    width="100%",
                ),
                rx.input(
                    placeholder="Confirm new password",
                    type="password",
                    value=AuthState.confirm_password,
                    on_change=AuthState.set_confirm_password,
                    class_name="input-field",
                    padding="10px 14px",
                    width="100%",
                ),
                rx.button(
                    "Update Password",
                    on_click=AuthState.do_reset_password,
                    class_name="btn-primary-action",
                    width="100%",
                    padding="12px",
                ),
                rx.button(
                    "← Back to Sign In",
                    on_click=rx.redirect("/"),
                    background="none",
                    border="none",
                    color="#64748b",
                    font_size="12px",
                    cursor="pointer",
                ),
                spacing="3",
                width="100%",
            ),
            padding="36px",
            class_name="glass-panel",
            max_width="380px",
            margin="auto",
        ),
        display="flex",
        align_items="center",
        justify_content="center",
        min_height="100vh",
        background="#060a14",
        on_mount=AuthState.load_reset_page,
    )