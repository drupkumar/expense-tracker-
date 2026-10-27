from __future__ import annotations

import csv
import io
import os
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
from sqlalchemy import extract, func, or_
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import Budget, Category, Goal, Transaction, User, db
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


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_categories()

    register_routes(app)
    return app


def seed_categories() -> None:
    if Category.query.count():
        return
    for name, kind, icon, color in DEFAULT_CATEGORIES:
        db.session.add(Category(name=name, kind=kind, icon=icon, color=color))
    db.session.commit()


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


def category_map() -> dict[str, Category]:
    return {c.name.lower(): c for c in Category.query.all()}


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        user = current_user()
        return {
            "current_user": user,
            "money": money,
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
            if not name or not email or len(password) < 6:
                flash("Name, email and a password of 6+ characters are required.", "danger")
                return render_template("register.html")
            try:
                if User.query.filter_by(email=email).first():
                    flash("That email is already registered.", "danger")
                    return render_template("register.html")
                user = User(name=name, email=email, password_hash=generate_password_hash(password))
                db.session.add(user)
                db.session.commit()
                session["user_id"] = user.id
                flash("Welcome to Aureum. Your ledger is ready.", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                db.session.rollback()
                flash(f"Registration failed: {str(e)}", "danger")
                return render_template("register.html")
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "danger")
                return render_template("login.html")
            session["user_id"] = user.id
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
        flash("Demo mode: This is a sample account. Create your own account to save your data permanently.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Signed out. Your numbers stay private.", "success")
        return redirect(url_for("login"))

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

        recent = (
            Transaction.query.filter_by(user_id=user.id)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
            .limit(8)
            .all()
        )
        budgets = Budget.query.filter_by(user_id=user.id, month=today.month, year=today.year).all()
        budget_cards = []
        for b in budgets:
            spent = sum(
                t.amount
                for t in Transaction.query.filter_by(user_id=user.id, category_id=b.category_id, kind="expense").filter(
                    Transaction.txn_date.between(start, end)
                )
            )
            pct = min(100, round(spent / b.amount * 100, 1)) if b.amount else 0
            budget_cards.append({"budget": b, "spent": spent, "pct": pct})

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
            recent=recent,
            budget_cards=budget_cards,
            goals=goals,
            insights=insights,
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
            q = q.filter_by(category_id=int(category_id))
        if search:
            like = f"%{search}%"
            q = q.filter(or_(Transaction.note.ilike(like), Transaction.merchant.ilike(like)))
        if start:
            q = q.filter(Transaction.txn_date >= datetime.strptime(start, "%Y-%m-%d").date())
        if end:
            q = q.filter(Transaction.txn_date <= datetime.strptime(end, "%Y-%m-%d").date())
        rows = q.order_by(Transaction.txn_date.desc(), Transaction.id.desc()).all()
        categories = Category.query.order_by(Category.kind, Category.name).all()
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
        if amount <= 0:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("transactions"))
        txn = Transaction(
            user_id=user.id,
            category_id=int(request.form["category_id"]),
            amount=amount,
            kind=request.form.get("kind", "expense"),
            note=request.form.get("note", "").strip(),
            merchant=request.form.get("merchant", "").strip(),
            payment_method=request.form.get("payment_method", "UPI"),
            txn_date=datetime.strptime(request.form.get("txn_date") or date.today().isoformat(), "%Y-%m-%d").date(),
            source=request.form.get("source", "manual"),
            receipt_path=request.form.get("receipt_path", ""),
        )
        db.session.add(txn)
        db.session.commit()
        flash("Transaction saved.", "success")
        next_page = request.form.get("next") or "transactions"
        return redirect(url_for(next_page))

    @app.route("/transactions/<int:txn_id>/edit", methods=["POST"])
    @login_required
    def edit_transaction(txn_id: int):
        txn = Transaction.query.filter_by(id=txn_id, user_id=session["user_id"]).first_or_404()
        txn.amount = float(request.form.get("amount") or txn.amount)
        txn.category_id = int(request.form.get("category_id") or txn.category_id)
        txn.kind = request.form.get("kind", txn.kind)
        txn.note = request.form.get("note", "").strip()
        txn.merchant = request.form.get("merchant", "").strip()
        txn.payment_method = request.form.get("payment_method", txn.payment_method)
        txn.txn_date = datetime.strptime(request.form.get("txn_date"), "%Y-%m-%d").date()
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

    @app.route("/scan")
    @login_required
    def scan():
        categories = Category.query.filter_by(kind="expense").order_by(Category.name).all()
        return render_template("scan.html", categories=categories)

    @app.route("/scan/parse", methods=["POST"])
    @login_required
    def scan_parse():
        text = request.json.get("text", "") if request.is_json else request.form.get("text", "")
        parsed = parse_receipt_text(text)
        cats = category_map()
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
            existing = Budget.query.filter_by(
                user_id=user.id,
                category_id=int(request.form["category_id"]),
                month=today.month,
                year=today.year,
            ).first()
            if existing:
                existing.amount = float(request.form["amount"])
            else:
                db.session.add(
                    Budget(
                        user_id=user.id,
                        category_id=int(request.form["category_id"]),
                        month=today.month,
                        year=today.year,
                        amount=float(request.form["amount"]),
                    )
                )
            db.session.commit()
            flash("Budget saved for this month.", "success")
            return redirect(url_for("budgets"))

        start, end = month_bounds(today.year, today.month)
        rows = []
        for b in Budget.query.filter_by(user_id=user.id, month=today.month, year=today.year).all():
            spent = sum(
                t.amount
                for t in Transaction.query.filter_by(user_id=user.id, category_id=b.category_id, kind="expense").filter(
                    Transaction.txn_date.between(start, end)
                )
            )
            rows.append({"budget": b, "spent": spent, "pct": min(100, spent / b.amount * 100) if b.amount else 0})
        categories = Category.query.filter_by(kind="expense").order_by(Category.name).all()
        return render_template("budgets.html", rows=rows, categories=categories, month=today.strftime("%B %Y"))

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
        year = int(request.args.get("year", date.today().year))
        month = request.args.get("month", "")
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

    @app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        user = current_user()
        if request.method == "POST":
            deadline = request.form.get("deadline") or None
            db.session.add(
                Goal(
                    user_id=user.id,
                    name=request.form["name"].strip(),
                    target_amount=float(request.form["target_amount"]),
                    saved_amount=float(request.form.get("saved_amount") or 0),
                    deadline=datetime.strptime(deadline, "%Y-%m-%d").date() if deadline else None,
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
        goal.saved_amount += float(request.form.get("amount") or 0)
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
            user.name = request.form.get("name", user.name).strip()
            user.phone = request.form.get("phone", "").strip()
            user.monthly_income = float(request.form.get("monthly_income") or 0)
            new_password = request.form.get("password", "")
            if len(new_password) >= 6:
                user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", user=user)


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
    cats = {c.name: c for c in Category.query.all()}
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
