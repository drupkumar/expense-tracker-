from __future__ import annotations

import csv
import hashlib
import io
import math
import os
import re
import uuid
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import extract, func, or_, text
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Budget, Category, Goal, ImportBatch, RecurringTransaction, Transaction, Transfer, User, db
from parser import parse_receipt_text

ALLOWED_RECEIPTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

DEFAULT_CATEGORIES = [
    ("Food", "expense", "bi-cup-hot", "#ff8a65"),
    ("Groceries", "expense", "bi-basket", "#81c784"),
    ("Travel", "expense", "bi-airplane", "#64b5f6"),
    ("Shopping", "expense", "bi-bag", "#ce93d8"),
    ("Education", "expense", "bi-mortarboard", "#4dd0e1"),
    ("Entertainment", "expense", "bi-film", "#f48fb1"),
    ("Bills", "expense", "bi-lightning", "#ffd54f"),
    ("Health", "expense", "bi-heart-pulse", "#ef9a9a"),
    ("Rent", "expense", "bi-house", "#90a4ae"),
    ("Other", "expense", "bi-three-dots", "#80cbc4"),
    ("Salary", "income", "bi-briefcase", "#3ee0b0"),
    ("Freelance", "income", "bi-laptop", "#a5d6a7"),
    ("Scholarship", "income", "bi-award", "#ffe082"),
    ("Gift", "income", "bi-gift", "#f8bbd0"),
    ("Other Income", "income", "bi-plus-circle", "#80deea"),
]


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)

    csrf = CSRFProtect(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=[])
    # Keep the limiter alive because its route decorators use a weak reference.
    app.extensions["aureum_limiter"] = limiter

    with app.app_context():
        db.create_all()
        migrate_database()
        seed_categories()
        process_recurring_transactions()

    register_routes(app, csrf, limiter)
    return app


def seed_categories() -> None:
    if Category.query.filter_by(user_id=None).count():
        return
    for name, kind, icon, color in DEFAULT_CATEGORIES:
        db.session.add(Category(user_id=None, name=name, kind=kind, icon=icon, color=color))
    db.session.commit()


def migrate_database() -> None:
    """Apply small additive migrations so existing SQLite installs keep working."""
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    additions = {
        "user": {
            "reset_token": "VARCHAR(100) DEFAULT ''",
            "reset_token_expires": "DATETIME NULL",
            "theme": "VARCHAR(10) DEFAULT 'dark'",
        },
        "category": {"user_id": "INTEGER NULL"},
    }
    with db.engine.begin() as connection:
        for table, columns in additions.items():
            present = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in present:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
    # db.create_all() above creates new tables for existing databases.


def process_recurring_transactions() -> None:
    today = date.today()
    due_recurring = RecurringTransaction.query.filter(
        RecurringTransaction.is_active.is_(True), RecurringTransaction.next_due_date <= today
    ).all()
    for rec in due_recurring:
        while rec.next_due_date <= today:
            db.session.add(Transaction(
                user_id=rec.user_id, category_id=rec.category_id, amount=rec.amount,
                kind=rec.kind, note=f"{rec.note} (recurring)" if rec.note else "Recurring transaction",
                merchant=rec.merchant, payment_method=rec.payment_method,
                txn_date=rec.next_due_date, source="recurring",
            ))
            rec.next_due_date = advance_due_date(rec.next_due_date, rec.frequency)
    if due_recurring:
        db.session.commit()


def advance_due_date(due: date, frequency: str) -> date:
    if frequency == "daily":
        return due + timedelta(days=1)
    if frequency == "weekly":
        return due + timedelta(weeks=1)
    if frequency == "monthly":
        year = due.year + (due.month == 12)
        month = 1 if due.month == 12 else due.month + 1
        return date(year, month, min(due.day, month_bounds(year, month)[1].day))
    year = due.year + 1
    return date(year, due.month, min(due.day, month_bounds(year, due.month)[1].day))


def valid_user_category(category_id: int, user_id: int, kind: str | None = None) -> bool:
    query = Category.query.filter(
        Category.id == category_id,
        (Category.user_id.is_(None) | (Category.user_id == user_id)),
    )
    if kind:
        query = query.filter(Category.kind == kind)
    return query.first() is not None


def valid_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_user() -> User | None:
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def money(value: float) -> str:
    return f"₹{value:,.0f}" if float(value).is_integer() else f"₹{value:,.2f}"


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def format_money(user: User | None, value: float) -> str:
    currency = user.currency if user else "INR"
    symbols = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency + " ")
    number = float(value)
    return f"{symbol}{number:,.0f}" if number.is_integer() else f"{symbol}{number:,.2f}"


def linear_regression(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return 0, 0
    n = len(values)
    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(xi * yi for xi, yi in zip(x, values))
    sum_x2 = sum(xi * xi for xi in x)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0, 0
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password must be 128 characters or fewer."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, ""


def category_map(user_id: int = None) -> dict[str, Category]:
    if user_id:
        cats = Category.query.filter((Category.user_id == None) | (Category.user_id == user_id)).all()
    else:
        cats = Category.query.all()
    return {c.name.lower(): c for c in cats}


def register_routes(app: Flask, csrf, limiter) -> None:
    @app.context_processor
    def inject_globals():
        user = current_user()
        return {
            "current_user": user,
            "money": lambda value: format_money(user, value),
            "today": date.today().isoformat(),
        }

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or len(name) > 120 or not email or len(email) > 180 or not password:
                flash("Name, email and password are required.", "danger")
                return render_template("register.html")
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                flash("Enter a valid email address.", "danger")
                return render_template("register.html")
            valid, msg = validate_password(password)
            if not valid:
                flash(msg, "danger")
                return render_template("register.html")
            if User.query.filter_by(email=email).first():
                flash("That email is already registered.", "danger")
                return render_template("register.html")
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome to Aureum. Your ledger is ready.", "success")
            return redirect(url_for("dashboard"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per 15 minutes")
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "danger")
                return render_template("login.html")
            session["user_id"] = user.id
            process_recurring_transactions()
            flash(f"Welcome back, {user.name.split()[0]}.", "success")
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/demo")
    def demo():
        user = User.query.filter_by(email="demo@aureum.app").first()
        if not user:
            user = User(
                name="Aarav Sharma",
                email="demo@aureum.app",
                password_hash=generate_password_hash("demo123"),
                monthly_income=45000,
                phone="9876543210",
            )
            db.session.add(user)
            db.session.commit()
            seed_demo_data(user)
        session["user_id"] = user.id
        flash("Demo workspace loaded with sample money stories.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Signed out. Your numbers stay private.", "success")
        return redirect(url_for("login"))

    @app.route("/forgot-password", methods=["GET", "POST"])
    @limiter.limit("5 per hour")
    def forgot_password():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user:
                token = uuid.uuid4().hex
                user.reset_token = token
                user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
                db.session.commit()
                reset_link = f"{request.host_url}reset-password?token={token}"
                if app.debug or app.config.get("PASSWORD_RESET_LOGS", False):
                    print(f"\n{'='*60}\nPASSWORD RESET LINK FOR {email}:\n{reset_link}\n{'='*60}\n")
            flash("If that email exists, a reset link was generated. Check the console/logs in development.", "info")
            return render_template("forgot_password.html")
        return render_template("forgot_password.html")

    @app.route("/reset-password", methods=["GET", "POST"])
    @limiter.limit("10 per hour")
    def reset_password():
        token = request.args.get("token", "")
        if request.method == "POST":
            token = request.form.get("token", "")
            password = request.form.get("password", "")
            user = User.query.filter_by(reset_token=token).first()
            if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
                flash("Invalid or expired reset link.", "danger")
                return redirect(url_for("login"))
            valid, msg = validate_password(password)
            if not valid:
                flash(msg, "danger")
                return render_template("reset_password.html", token=token)
            user.password_hash = generate_password_hash(password)
            user.reset_token = ""
            user.reset_token_expires = None
            db.session.commit()
            flash("Password reset. Sign in with your new password.", "success")
            return redirect(url_for("login"))
        return render_template("reset_password.html", token=token)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = current_user()
        today = date.today()
        start, end = month_bounds(today.year, today.month)
        txns = Transaction.query.filter_by(user_id=user.id)
        month_txns = txns.filter(Transaction.txn_date.between(start, end))

        income = sum(t.amount for t in month_txns.filter_by(kind="income"))
        expense = sum(t.amount for t in month_txns.filter_by(kind="expense"))
        balance = income - expense
        savings_rate = (balance / income * 100) if income else 0

        prev_start, prev_end = month_bounds(today.year if today.month > 1 else today.year - 1, 12 if today.month == 1 else today.month - 1)
        prev_expense = sum(
            t.amount
            for t in Transaction.query.filter_by(user_id=user.id, kind="expense").filter(
                Transaction.txn_date.between(prev_start, prev_end)
            )
        )
        delta = ((expense - prev_expense) / prev_expense * 100) if prev_expense else 0

        cat_rows = (
            db.session.query(Category.name, Category.color, func.sum(Transaction.amount))
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user.id,
                Transaction.kind == "expense",
                Transaction.txn_date.between(start, end),
            )
            .group_by(Category.id)
            .order_by(func.sum(Transaction.amount).desc())
            .all()
        )

        trend_labels, trend_income, trend_expense = [], [], []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            s, e = month_bounds(y, m)
            trend_labels.append(s.strftime("%b"))
            month_set = Transaction.query.filter_by(user_id=user.id).filter(Transaction.txn_date.between(s, e))
            trend_income.append(round(sum(t.amount for t in month_set.filter_by(kind="income")), 2))
            trend_expense.append(round(sum(t.amount for t in month_set.filter_by(kind="expense")), 2))

        slope, intercept = linear_regression(trend_expense)
        regression_forecast = max(0, intercept + slope * len(trend_expense))
        daily_forecast = expense / max(today.day, 1) * end.day
        forecast = round((daily_forecast + regression_forecast) / 2, 2)

        recent = (
            Transaction.query.filter_by(user_id=user.id)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
            .limit(8)
            .all()
        )
        budgets = Budget.query.filter_by(user_id=user.id, month=today.month, year=today.year).all()
        budget_cards = []
        over_budget = []
        near_budget = []
        for b in budgets:
            spent = sum(
                t.amount
                for t in Transaction.query.filter_by(user_id=user.id, category_id=b.category_id, kind="expense").filter(
                    Transaction.txn_date.between(start, end)
                )
            )
            pct = min(100, round(spent / b.amount * 100, 1)) if b.amount else 0
            card = {"budget": b, "spent": spent, "pct": pct}
            budget_cards.append(card)
            if pct >= 100:
                over_budget.append(card)
            elif pct >= 80:
                near_budget.append(card)

        goals = Goal.query.filter_by(user_id=user.id).all()
        insights = build_insights(user, expense, prev_expense, cat_rows, budget_cards)

        return render_template(
            "dashboard.html",
            income=income,
            expense=expense,
            balance=balance,
            savings_rate=savings_rate,
            delta=delta,
            cat_labels=[r[0] for r in cat_rows],
            cat_colors=[r[1] for r in cat_rows],
            cat_values=[round(r[2], 2) for r in cat_rows],
            trend_labels=trend_labels,
            trend_income=trend_income,
            trend_expense=trend_expense,
            forecast=forecast,
            recent=recent,
            budget_cards=budget_cards,
            goals=goals,
            insights=insights,
            over_budget=over_budget,
            near_budget=near_budget,
        )

    @app.route("/transactions")
    @login_required
    def transactions():
        user = current_user()
        q = Transaction.query.filter_by(user_id=user.id)
        kind = request.args.get("kind", "")
        category_id = request.args.get("category", "")
        search = request.args.get("q", "").strip()
        start = request.args.get("start", "")
        end = request.args.get("end", "")
        if kind in {"income", "expense"}:
            q = q.filter_by(kind=kind)
        if category_id:
            try:
                category_id_int = int(category_id)
            except ValueError:
                flash("Choose a valid category filter.", "warning")
                return redirect(url_for("transactions"))
            if valid_user_category(category_id_int, user.id):
                q = q.filter_by(category_id=category_id_int)
        if search:
            like = f"%{search}%"
            conditions = [Transaction.note.ilike(like), Transaction.merchant.ilike(like)]
            try:
                conditions.append(Transaction.amount == float(search))
            except ValueError:
                pass
            q = q.filter(or_(*conditions))
        try:
            if start:
                q = q.filter(Transaction.txn_date >= datetime.strptime(start, "%Y-%m-%d").date())
            if end:
                q = q.filter(Transaction.txn_date <= datetime.strptime(end, "%Y-%m-%d").date())
        except ValueError:
            flash("Use valid dates for the transaction filter.", "warning")
            return redirect(url_for("transactions"))
        rows = q.order_by(Transaction.txn_date.desc(), Transaction.id.desc()).all()
        categories = Category.query.filter((Category.user_id == None) | (Category.user_id == user.id)).order_by(Category.kind, Category.name).all()
        return render_template(
            "transactions.html",
            rows=rows,
            categories=categories,
            filters={"kind": kind, "category": category_id, "q": search, "start": start, "end": end},
        )

    @app.route("/transactions/new", methods=["POST"])
    @login_required
    def create_transaction():
        user = current_user()
        try:
            amount = float(request.form.get("amount") or 0)
        except ValueError:
            amount = 0
        if not math.isfinite(amount) or amount <= 0:
            flash("Enter a valid amount greater than 0.", "danger")
            return redirect(url_for("transactions"))
        try:
            category_id = int(request.form["category_id"])
        except (ValueError, KeyError):
            flash("Invalid category.", "danger")
            return redirect(url_for("transactions"))
        kind = request.form.get("kind", "expense")
        if kind not in ("income", "expense"):
            flash("Invalid transaction type.", "danger")
            return redirect(url_for("transactions"))
        if not valid_user_category(category_id, user.id, kind):
            flash("Choose an available category for this transaction type.", "danger")
            return redirect(url_for("transactions"))
        note = request.form.get("note", "").strip()[:255]
        merchant = request.form.get("merchant", "").strip()[:120]
        payment_method = request.form.get("payment_method", "UPI")[:40]
        if payment_method not in {"UPI", "Card", "Cash", "Net Banking", "Wallet", "Bank"}:
            flash("Choose a supported payment method.", "danger")
            return redirect(url_for("transactions"))
        try:
            txn_date = datetime.strptime(request.form.get("txn_date") or date.today().isoformat(), "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("transactions"))
        txn = Transaction(
            user_id=user.id,
            category_id=category_id,
            amount=amount,
            kind=kind,
            note=note,
            merchant=merchant,
            payment_method=payment_method,
            txn_date=txn_date,
            source=request.form.get("source", "manual"),
            receipt_path=request.form.get("receipt_path", "")[:255],
        )
        db.session.add(txn)
        db.session.commit()
        flash("Transaction saved.", "success")
        next_page = request.form.get("next")
        if next_page not in {"transactions", "dashboard"}:
            next_page = "transactions"
        return redirect(url_for(next_page))

    @app.route("/transactions/<int:txn_id>/edit", methods=["POST"])
    @login_required
    def edit_transaction(txn_id: int):
        txn = Transaction.query.filter_by(id=txn_id, user_id=session["user_id"]).first_or_404()
        try:
            amount = float(request.form.get("amount") or txn.amount)
        except ValueError:
            flash("Invalid amount.", "danger")
            return redirect(url_for("transactions"))
        if not math.isfinite(amount) or amount <= 0:
            flash("Amount must be greater than 0.", "danger")
            return redirect(url_for("transactions"))
        try:
            category_id = int(request.form.get("category_id") or txn.category_id)
        except ValueError:
            flash("Invalid category.", "danger")
            return redirect(url_for("transactions"))
        if not valid_user_category(category_id, session["user_id"], request.form.get("kind", txn.kind)):
            flash("Choose an available category for this transaction.", "danger")
            return redirect(url_for("transactions"))
        kind = request.form.get("kind", txn.kind)
        if kind not in ("income", "expense"):
            flash("Invalid transaction type.", "danger")
            return redirect(url_for("transactions"))
        note = request.form.get("note", "").strip()[:255]
        merchant = request.form.get("merchant", "").strip()[:120]
        payment_method = request.form.get("payment_method", txn.payment_method)[:40]
        if payment_method not in {"UPI", "Card", "Cash", "Net Banking", "Wallet", "Bank"}:
            flash("Choose a supported payment method.", "danger")
            return redirect(url_for("transactions"))
        try:
            txn_date = datetime.strptime(request.form.get("txn_date"), "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for("transactions"))
        txn.amount = amount
        txn.category_id = category_id
        txn.kind = kind
        txn.note = note
        txn.merchant = merchant
        txn.payment_method = payment_method
        txn.txn_date = txn_date
        db.session.commit()
        flash("Transaction updated.", "success")
        return redirect(url_for("transactions"))

    @app.route("/transactions/<int:txn_id>/delete", methods=["POST"])
    @login_required
    def delete_transaction(txn_id: int):
        txn = Transaction.query.filter_by(id=txn_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(txn)
        db.session.commit()
        flash("Transaction removed.", "success")
        return redirect(url_for("transactions"))

    @app.route("/transactions/bulk", methods=["POST"])
    @login_required
    def bulk_transaction_action():
        user = current_user()
        action = request.form.get("action")
        selected_ids = request.form.getlist("selected")
        if not selected_ids:
            flash("No transactions selected.", "warning")
            return redirect(url_for("transactions"))
        try:
            selected_ids = [int(i) for i in selected_ids]
        except ValueError:
            flash("Invalid selection.", "danger")
            return redirect(url_for("transactions"))
        txns = Transaction.query.filter(Transaction.id.in_(selected_ids), Transaction.user_id == user.id).all()
        if action == "delete":
            for txn in txns:
                db.session.delete(txn)
            db.session.commit()
            flash(f"{len(txns)} transaction(s) deleted.", "success")
        elif action == "change_category":
            try:
                new_category_id = int(request.form.get("new_category_id"))
            except (ValueError, TypeError):
                flash("Invalid category.", "danger")
                return redirect(url_for("transactions"))
            if not valid_user_category(new_category_id, user.id):
                flash("Choose one of your available categories.", "danger")
                return redirect(url_for("transactions"))
            for txn in txns:
                txn.category_id = new_category_id
            db.session.commit()
            flash(f"{len(txns)} transaction(s) updated.", "success")
        else:
            flash("Invalid action.", "danger")
        return redirect(url_for("transactions"))

    @app.route("/scan")
    @login_required
    def scan():
        user = current_user()
        categories = Category.query.filter(
            (Category.kind == "expense"),
            ((Category.user_id == None) | (Category.user_id == user.id))
        ).order_by(Category.name).all()
        return render_template("scan.html", categories=categories)

    @app.route("/scan/parse", methods=["POST"])
    @login_required
    def scan_parse():
        text = request.json.get("text", "") if request.is_json else request.form.get("text", "")
        parsed = parse_receipt_text(text)
        user = current_user()
        cats = category_map(user.id)
        category = cats.get(parsed["category"].lower()) or cats.get("other")
        parsed["category_id"] = category.id if category else None
        parsed["category_name"] = category.name if category else "Other"
        return jsonify(parsed)

    @app.route("/scan/upload", methods=["POST"])
    @login_required
    def scan_upload():
        file = request.files.get("receipt")
        if not file or not file.filename:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_RECEIPTS:
            return jsonify({"ok": False, "error": "Use a JPG, PNG or WEBP photo"}), 400
        filename = f"{uuid.uuid4().hex}{ext}"
        path = Config.UPLOAD_FOLDER / filename
        file.save(path)
        return jsonify({"ok": True, "path": f"uploads/receipts/{filename}"})

    @app.route("/budgets", methods=["GET", "POST"])
    @login_required
    def budgets():
        user = current_user()
        today = date.today()
        if request.method == "POST":
            try:
                category_id = int(request.form["category_id"])
            except (ValueError, KeyError):
                flash("Invalid category.", "danger")
                return redirect(url_for("budgets"))
            if not valid_user_category(category_id, user.id, "expense"):
                flash("Choose one of your available expense categories.", "danger")
                return redirect(url_for("budgets"))
            try:
                amount = float(request.form["amount"])
            except (ValueError, KeyError):
                flash("Invalid amount.", "danger")
                return redirect(url_for("budgets"))
            if not math.isfinite(amount) or amount <= 0:
                flash("Budget amount must be greater than 0.", "danger")
                return redirect(url_for("budgets"))
            existing = Budget.query.filter_by(
                user_id=user.id,
                category_id=category_id,
                month=today.month,
                year=today.year,
            ).first()
            if existing:
                existing.amount = amount
            else:
                db.session.add(
                    Budget(
                        user_id=user.id,
                        category_id=category_id,
                        month=today.month,
                        year=today.year,
                        amount=amount,
                    )
                )
            db.session.commit()
            flash("Budget saved for this month.", "success")
            return redirect(url_for("budgets"))

        start, end = month_bounds(today.year, today.month)
        rows = []
        over_budget = []
        near_budget = []
        for b in Budget.query.filter_by(user_id=user.id, month=today.month, year=today.year).all():
            spent = sum(
                t.amount
                for t in Transaction.query.filter_by(user_id=user.id, category_id=b.category_id, kind="expense").filter(
                    Transaction.txn_date.between(start, end)
                )
            )
            pct = min(100, spent / b.amount * 100) if b.amount else 0
            row = {"budget": b, "spent": spent, "pct": pct}
            rows.append(row)
            if pct >= 100:
                over_budget.append(row)
            elif pct >= 80:
                near_budget.append(row)
        categories = Category.query.filter(
            (Category.kind == "expense"),
            ((Category.user_id == None) | (Category.user_id == user.id))
        ).order_by(Category.name).all()
        return render_template("budgets.html", rows=rows, categories=categories, month=today.strftime("%B %Y"), over_budget=over_budget, near_budget=near_budget)

    @app.route("/budgets/<int:budget_id>/delete", methods=["POST"])
    @login_required
    def delete_budget(budget_id: int):
        row = Budget.query.filter_by(id=budget_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(row)
        db.session.commit()
        flash("Budget removed.", "success")
        return redirect(url_for("budgets"))

    @app.route("/reports")
    @login_required
    def reports():
        user = current_user()
        try:
            year = int(request.args.get("year", date.today().year))
            if not 2000 <= year <= date.today().year + 1:
                raise ValueError
        except ValueError:
            flash("Choose a valid report year.", "warning")
            return redirect(url_for("reports"))
        month = request.args.get("month", "")
        if month and (not month.isdigit() or not 1 <= int(month) <= 12):
            flash("Choose a valid month.", "warning")
            return redirect(url_for("reports", year=year))
        q = Transaction.query.filter_by(user_id=user.id).filter(extract("year", Transaction.txn_date) == year)
        if month:
            q = q.filter(extract("month", Transaction.txn_date) == int(month))
        txns = q.all()
        income = sum(t.amount for t in txns if t.kind == "income")
        expense = sum(t.amount for t in txns if t.kind == "expense")
        by_cat = {}
        by_method = {}
        calendar = {}
        for t in txns:
            if t.kind == "expense":
                by_cat[t.category.name] = by_cat.get(t.category.name, 0) + t.amount
                by_method[t.payment_method] = by_method.get(t.payment_method, 0) + t.amount
                key = t.txn_date.isoformat()
                calendar[key] = calendar.get(key, 0) + t.amount
        monthly = []
        for m in range(1, 13):
            s, e = month_bounds(year, m)
            subset = [t for t in Transaction.query.filter_by(user_id=user.id).filter(Transaction.txn_date.between(s, e))]
            monthly.append(
                {
                    "label": s.strftime("%b"),
                    "income": round(sum(t.amount for t in subset if t.kind == "income"), 2),
                    "expense": round(sum(t.amount for t in subset if t.kind == "expense"), 2),
                }
            )
        years = sorted({t.txn_date.year for t in Transaction.query.filter_by(user_id=user.id)}, reverse=True) or [year]
        weekdays = [0.0] * 7
        merchants = {}
        for txn in txns:
            if txn.kind == "expense":
                weekdays[txn.txn_date.weekday()] += txn.amount
                name = txn.merchant or "Unknown merchant"
                merchants[name] = merchants.get(name, 0) + txn.amount
        comparison = []
        if month:
            current_month = int(month)
            previous_year, previous_month = (year - 1, 12) if current_month == 1 else (year, current_month - 1)
            pstart, pend = month_bounds(previous_year, previous_month)
            previous = {}
            for txn in Transaction.query.filter_by(user_id=user.id, kind="expense").filter(Transaction.txn_date.between(pstart, pend)).all():
                previous[txn.category.name] = previous.get(txn.category.name, 0) + txn.amount
            for name in sorted(set(by_cat) | set(previous)):
                old, new = previous.get(name, 0), by_cat.get(name, 0)
                comparison.append((name, old, new, new-old, ((new-old)/old*100 if old else (100 if new else 0))))
        today = date.today()
        month_start, month_end = month_bounds(today.year, today.month)
        elapsed_days = max(today.day, 1)
        current_month_expense = sum(t.amount for t in Transaction.query.filter_by(user_id=user.id, kind="expense").filter(Transaction.txn_date.between(month_start, today)).all())
        daily_projection = current_month_expense / elapsed_days * month_end.day
        monthly_values = [row["expense"] for row in monthly]
        slope, intercept = linear_regression(monthly_values)
        forecast = round(max(0, (daily_projection + intercept + slope * len(monthly_values)) / 2), 2)
        user_expenses = Transaction.query.filter_by(user_id=user.id, kind="expense").all()
        totals = {}
        for txn in user_expenses:
            totals.setdefault(txn.category_id, []).append(txn)
        anomalies = []
        for txn in txns:
            history_for_category = [entry.amount for entry in totals.get(txn.category_id, []) if entry.txn_date < txn.txn_date]
            if txn.kind == "expense" and len(history_for_category) >= 2:
                mean = sum(history_for_category) / len(history_for_category)
                stdev = (sum((v-mean)**2 for v in history_for_category) / len(history_for_category)) ** .5
                if txn.amount > mean + 2*stdev:
                    anomalies.append(txn)
        this_month_income = sum(t.amount for t in Transaction.query.filter_by(user_id=user.id, kind="income").filter(Transaction.txn_date.between(month_start, today)).all())
        savings_rate = max(0, min(100, (this_month_income-current_month_expense)/this_month_income*100 if this_month_income else 0))
        budget_rows = Budget.query.filter_by(user_id=user.id, month=today.month, year=today.year).all()
        adherence = []
        for budget in budget_rows:
            spent = sum(t.amount for t in Transaction.query.filter_by(user_id=user.id, category_id=budget.category_id, kind="expense").filter(Transaction.txn_date.between(month_start, today)).all())
            adherence.append(min(100, budget.amount/spent*100) if spent > budget.amount else 100)
        budget_score = sum(adherence)/len(adherence) if adherence else 60
        goals = Goal.query.filter_by(user_id=user.id).all()
        goal_score = sum(min(100, g.saved_amount/g.target_amount*100) for g in goals)/len(goals) if goals else 50
        health_score = round(savings_rate*.4 + budget_score*.35 + goal_score*.25)
        return render_template(
            "reports.html",
            year=year,
            month=month,
            years=years,
            income=income,
            expense=expense,
            net=income - expense,
            by_cat=by_cat,
            by_method=by_method,
            monthly=monthly,
            calendar=calendar,
            comparison=comparison,
            weekdays=weekdays,
            top_merchants=sorted(merchants.items(), key=lambda item: item[1], reverse=True)[:8],
            top_merchant_labels=[item[0] for item in sorted(merchants.items(), key=lambda item: item[1], reverse=True)[:8]],
            top_merchant_values=[item[1] for item in sorted(merchants.items(), key=lambda item: item[1], reverse=True)[:8]],
            forecast=forecast,
            anomalies=anomalies,
            health_score=health_score,
            health_tips=["Save a small amount as soon as income arrives.", "Review categories approaching their budget.", "Set a clear target and deadline for one savings goal."],
        )

    @app.route("/reports/export")
    @login_required
    def export_csv():
        user = current_user()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Type", "Category", "Merchant", "Amount", "Payment", "Note", "Source"])
        rows = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.txn_date.desc()).all()
        for t in rows:
            writer.writerow([t.txn_date, t.kind, t.category.name, t.merchant, t.amount, t.payment_method, t.note, t.source])
        mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="aureum-transactions.csv")

    @app.route("/reports/export.xlsx")
    @login_required
    def export_xlsx():
        from openpyxl import Workbook
        user = current_user()
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Transactions"
        sheet.append(["Date", "Type", "Category", "Merchant", "Amount", "Payment", "Note", "Source"])
        for t in Transaction.query.filter_by(user_id=user.id).order_by(Transaction.txn_date.desc()).all():
            sheet.append([t.txn_date.isoformat(), t.kind, t.category.name, t.merchant, t.amount, t.payment_method, t.note, t.source])
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="aureum-transactions.xlsx")

    @app.route("/reports/pdf")
    @login_required
    def export_pdf():
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        user = current_user()
        year_value = request.args.get("year", type=int)
        month_value = request.args.get("month", type=int)
        query = Transaction.query.filter_by(user_id=user.id)
        if year_value and 2000 <= year_value <= date.today().year + 1:
            query = query.filter(extract("year", Transaction.txn_date) == year_value)
        if month_value and 1 <= month_value <= 12:
            query = query.filter(extract("month", Transaction.txn_date) == month_value)
        rows = query.order_by(Transaction.txn_date.desc()).limit(1000).all()
        income_total = sum(t.amount for t in rows if t.kind == "income")
        expense_total = sum(t.amount for t in rows if t.kind == "expense")
        top_expenses = sorted((t for t in rows if t.kind == "expense"), key=lambda t: t.amount, reverse=True)[:5]
        output = io.BytesIO()
        page = canvas.Canvas(output, pagesize=letter)
        page.setTitle("Aureum financial report")
        page.setFont("Helvetica-Bold", 18)
        page.drawString(48, 748, "Aureum Financial Report")
        page.setFont("Helvetica", 10)
        page.drawString(48, 728, f"{user.name} - Generated {date.today().isoformat()} - Latest 100 transactions")
        page.drawString(48, 708, f"Income: {income_total:,.2f}       Expenses: {expense_total:,.2f}       Net: {income_total-expense_total:,.2f}")
        # A small vector bar chart keeps the PDF self-contained.
        max_amount = max(income_total, expense_total, 1)
        page.setFillColorRGB(.12, .65, .48)
        page.rect(60, 625, 180 * income_total / max_amount, 18, fill=1, stroke=0)
        page.setFillColorRGB(.92, .38, .35)
        page.rect(60, 595, 180 * expense_total / max_amount, 18, fill=1, stroke=0)
        page.setFillColorRGB(0, 0, 0)
        page.drawString(250, 630, "Income")
        page.drawString(250, 600, "Expenses")
        page.setFont("Helvetica-Bold", 10)
        page.drawString(48, 565, "Top expenses")
        page.setFont("Helvetica", 9)
        y = 548
        for txn in top_expenses:
            page.drawString(48, y, f"{txn.txn_date}  {txn.merchant or txn.category.name}  {txn.amount:,.2f}")
            y -= 14
        y = 700
        page.setFont("Helvetica-Bold", 9)
        page.drawString(48, y, "Date       Type       Category             Merchant                 Amount")
        page.setFont("Helvetica", 8)
        for t in rows:
            y -= 15
            if y < 45:
                page.showPage()
                y = 750
            page.drawString(48, y, f"{t.txn_date}  {t.kind:<8} {t.category.name[:18]:<19} {(t.merchant or t.note)[:24]:<25} {t.amount:,.2f}")
        page.save()
        output.seek(0)
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="aureum-report.pdf")

    @app.route("/reports/print")
    @login_required
    def printable_report():
        user = current_user()
        rows = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.txn_date.desc()).limit(200).all()
        return render_template("print_report.html", rows=rows)

    @app.route("/reports/import", methods=["GET", "POST"])
    @login_required
    def import_csv():
        if request.method == "GET":
            return render_template("import.html", headers=[], sample=[])
        file = request.files.get("file")
        if not file or not file.filename.lower().endswith(".csv"):
            flash("Choose a CSV file to import.", "danger")
            return redirect(url_for("import_csv"))
        try:
            rows = list(csv.DictReader(io.StringIO(file.stream.read().decode("utf-8-sig"))))
        except (UnicodeDecodeError, csv.Error):
            flash("That CSV could not be read. Save it as UTF-8 and try again.", "danger")
            return redirect(url_for("import_csv"))
        headers = list(rows[0].keys()) if rows else []
        if not headers:
            flash("The CSV has no transaction rows.", "warning")
            return redirect(url_for("import_csv"))
        mappings = {key: request.form.get(key, "") for key in ("date", "amount", "type", "category", "merchant", "payment", "note")}
        if request.form.get("confirm") != "yes":
            return render_template("import.html", headers=headers, sample=rows[:5], mappings=mappings)
        if any(value not in headers for key, value in mappings.items() if key in {"date", "amount"}):
            flash("Map at least the date and amount columns.", "danger")
            return render_template("import.html", headers=headers, sample=rows[:5], mappings=mappings)
        user = current_user()
        cats = category_map(user.id)
        fallback = cats.get("other")
        added = skipped = 0
        for row in rows:
            try:
                amount = float(row[mappings["amount"]].replace(",", "").replace("₹", "").strip())
                txn_date = datetime.strptime(row[mappings["date"]].strip(), "%Y-%m-%d").date()
                if amount <= 0:
                    raise ValueError
            except (ValueError, TypeError, KeyError, AttributeError):
                skipped += 1
                continue
            kind = (row.get(mappings.get("type", ""), "expense") or "expense").lower()
            if kind not in {"income", "expense"}:
                skipped += 1
                continue
            category_name = (row.get(mappings.get("category", ""), "") or "").strip().lower()
            category = cats.get(category_name) or fallback
            if not category or not valid_user_category(category.id, user.id):
                skipped += 1
                continue
            merchant = (row.get(mappings.get("merchant", ""), "") or "")[:120]
            note = (row.get(mappings.get("note", ""), "") or "")[:255]
            payment = (row.get(mappings.get("payment", ""), "") or "UPI")[:40]
            fingerprint = hashlib.sha256(f"{user.id}|{txn_date}|{kind}|{category.id}|{amount:.2f}|{merchant}|{note}".encode()).hexdigest()
            duplicate = ImportBatch.query.filter_by(user_id=user.id, fingerprint=fingerprint).first()
            duplicate = duplicate or Transaction.query.filter_by(user_id=user.id, txn_date=txn_date, kind=kind, category_id=category.id, amount=amount, merchant=merchant, note=note).first()
            if duplicate:
                skipped += 1
                continue
            db.session.add(Transaction(user_id=user.id, category_id=category.id, amount=amount, kind=kind, txn_date=txn_date,
                                       merchant=merchant, note=note, payment_method=payment, source="import"))
            db.session.add(ImportBatch(user_id=user.id, fingerprint=fingerprint))
            added += 1
        db.session.commit()
        flash(f"Imported {added} transaction(s); skipped {skipped} invalid or duplicate row(s).", "success")
        return redirect(url_for("transactions"))

    @app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        user = current_user()
        if request.method == "POST":
            name = request.form.get("name", "").strip()[:120]
            if not name:
                flash("Goal name is required.", "danger")
                return redirect(url_for("goals"))
            try:
                target_amount = float(request.form["target_amount"])
            except (ValueError, KeyError):
                flash("Invalid target amount.", "danger")
                return redirect(url_for("goals"))
            if not math.isfinite(target_amount) or target_amount <= 0:
                flash("Target amount must be greater than 0.", "danger")
                return redirect(url_for("goals"))
            try:
                saved_amount = float(request.form.get("saved_amount") or 0)
            except (ValueError, TypeError):
                saved_amount = 0
            if not math.isfinite(saved_amount) or saved_amount < 0:
                flash("Saved amount cannot be negative.", "danger")
                return redirect(url_for("goals"))
            deadline = request.form.get("deadline") or None
            if deadline:
                try:
                    deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    flash("Invalid deadline date.", "danger")
                    return redirect(url_for("goals"))
            db.session.add(
                Goal(
                    user_id=user.id,
                    name=name,
                    target_amount=target_amount,
                    saved_amount=saved_amount,
                    deadline=deadline,
                )
            )
            db.session.commit()
            flash("Savings goal created.", "success")
            return redirect(url_for("goals"))
        items = Goal.query.filter_by(user_id=user.id).order_by(Goal.created_at.desc()).all()
        return render_template("goals.html", items=items)

    @app.route("/goals/<int:goal_id>/save", methods=["POST"])
    @login_required
    def add_to_goal(goal_id: int):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        try:
            amount = float(request.form.get("amount") or 0)
        except ValueError:
            flash("Invalid amount.", "danger")
            return redirect(url_for("goals"))
        if not math.isfinite(amount) or amount <= 0:
            flash("Amount must be greater than 0.", "danger")
            return redirect(url_for("goals"))
        goal.saved_amount += amount
        db.session.commit()
        flash("Saved towards your goal.", "success")
        return redirect(url_for("goals"))

    @app.route("/goals/<int:goal_id>/delete", methods=["POST"])
    @login_required
    def delete_goal(goal_id: int):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(goal)
        db.session.commit()
        return redirect(url_for("goals"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user = current_user()
        if request.method == "POST":
            if request.form.get("delete_account") == "yes":
                if not check_password_hash(user.password_hash, request.form.get("current_password", "")):
                    flash("Enter your current password to delete the account.", "danger")
                    return render_template("profile.html", user=user)
                for model in (Transaction, Budget, Goal, RecurringTransaction, Transfer, ImportBatch):
                    model.query.filter_by(user_id=user.id).delete(synchronize_session=False)
                Category.query.filter_by(user_id=user.id).delete(synchronize_session=False)
                db.session.delete(user)
                db.session.commit()
                session.clear()
                flash("Your account has been deleted.", "success")
                return redirect(url_for("login"))
            name = request.form.get("name", user.name).strip()[:120]
            if not name:
                flash("Name is required.", "danger")
                return render_template("profile.html", user=user)
            user.name = name
            user.phone = request.form.get("phone", "").strip()[:20]
            try:
                monthly_income = float(request.form.get("monthly_income") or 0)
            except ValueError:
                flash("Invalid monthly income.", "danger")
                return render_template("profile.html", user=user)
            if not math.isfinite(monthly_income) or monthly_income < 0:
                flash("Monthly income cannot be negative.", "danger")
                return render_template("profile.html", user=user)
            user.monthly_income = monthly_income
            currency = request.form.get("currency", "INR")
            if currency not in {"INR", "USD", "EUR", "GBP"}:
                flash("Choose a supported currency.", "danger")
                return render_template("profile.html", user=user)
            user.currency = currency
            user.theme = "light" if request.form.get("theme") == "light" else "dark"
            new_password = request.form.get("password", "")
            if new_password:
                if not check_password_hash(user.password_hash, request.form.get("current_password", "")):
                    flash("Enter your current password before changing it.", "danger")
                    return render_template("profile.html", user=user)
                valid, msg = validate_password(new_password)
                if not valid:
                    flash(msg, "danger")
                    return render_template("profile.html", user=user)
                user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", user=user)

    @app.route("/recurring", methods=["GET", "POST"])
    @login_required
    def recurring():
        user = current_user()
        if request.method == "POST":
            try:
                category_id = int(request.form["category_id"])
            except (ValueError, KeyError):
                flash("Invalid category.", "danger")
                return redirect(url_for("recurring"))
            if not valid_user_category(category_id, user.id, request.form.get("kind", "expense")):
                flash("Choose an available category for this recurring transaction.", "danger")
                return redirect(url_for("recurring"))
            try:
                amount = float(request.form["amount"])
            except (ValueError, KeyError):
                flash("Invalid amount.", "danger")
                return redirect(url_for("recurring"))
            if not math.isfinite(amount) or amount <= 0:
                flash("Amount must be greater than 0.", "danger")
                return redirect(url_for("recurring"))
            kind = request.form.get("kind", "expense")
            if kind not in ("income", "expense"):
                flash("Invalid transaction type.", "danger")
                return redirect(url_for("recurring"))
            frequency = request.form.get("frequency", "monthly")
            if frequency not in ("daily", "weekly", "monthly", "yearly"):
                flash("Invalid frequency.", "danger")
                return redirect(url_for("recurring"))
            try:
                next_due_date = datetime.strptime(request.form.get("next_due_date"), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                flash("Invalid date format.", "danger")
                return redirect(url_for("recurring"))
            db.session.add(
                RecurringTransaction(
                    user_id=user.id,
                    category_id=category_id,
                    amount=amount,
                    kind=kind,
                    note=request.form.get("note", "").strip()[:255],
                    merchant=request.form.get("merchant", "").strip()[:120],
                    payment_method=request.form.get("payment_method", "UPI")[:40],
                    frequency=frequency,
                    next_due_date=next_due_date,
                )
            )
            db.session.commit()
            flash("Recurring transaction created.", "success")
            return redirect(url_for("recurring"))
        items = RecurringTransaction.query.filter_by(user_id=user.id).order_by(RecurringTransaction.next_due_date).all()
        categories = Category.query.filter((Category.user_id == None) | (Category.user_id == user.id)).order_by(Category.kind, Category.name).all()
        return render_template("recurring.html", items=items, categories=categories)

    @app.route("/recurring/<int:rec_id>/pause", methods=["POST"])
    @login_required
    def pause_recurring(rec_id: int):
        rec = RecurringTransaction.query.filter_by(id=rec_id, user_id=session["user_id"]).first_or_404()
        rec.is_active = False
        db.session.commit()
        flash("Recurring transaction paused.", "success")
        return redirect(url_for("recurring"))

    @app.route("/recurring/<int:rec_id>/resume", methods=["POST"])
    @login_required
    def resume_recurring(rec_id: int):
        rec = RecurringTransaction.query.filter_by(id=rec_id, user_id=session["user_id"]).first_or_404()
        rec.is_active = True
        db.session.commit()
        flash("Recurring transaction resumed.", "success")
        return redirect(url_for("recurring"))

    @app.route("/recurring/<int:rec_id>/delete", methods=["POST"])
    @login_required
    def delete_recurring(rec_id: int):
        rec = RecurringTransaction.query.filter_by(id=rec_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(rec)
        db.session.commit()
        flash("Recurring transaction deleted.", "success")
        return redirect(url_for("recurring"))

    @app.route("/categories", methods=["GET", "POST"])
    @login_required
    def categories():
        user = current_user()
        if request.method == "POST":
            name = request.form.get("name", "").strip()[:80]
            if not name:
                flash("Category name is required.", "danger")
                return redirect(url_for("categories"))
            kind = request.form.get("kind", "expense")
            if kind not in ("income", "expense"):
                flash("Invalid category type.", "danger")
                return redirect(url_for("categories"))
            existing = Category.query.filter_by(user_id=user.id, name=name).first()
            if existing:
                flash("You already have a category with this name.", "danger")
                return redirect(url_for("categories"))
            color = request.form.get("color", "#3ee0b0")
            if not valid_color(color):
                flash("Choose a valid six-digit color.", "danger")
                return redirect(url_for("categories"))
            db.session.add(
                Category(
                    user_id=user.id,
                    name=name,
                    kind=kind,
                    icon=request.form.get("icon", "bi-tag")[:40],
                    color=color,
                )
            )
            db.session.commit()
            flash("Category created.", "success")
            return redirect(url_for("categories"))
        default_cats = Category.query.filter_by(user_id=None).order_by(Category.kind, Category.name).all()
        user_cats = Category.query.filter_by(user_id=user.id).order_by(Category.kind, Category.name).all()
        return render_template("categories.html", default_cats=default_cats, user_cats=user_cats)

    @app.route("/categories/<int:cat_id>/edit", methods=["POST"])
    @login_required
    def edit_category(cat_id: int):
        cat = Category.query.filter_by(id=cat_id, user_id=session["user_id"]).first_or_404()
        name = request.form.get("name", "").strip()[:80]
        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("categories"))
        if name != cat.name:
            existing = Category.query.filter_by(user_id=session["user_id"], name=name).first()
            if existing:
                flash("You already have a category with this name.", "danger")
                return redirect(url_for("categories"))
        color = request.form.get("color", cat.color)
        if not valid_color(color):
            flash("Choose a valid six-digit color.", "danger")
            return redirect(url_for("categories"))
        cat.name = name
        cat.icon = request.form.get("icon", cat.icon)[:40]
        cat.color = color
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("categories"))

    @app.route("/categories/<int:cat_id>/delete", methods=["POST"])
    @login_required
    def delete_category(cat_id: int):
        cat = Category.query.filter_by(id=cat_id, user_id=session["user_id"]).first_or_404()
        if Transaction.query.filter_by(category_id=cat_id).first():
            flash("Cannot delete category with transactions. Move or delete transactions first.", "danger")
            return redirect(url_for("categories"))
        db.session.delete(cat)
        db.session.commit()
        flash("Category deleted.", "success")
        return redirect(url_for("categories"))

    @app.route("/transfers", methods=["GET", "POST"])
    @login_required
    def transfers():
        user = current_user()
        if request.method == "POST":
            try:
                amount = float(request.form["amount"])
            except (ValueError, KeyError):
                flash("Invalid amount.", "danger")
                return redirect(url_for("transfers"))
            if not math.isfinite(amount) or amount <= 0:
                flash("Amount must be greater than 0.", "danger")
                return redirect(url_for("transfers"))
            from_method = request.form.get("from_method", "Cash")[:40]
            to_method = request.form.get("to_method", "UPI")[:40]
            if from_method not in {"Cash", "UPI", "Card", "Bank", "Net Banking", "Wallet"} or to_method not in {"Cash", "UPI", "Card", "Bank", "Net Banking", "Wallet"}:
                flash("Choose a supported payment method.", "danger")
                return redirect(url_for("transfers"))
            if from_method == to_method:
                flash("From and to payment methods must be different.", "danger")
                return redirect(url_for("transfers"))
            try:
                txn_date = datetime.strptime(request.form.get("txn_date") or date.today().isoformat(), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                flash("Invalid date format.", "danger")
                return redirect(url_for("transfers"))
            db.session.add(
                Transfer(
                    user_id=user.id,
                    from_method=from_method,
                    to_method=to_method,
                    amount=amount,
                    txn_date=txn_date,
                    note=request.form.get("note", "").strip()[:255],
                )
            )
            db.session.commit()
            flash("Transfer recorded.", "success")
            return redirect(url_for("transfers"))
        transfers = Transfer.query.filter_by(user_id=user.id).order_by(Transfer.txn_date.desc(), Transfer.id.desc()).limit(20).all()
        balances = {}
        default_methods = ["Cash", "UPI", "Card", "Bank", "Net Banking", "Wallet"]
        for method in default_methods:
            balance = sum(t.amount for t in Transaction.query.filter_by(user_id=user.id, payment_method=method, kind="income").all())
            balance -= sum(t.amount for t in Transaction.query.filter_by(user_id=user.id, payment_method=method, kind="expense").all())
            balance += sum(t.amount for t in Transfer.query.filter_by(user_id=user.id, to_method=method).all())
            balance -= sum(t.amount for t in Transfer.query.filter_by(user_id=user.id, from_method=method).all())
            if balance != 0:
                balances[method] = balance
        return render_template("transfers.html", transfers=transfers, balances=balances, default_methods=default_methods)

    @app.route("/transfers/<int:transfer_id>/delete", methods=["POST"])
    @login_required
    def delete_transfer(transfer_id: int):
        transfer = Transfer.query.filter_by(id=transfer_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(transfer)
        db.session.commit()
        flash("Transfer deleted.", "success")
        return redirect(url_for("transfers"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500


def build_insights(user, expense, prev_expense, cat_rows, budget_cards):
    insights = []
    if prev_expense:
        change = (expense - prev_expense) / prev_expense * 100
        if change > 8:
            insights.append(f"Spending is {change:.0f}% higher than last month. A quiet week can reverse the curve.")
        elif change < -8:
            insights.append(f"Nice discipline — spending dropped {abs(change):.0f}% versus last month.")
        else:
            insights.append("This month is tracking close to last month. Consistency is a superpower.")
    if cat_rows:
        top = cat_rows[0]
        insights.append(f"{top[0]} is your largest category this month at {money(top[2])}.")
    over = [c for c in budget_cards if c["pct"] >= 90]
    if over:
        insights.append(f"{over[0]['budget'].category.name} is at {over[0]['pct']:.0f}% of its budget.")
    if user.monthly_income and expense:
        left = user.monthly_income - expense
        insights.append(f"Of your stated income, {money(max(left, 0))} is still unspent this month.")
    if not insights:
        insights.append("Add a few transactions or scan a bill — Aureum will start telling your money story.")
    return insights[:4]


def seed_demo_data(user: User) -> None:
    cats = {c.name: c for c in Category.query.filter_by(user_id=None).all()}
    today = date.today()
    samples = [
        ("Salary", "income", user.monthly_income or 45000, today.replace(day=1), "Company payroll", "Salary", "Bank"),
        ("Food", "expense", 280, today - timedelta(days=1), "Lunch at Third Wave", "Swiggy", "UPI"),
        ("Travel", "expense", 164, today - timedelta(days=1), "Office commute", "Uber", "UPI"),
        ("Groceries", "expense", 1860, today - timedelta(days=3), "Weekly vegetables", "DMart", "Card"),
        ("Entertainment", "expense", 199, today - timedelta(days=4), "Music plan", "Spotify", "UPI"),
        ("Shopping", "expense", 1299, today - timedelta(days=6), "Sneakers sale", "Myntra", "UPI"),
        ("Education", "expense", 499, today - timedelta(days=8), "Python course", "Udemy", "Card"),
        ("Bills", "expense", 699, today - timedelta(days=10), "Fiber broadband", "Airtel", "UPI"),
        ("Health", "expense", 320, today - timedelta(days=12), "Pharmacy run", "Apollo", "Cash"),
        ("Food", "expense", 540, today - timedelta(days=14), "Weekend dinner", "Truffles", "UPI"),
        ("Freelance", "income", 8000, today - timedelta(days=16), "Logo design gig", "Client", "Bank"),
        ("Travel", "expense", 2100, today - timedelta(days=20), "Home trip", "IRCTC", "UPI"),
    ]
    for cat, kind, amount, day, note, merchant, method in samples:
        db.session.add(
            Transaction(
                user_id=user.id,
                category_id=cats[cat].id,
                amount=amount,
                kind=kind,
                note=note,
                merchant=merchant,
                payment_method=method,
                txn_date=day,
                source="demo",
            )
        )
    db.session.add(Budget(user_id=user.id, category_id=cats["Food"].id, month=today.month, year=today.year, amount=6000))
    db.session.add(Budget(user_id=user.id, category_id=cats["Travel"].id, month=today.month, year=today.year, amount=3000))
    db.session.add(Budget(user_id=user.id, category_id=cats["Shopping"].id, month=today.month, year=today.year, amount=4000))
    db.session.add(Goal(user_id=user.id, name="Emergency fund", target_amount=50000, saved_amount=12500, deadline=today.replace(month=12) if today.month < 12 else today))
    db.session.add(Goal(user_id=user.id, name="New laptop", target_amount=65000, saved_amount=18000, deadline=None))
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
