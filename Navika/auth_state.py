# finance_ai/auth_state.py
import os
import re
import reflex as rx
from dotenv import load_dotenv

load_dotenv()   # ← MUST be called before os.getenv


def _get_google_client_id():
    return os.getenv("GOOGLE_CLIENT_ID", "")

def _get_google_client_secret():
    return os.getenv("GOOGLE_CLIENT_SECRET", "")

def _get_app_url():
    return os.getenv("APP_URL", "http://localhost:3000")


def _valid_email(e: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e.strip()))


class AuthState(rx.State):

    # ── Tab: "login" or "signup" — Reflex state controls which form shows ─────
    active_tab: str = "login"

    # ── Form fields ───────────────────────────────────────────────────────────
    login_email:     str = ""
    login_password:  str = ""
    signup_name:     str = ""
    signup_email:    str = ""
    signup_password: str = ""

    # ── UI ────────────────────────────────────────────────────────────────────
    is_loading:  bool = False
    error_msg:   str  = ""
    success_msg: str  = ""
    show_pw:      bool = False
    pw_strength:  int  = 0   # 0=empty 1=weak 2=medium 3=strong

    # ── Reset password page ───────────────────────────────────────────────────
    reset_token:     str  = ""   # from URL query param
    new_password:    str  = ""
    confirm_password:str  = ""
    new_pw_strength: int  = 0
    show_new_pw:     bool = False
    reset_done:      bool = False

    # ── Session cookie (30 days) ──────────────────────────────────────────────
    session_token: str = rx.Cookie(name="fs_session", max_age=2_592_000)

    # ── Logged-in user ────────────────────────────────────────────────────────
    user_name:    str  = ""
    user_email:   str  = ""
    user_id:      int  = 0
    is_logged_in: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # Tab switching
    # ─────────────────────────────────────────────────────────────────────────
    def switch_tab(self, tab: str):
        self.active_tab  = tab
        self.error_msg   = ""
        self.success_msg = ""

    # ─────────────────────────────────────────────────────────────────────────
    # Field setters
    # ─────────────────────────────────────────────────────────────────────────
    def set_login_email(self, v: str):
        self.login_email = v; self.error_msg = ""

    def set_login_password(self, v: str):
        self.login_password = v; self.error_msg = ""

    def set_signup_name(self, v: str):
        self.signup_name = v; self.error_msg = ""

    def set_signup_email(self, v: str):
        self.signup_email = v; self.error_msg = ""

    def set_signup_password(self, v: str):
        self.signup_password = v; self.error_msg = ""
        s = 0
        if len(v) >= 8:                     s += 1
        if re.search(r"[A-Z]", v):          s += 1
        if re.search(r"[0-9!@#$%^&*]", v): s += 1
        self.pw_strength = s

    def toggle_pw(self):
        self.show_pw = not self.show_pw

    def toggle_new_pw(self):
        self.show_new_pw = not self.show_new_pw

    def set_new_password(self, v: str):
        self.new_password = v
        s = 0
        if len(v) >= 8:                     s += 1
        if re.search(r"[A-Z]", v):          s += 1
        if re.search(r"[0-9!@#$%^&*]", v): s += 1
        self.new_pw_strength = s

    def set_confirm_password(self, v: str):
        self.confirm_password = v

    def set_reset_token(self, token: str):
        self.reset_token = token

    # ─────────────────────────────────────────────────────────────────────────
    # Session
    # ─────────────────────────────────────────────────────────────────────────
    def check_session(self):
        if not self.session_token:
            return
        from .auth_db import get_user_from_session
        u = get_user_from_session(self.session_token)
        if u:
            self.is_logged_in = True
            self.user_name    = u.name
            self.user_email   = u.email
            self.user_id      = u.id
        else:
            self.session_token = ""

    def check_and_redirect(self):
        """on_mount for login page — redirect to dashboard if already logged in."""
        self.check_session()
        if self.is_logged_in:
            return rx.redirect("/")

    # ─────────────────────────────────────────────────────────────────────────
    # Sign up
    # ─────────────────────────────────────────────────────────────────────────
    def sign_up(self):
        self.error_msg = ""; self.success_msg = ""

        if not self.signup_name.strip():
            self.error_msg = "Please enter your full name"; return
        if not _valid_email(self.signup_email):
            self.error_msg = "Please enter a valid email address"; return
        if len(self.signup_password) < 8:
            self.error_msg = "Password must be at least 8 characters"; return

        self.is_loading = True
        yield  # show spinner

        try:
            from .auth_db import create_user, create_verification_token
            from .email_service import send_verification_email

            user = create_user(
                email    = self.signup_email,
                name     = self.signup_name,
                password = self.signup_password,
            )
            if user is None:
                self.error_msg = "An account with this email already exists"; return

            # Check if Gmail is configured
            gmail_user = os.getenv("GMAIL_USER", "").strip()
            gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "").strip()
            email_configured = bool(gmail_user and gmail_pass)

            if email_configured:
                # Send real verification email
                token = create_verification_token(user.id)
                send_verification_email(self.signup_email, self.signup_name, token)
                self.success_msg = (
                    f"✓ Account created! Check {self.signup_email} for your verification link. "
                    f"(Also check your spam folder)"
                )
            else:
                # No Gmail configured — auto-verify so user can log in immediately
                from .auth_db import verify_user_directly
                verify_user_directly(user.id)
                try:
                    from .email_service import send_welcome_email
                    send_welcome_email(self.signup_email, self.signup_name)
                except Exception:
                    pass
                self.success_msg = (
                    f"✓ Account created! You can now sign in. "
                    f"(Email verification skipped — Gmail not configured)"
                )

            self.signup_name     = ""
            self.signup_email    = ""
            self.signup_password = ""
            self.pw_strength     = 0
        except Exception as e:
            self.error_msg = f"Signup failed: {str(e)}"
        finally:
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    # Login
    # ─────────────────────────────────────────────────────────────────────────
    def login(self):
        self.error_msg = ""; self.success_msg = ""

        if not _valid_email(self.login_email):
            self.error_msg = "Please enter a valid email address"; return
        if not self.login_password:
            self.error_msg = "Please enter your password"; return

        self.is_loading = True
        yield

        try:
            from .auth_db import (get_user_by_email, verify_password,
                                   create_session, update_last_login)

            u = get_user_by_email(self.login_email)
            if not u or not u.password_hash:
                self.error_msg = "Invalid email or password"; return
            if not verify_password(self.login_password, u.password_hash):
                self.error_msg = "Invalid email or password"; return
            if not u.is_verified:
                self.error_msg = "Please verify your email first — check your inbox"; return

            tok = create_session(u.id)
            update_last_login(u.id)

            self.session_token  = tok
            self.is_logged_in   = True
            self.user_name      = u.name
            self.user_email     = u.email
            self.user_id        = u.id
            self.login_email    = ""
            self.login_password = ""
            yield
            return rx.redirect("/")
        except Exception as e:
            self.error_msg = f"Login failed: {str(e)}"
        finally:
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    # Logout
    # ─────────────────────────────────────────────────────────────────────────
    def logout(self):
        from .auth_db import delete_session
        if self.session_token:
            delete_session(self.session_token)
        self.session_token = ""; self.is_logged_in = False
        self.user_name = ""; self.user_email = ""; self.user_id = 0
        return rx.redirect("/")

    # ─────────────────────────────────────────────────────────────────────────
    # Forgot password
    # ─────────────────────────────────────────────────────────────────────────
    def forgot_password(self):
        if not _valid_email(self.login_email):
            self.error_msg = "Enter your email in the field above first"; return
        self.is_loading = True; yield
        try:
            from .auth_db import get_user_by_email, create_reset_token
            from .email_service import send_password_reset_email
            u = get_user_by_email(self.login_email)
            if u:
                tok = create_reset_token(u.id)
                send_password_reset_email(self.login_email, u.name, tok)
            self.success_msg = "If that account exists, a reset link has been sent."
        except Exception as e:
            self.error_msg = str(e)
        finally:
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    # Reset password (from the /reset-password page)
    # ─────────────────────────────────────────────────────────────────────────
    def load_reset_page(self):
        """Called on_load of reset password page — reads ?token= from URL params."""
        self.error_msg = ""
        self.success_msg = ""
        self.reset_done = False
        token = self.router.page.params.get("token", "")
        if token:
            self.reset_token = token
        elif not self.reset_token:
            self.error_msg = "Invalid or missing reset link."

    def do_reset_password(self):
        self.error_msg = ""; self.success_msg = ""

        if not self.reset_token:
            self.error_msg = "Invalid reset link — please request a new one."
            return

        if len(self.new_password) < 8:
            self.error_msg = "Password must be at least 8 characters."
            return

        if self.new_password != self.confirm_password:
            self.error_msg = "Passwords do not match."
            return

        self.is_loading = True
        yield

        try:
            from .auth_db import reset_password, get_user_by_id
            result = reset_password(self.reset_token, self.new_password)

            if not result:
                self.error_msg = "This reset link has expired or already been used. Please request a new one."
                return

            # Send confirmation email
            try:
                u = get_user_by_id(result)
                if u:
                    from .email_service import send_password_changed_email
                    send_password_changed_email(u.email, u.name)
            except Exception:
                pass

            self.reset_done       = True
            self.new_password     = ""
            self.confirm_password = ""
            self.reset_token      = ""
            self.success_msg      = "✓ Password changed! You can now sign in with your new password."

        except Exception as e:
            self.error_msg = f"Reset failed: {str(e)}"
        finally:
            self.is_loading = False

    # ─────────────────────────────────────────────────────────────────────────
    # Google OAuth
    # ─────────────────────────────────────────────────────────────────────────
    def google_login(self):
        if not _get_google_client_id():
            self.error_msg = "Google login not set up yet — use email/password"
            return
        redirect_uri = f"{_get_app_url()}/auth/google/callback"
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={_get_google_client_id()}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline&prompt=select_account"
        )
        return rx.redirect(url)

    def process_google_code(self, code: str):
        self.is_loading = True; yield
        try:
            import httpx
            redirect_uri = f"{_get_app_url()}/auth/google/callback"
            r = httpx.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": _get_google_client_id(),
                "client_secret": _get_google_client_secret(),
                "redirect_uri": redirect_uri, "grant_type": "authorization_code",
            })
            tokens = r.json()
            access_token = tokens.get("access_token")
            if not access_token:
                self.error_msg = f"Google login failed: {tokens.get('error_description','unknown')}"
                return rx.redirect("/")
            info = httpx.get("https://www.googleapis.com/oauth2/v2/userinfo",
                             headers={"Authorization": f"Bearer {access_token}"}).json()
            from .auth_db import (get_user_by_google_id, get_user_by_email,
                                   create_user, link_google, create_session, update_last_login)
            u = get_user_by_google_id(info["id"])
            if not u:
                u = get_user_by_email(info["email"])
                if u:
                    link_google(u.id, info["id"], info.get("picture"))
                else:
                    u = create_user(email=info["email"],
                                    name=info.get("name", info["email"].split("@")[0]),
                                    google_id=info["id"], avatar_url=info.get("picture"),
                                    is_verified=True)
                    # Send Google welcome email for brand new users
                    if u:
                        try:
                            from .email_service import send_google_welcome_email
                            send_google_welcome_email(u.email, u.name)
                        except Exception:
                            pass
            if not u:
                self.error_msg = "Could not create account"; return rx.redirect("/")
            tok = create_session(u.id); update_last_login(u.id)
            self.session_token = tok; self.is_logged_in = True
            self.user_name = u.name; self.user_email = u.email; self.user_id = u.id
            yield; return rx.redirect("/")
        except Exception as e:
            self.error_msg = f"Google login error: {str(e)}"; return rx.redirect("/")
        finally:
            self.is_loading = False