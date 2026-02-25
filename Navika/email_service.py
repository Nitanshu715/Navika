# finance_ai/email_service.py
import os
import smtplib
import re as _re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()   # ← load .env FIRST, before reading any os.getenv

APP_NAME = "Navika"


def _cfg():
    """Read env vars fresh every call — so they're never stale."""
    return {
        "user":     os.getenv("GMAIL_USER", "").strip(),
        "password": os.getenv("GMAIL_APP_PASSWORD", "").strip(),
        "app_url":  os.getenv("APP_URL", "http://localhost:3000").rstrip("/"),
    }


def _send(to: str, subject: str, html: str) -> bool:
    cfg  = _cfg()
    user = cfg["user"]
    pw   = cfg["password"]

    if not user or not pw:
        # ── Dev mode: no Gmail configured → print link to terminal ──────────
        print("\n" + "=" * 65)
        print(f"[EMAIL DEV MODE]  To: {to}")
        print(f"Subject: {subject}")
        links = _re.findall(r'href="(http[^"]+)"', html)
        if links:
            print("\nCopy this link into your browser:")
            for link in links:
                print(f"\n  >>> {link}\n")
        print("=" * 65 + "\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{APP_NAME} <{user}>"
        msg["To"]      = to
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(user, pw)
            srv.sendmail(user, to, msg.as_string())
        print(f"[email] Sent '{subject}' → {to}")
        return True
    except Exception as e:
        print(f"[email] FAILED to send to {to}: {e}")
        return False


def _wrap(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{margin:0;padding:0;background:#060a14;font-family:'Courier New',monospace;color:#e2e8f0}}
.w{{max-width:540px;margin:36px auto;padding:0 16px}}
.c{{background:#0b1120;border:1px solid #1a2f50;border-radius:16px;overflow:hidden}}
.h{{background:linear-gradient(135deg,#0d1830,#0b1120);border-bottom:1px solid #1a2f50;padding:30px 36px 24px;text-align:center}}
.lm{{font-size:32px;color:#00d4ff;display:block;margin-bottom:8px}}
.ln{{font-size:17px;font-weight:900;letter-spacing:.2em;color:#e2e8f0;display:block}}
.b{{padding:32px 36px}}
h2{{font-size:18px;font-weight:900;color:#e2e8f0;margin:0 0 12px}}
p{{font-size:13px;color:#94a3b8;line-height:1.8;margin:0 0 14px}}
strong{{color:#e2e8f0}}
.bw{{text-align:center;margin:24px 0}}
.btn{{display:inline-block;padding:13px 32px;background:linear-gradient(135deg,#7c3aed,#5b21b6);color:white;text-decoration:none;border-radius:10px;font-size:14px;font-weight:900;letter-spacing:.06em}}
.code{{background:#060a14;border:1px solid #1a2f5066;border-radius:8px;padding:10px 14px;font-size:11px;color:#4a6080;word-break:break-all;margin-top:6px}}
.ft{{border-top:1px solid #1a2f50;padding:16px 36px;text-align:center;font-size:10px;color:#4a6080;letter-spacing:.06em}}
</style></head><body><div class="w"><div class="c">
<div class="h"><span class="lm">◈</span><span class="ln">Navika</span></div>
<div class="b"><h2>{title}</h2>{body}</div>
<div class="ft">Navika · Automated message · Do not reply</div>
</div></div></body></html>"""


def send_verification_email(to: str, name: str, token: str) -> bool:
    app_url = _cfg()["app_url"]
    url     = f"{app_url}/verify-email?token={token}"
    body    = f"""
      <p>Hey <strong>{name}</strong>,</p>
      <p>Thanks for signing up to Navika. Click below to verify your email:</p>
      <div class="bw"><a href="{url}" class="btn">◈  VERIFY MY ACCOUNT</a></div>
      <p>This link expires in <strong style="color:#f59e0b">24 hours</strong>.</p>
      <p>If you didn't sign up, ignore this email.</p>
      <div class="code">{url}</div>
    """
    return _send(to, f"Verify your {APP_NAME} account", _wrap("Verify Your Email", body))


def send_welcome_email(to: str, name: str) -> bool:
    app_url = _cfg()["app_url"]
    body    = f"""
      <p>Your account is active, <strong>{name}</strong>!</p>
      <p>Head to your dashboard to start tracking your finances with AI.</p>
      <div class="bw"><a href="{app_url}" class="btn">→  OPEN DASHBOARD</a></div>
    """
    return _send(to, f"Welcome to {APP_NAME}!", _wrap("You're All Set 🚀", body))


def send_password_reset_email(to: str, name: str, token: str) -> bool:
    app_url = _cfg()["app_url"]
    url     = f"{app_url}/reset-password?token={token}"
    body    = f"""
      <p>Hi <strong>{name}</strong>,</p>
      <p>We received a password reset request. This link expires in <strong style="color:#ef4444">1 hour</strong>.</p>
      <div class="bw">
        <a href="{url}" class="btn" style="background:linear-gradient(135deg,#ef4444,#b91c1c)">
          ⚠  RESET PASSWORD
        </a>
      </div>
      <p>If you didn't request this, ignore this email.</p>
      <div class="code">{url}</div>
    """
    return _send(to, f"Reset your {APP_NAME} password", _wrap("Password Reset Request", body))