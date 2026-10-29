from datetime import date
from io import BytesIO

from models import Budget, Category, RecurringTransaction, Transaction, User, db
from app import advance_due_date, process_recurring_transactions


def test_registration_and_login(client, user):
    client.get("/logout")
    response = client.post("/login", data=user)
    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_finance_pages_render(client, user):
    with client:
        client.post("/login", data=user)
        for path in ("/dashboard", "/transactions", "/budgets", "/goals", "/reports", "/scan",
                     "/profile", "/recurring", "/categories", "/transfers"):
            assert client.get(path).status_code == 200, path


def test_weak_password_rejected(client):
    response = client.post("/register", data={"name": "A", "email": "weak@example.com", "password": "weak"})
    assert response.status_code == 200
    assert b"at least 8 characters" in response.data


def test_forgot_password_resets_password(client, app, user):
    client.post("/forgot-password", data={"email": user["email"]})
    with app.app_context():
        owner = User.query.filter_by(email=user["email"]).first()
        token = owner.reset_token
        assert token
    response = client.post(f"/reset-password?token={token}", data={"token": token, "password": "ChangedPass2"})
    assert response.status_code == 302
    client.post("/logout")
    assert client.post("/login", data={"email": user["email"], "password": "ChangedPass2"}).status_code == 302


def test_transaction_create_and_delete(client, user, app):
    with client:
        client.post("/login", data=user)
        with app.app_context():
            category = Category.query.filter_by(name="Food", user_id=None).first()
            category_id = category.id
        response = client.post("/transactions/new", data={"amount": "12.50", "category_id": category_id,
                                                           "kind": "expense", "txn_date": date.today().isoformat()})
        assert response.status_code == 302
        with app.app_context():
            txn = Transaction.query.filter_by(merchant="").first()
            assert txn and txn.amount == 12.5
            txn_id = txn.id
        assert client.post(f"/transactions/{txn_id}/delete").status_code == 302


def test_budget_rejects_foreign_category(client, user, app):
    other_id = None
    with app.app_context():
        other = Category(user_id=999, name="Private", kind="expense")
        db.session.add(other)
        db.session.commit()
        other_id = other.id
    with client:
        client.post("/login", data=user)
        client.post("/budgets", data={"category_id": other_id, "amount": "100"})
        with app.app_context():
            from models import Budget
            assert Budget.query.count() == 0


def test_recurring_month_end_advance():
    assert advance_due_date(date(2024, 1, 31), "monthly") == date(2024, 2, 29)
    assert advance_due_date(date(2023, 2, 28), "yearly") == date(2024, 2, 28)


def test_recurring_transaction_is_created_when_due(app, user):
    with app.app_context():
        owner = User.query.filter_by(email=user["email"]).first()
        category = Category.query.filter_by(name="Food", user_id=None).first()
        db.session.add(RecurringTransaction(user_id=owner.id, category_id=category.id, amount=25,
                                            kind="expense", frequency="weekly", next_due_date=date.today()))
        db.session.commit()
        before = Transaction.query.count()
        process_recurring_transactions()
        assert Transaction.query.count() == before + 1


def test_budget_alert_calculation(client, app, user):
    with app.app_context():
        owner = User.query.filter_by(email=user["email"]).first()
        category = Category.query.filter_by(name="Food", user_id=None).first()
        today = date.today()
        db.session.add(Budget(user_id=owner.id, category_id=category.id, month=today.month, year=today.year, amount=100))
        db.session.add(Transaction(user_id=owner.id, category_id=category.id, amount=80, kind="expense", txn_date=today))
        db.session.commit()
    with client:
        client.post("/login", data=user)
        response = client.get("/budgets")
        assert b"Near" in response.data


def test_csrf_blocks_post_without_token():
    from app import create_app
    from pathlib import Path
    application = create_app({"TESTING": True, "SECRET_KEY": "csrf-test", "SQLALCHEMY_DATABASE_URI": "sqlite://",
                              "UPLOAD_FOLDER": Path(__file__).parent / ".uploads", "RATELIMIT_ENABLED": False,
                              "WTF_CSRF_ENABLED": True})
    response = application.test_client().post("/login", data={"email": "x", "password": "x"})
    assert response.status_code == 400


def test_login_is_rate_limited():
    from app import create_app
    from pathlib import Path
    application = create_app({"TESTING": True, "SECRET_KEY": "limit-test", "SQLALCHEMY_DATABASE_URI": "sqlite://",
                              "UPLOAD_FOLDER": Path(__file__).parent / ".uploads", "WTF_CSRF_ENABLED": False})
    client = application.test_client()
    statuses = [client.post("/login", data={"email": "absent@example.com", "password": "wrong"}).status_code for _ in range(6)]
    assert statuses[-1] == 429


def test_finance_exports_render(client, user):
    with client:
        client.post("/login", data=user)
        assert client.get("/reports").status_code == 200
        assert client.get("/reports/export.xlsx").mimetype.endswith("spreadsheetml.sheet")
        assert client.get("/reports/pdf").mimetype == "application/pdf"
        assert client.get("/reports/print").status_code == 200


def test_csv_import_maps_and_skips_duplicate(client, user, app):
    csv_data = b"Date,Amount,Type,Category,Merchant\n2026-10-01,25.50,expense,Food,Cafe Test\n"
    def upload(confirm=False):
        data = {"file": (BytesIO(csv_data), "sample.csv")}
        if confirm:
            data.update({"confirm": "yes", "date": "Date", "amount": "Amount", "type": "Type",
                         "category": "Category", "merchant": "Merchant"})
        return client.post("/reports/import", data=data, content_type="multipart/form-data")
    with client:
        client.post("/login", data=user)
        assert upload().status_code == 200
        upload(confirm=True)
        upload(confirm=True)
    with app.app_context():
        imported = Transaction.query.filter_by(source="import").all()
        assert len(imported) == 1
