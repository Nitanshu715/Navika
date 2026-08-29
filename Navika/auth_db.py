# finance_ai/auth_db.py
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# users.db is SEPARATE from finance.db (which holds transactions)
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "users.db")
DB_URL   = f"sqlite:///{_DB_PATH}"

engine    = create_engine(DB_URL, connect_args={"check_same_thread": False})
DBSession = sessionmaker(bind=engine)
Base      = declarative_base()


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    name          = Column(String(255), nullable=False, default="")
    username      = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=True)   # null for Google-only accounts
    google_id     = Column(String(255), nullable=True, unique=True)
    is_verified   = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    avatar_url    = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    last_login    = Column(DateTime, nullable=True)


class TransactionNote(Base):
    __tablename__ = "transaction_notes"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, nullable=False, index=True)
    title      = Column(String(255), nullable=False)
    content    = Column(Text, nullable=False)
    tag        = Column(String(50), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBudget(Base):
    __tablename__ = "user_budgets"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, nullable=False, unique=True, index=True)
    monthly_cap   = Column(Float, default=25000.0)
    food_cap      = Column(Float, default=8000.0)
    shopping_cap  = Column(Float, default=10000.0)
    transport_cap = Column(Float, default=4000.0)
    ent_cap       = Column(Float, default=3000.0)
    updated_at    = Column(DateTime, default=datetime.utcnow)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False)
    token      = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Boolean, default=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False)
    token      = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Boolean, default=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False, index=True)
    token      = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables automatically on first run
Base.metadata.create_all(engine)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(pw: str) -> str:
    salt   = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + pw).encode()).hexdigest() == hashed
    except Exception:
        return False

def _new_token(n: int = 48) -> str:
    return secrets.token_urlsafe(n)


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(email: str, name: str = "", password: str = None,
                google_id: str = None, avatar_url: str = None,
                is_verified: bool = False):
    s = DBSession()
    try:
        if s.query(User).filter_by(email=email.lower().strip()).first():
            return None   # email already registered
        u = User(
            email         = email.lower().strip(),
            name          = name.strip(),
            password_hash = hash_password(password) if password else None,
            google_id     = google_id,
            avatar_url    = avatar_url,
            is_verified   = is_verified,
        )
        s.add(u); s.commit(); s.refresh(u)
        return u
    except Exception as e:
        s.rollback()
        print(f"[auth_db] create_user error: {e}")
        return None
    finally:
        s.close()

def get_user_by_email(email: str):
    s = DBSession()
    try:    return s.query(User).filter_by(email=email.lower().strip()).first()
    finally: s.close()

def get_user_by_id(uid: int):
    s = DBSession()
    try:    return s.query(User).filter_by(id=uid).first()
    finally: s.close()

def get_user_by_google_id(gid: str):
    s = DBSession()
    try:    return s.query(User).filter_by(google_id=gid).first()
    finally: s.close()

def update_last_login(uid: int):
    s = DBSession()
    try:
        u = s.query(User).filter_by(id=uid).first()
        if u: u.last_login = datetime.utcnow(); s.commit()
    finally: s.close()

def link_google(uid: int, google_id: str, avatar_url: str = None):
    s = DBSession()
    try:
        u = s.query(User).filter_by(id=uid).first()
        if u:
            u.google_id   = google_id
            u.is_verified = True
            if avatar_url: u.avatar_url = avatar_url
            s.commit()
    finally: s.close()


# ── Email verification ────────────────────────────────────────────────────────

def create_verification_token(user_id: int) -> str:
    s = DBSession(); tok = _new_token()
    try:
        s.add(EmailVerificationToken(
            user_id    = user_id,
            token      = tok,
            expires_at = datetime.utcnow() + timedelta(hours=24),
        ))
        s.commit()
        return tok
    finally:
        s.close()

def verify_email_token(token_str: str):
    """Returns user_id on success, None on failure."""
    s = DBSession()
    try:
        t = s.query(EmailVerificationToken).filter_by(token=token_str, used=False).first()
        if not t or t.expires_at < datetime.utcnow():
            return None
        t.used = True
        u = s.query(User).filter_by(id=t.user_id).first()
        if u: u.is_verified = True
        s.commit()
        return t.user_id
    except:
        s.rollback(); return None
    finally:
        s.close()


# ── Password reset ────────────────────────────────────────────────────────────

def verify_user_directly(user_id: int):
    """Directly mark a user as verified — used when email is not configured."""
    s = DBSession()
    try:
        u = s.query(User).filter_by(id=user_id).first()
        if u:
            u.is_verified = True
            s.commit()
    finally:
        s.close()


def create_reset_token(user_id: int) -> str:
    s = DBSession(); tok = _new_token()
    try:
        s.add(PasswordResetToken(
            user_id    = user_id,
            token      = tok,
            expires_at = datetime.utcnow() + timedelta(hours=1),
        ))
        s.commit()
        return tok
    finally:
        s.close()

def reset_password(token_str: str, new_pw: str):
    """Returns user_id on success, None on failure (expired/invalid/used token)."""
    s = DBSession()
    try:
        t = s.query(PasswordResetToken).filter_by(token=token_str, used=False).first()
        if not t or t.expires_at < datetime.utcnow():
            return None
        t.used = True
        u = s.query(User).filter_by(id=t.user_id).first()
        if not u:
            return None
        u.password_hash = hash_password(new_pw)
        s.commit()
        return u.id          # ← return user_id so caller can send confirmation email
    except:
        s.rollback()
        return None
    finally:
        s.close()


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(user_id: int) -> str:
    s = DBSession(); tok = _new_token()
    try:
        s.add(UserSession(
            user_id    = user_id,
            token      = tok,
            expires_at = datetime.utcnow() + timedelta(days=30),
        ))
        s.commit()
        return tok
    finally:
        s.close()

def get_user_from_session(token: str):
    s = DBSession()
    try:
        sess = s.query(UserSession).filter_by(token=token).first()
        if not sess or sess.expires_at < datetime.utcnow():
            return None
        return s.query(User).filter_by(id=sess.user_id).first()
    finally:
        s.close()

def delete_session(token: str):
    s = DBSession()
    try:
        s.query(UserSession).filter_by(token=token).delete()
        s.commit()
    finally:
        s.close()


# ── Profile & Notes CRUD ──────────────────────────────────────────────────────

def update_user_profile(user_id: int, name: str = None, username: str = None, avatar_url: str = None):
    s = DBSession()
    try:
        u = s.query(User).filter_by(id=user_id).first()
        if u:
            if name is not None:
                u.name = name.strip()
            if username is not None:
                u.username = username.strip().lower()
            if avatar_url is not None:
                u.avatar_url = avatar_url.strip()
            s.commit()
            s.refresh(u)
            return u
        return None
    finally:
        s.close()

def create_transaction_note(user_id: int, title: str, content: str, tag: str = "General"):
    s = DBSession()
    try:
        note = TransactionNote(
            user_id=user_id,
            title=title.strip(),
            content=content.strip(),
            tag=tag.strip(),
            created_at=datetime.utcnow()
        )
        s.add(note)
        s.commit()
        s.refresh(note)
        return note
    finally:
        s.close()

def get_transaction_notes(user_id: int):
    s = DBSession()
    try:
        notes = s.query(TransactionNote).filter_by(user_id=user_id).order_by(TransactionNote.id.desc()).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "tag": n.tag,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "",
            }
            for n in notes
        ]
    finally:
        s.close()

def delete_transaction_note(user_id: int, note_id: int) -> bool:
    s = DBSession()
    try:
        n = s.query(TransactionNote).filter_by(id=note_id, user_id=user_id).first()
        if n:
            s.delete(n)
            s.commit()
            return True
        return False
    finally:
        s.close()


def get_user_budget(user_id: int) -> dict:
    s = DBSession()
    try:
        b = s.query(UserBudget).filter_by(user_id=user_id).first()
        if not b:
            return {
                "monthly_cap": 25000.0,
                "food_cap": 8000.0,
                "shopping_cap": 10000.0,
                "transport_cap": 4000.0,
                "ent_cap": 3000.0,
            }
        return {
            "monthly_cap": float(b.monthly_cap or 25000.0),
            "food_cap": float(b.food_cap or 8000.0),
            "shopping_cap": float(b.shopping_cap or 10000.0),
            "transport_cap": float(b.transport_cap or 4000.0),
            "ent_cap": float(b.ent_cap or 3000.0),
        }
    finally:
        s.close()


def save_user_budget(user_id: int, monthly: float, food: float, shopping: float, transport: float, ent: float) -> dict:
    s = DBSession()
    try:
        b = s.query(UserBudget).filter_by(user_id=user_id).first()
        if not b:
            b = UserBudget(
                user_id=user_id,
                monthly_cap=monthly,
                food_cap=food,
                shopping_cap=shopping,
                transport_cap=transport,
                ent_cap=ent,
            )
            s.add(b)
        else:
            b.monthly_cap = monthly
            b.food_cap = food
            b.shopping_cap = shopping
            b.transport_cap = transport
            b.ent_cap = ent
            b.updated_at = datetime.utcnow()
        s.commit()
        return {
            "monthly_cap": b.monthly_cap,
            "food_cap": b.food_cap,
            "shopping_cap": b.shopping_cap,
            "transport_cap": b.transport_cap,
            "ent_cap": b.ent_cap,
        }
    finally:
        s.close()

Base.metadata.create_all(engine)