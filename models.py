from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), default="")
    monthly_income = db.Column(db.Float, default=0)
    currency = db.Column(db.String(8), default="INR")
    theme = db.Column(db.String(10), default="dark")
    reset_token = db.Column(db.String(100), default="")
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", lazy=True, cascade="all, delete-orphan")


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(80), nullable=False)
    kind = db.Column(db.String(20), default="expense")
    icon = db.Column(db.String(40), default="bi-tag")
    color = db.Column(db.String(20), default="#3ee0b0")

    user = db.relationship("User")

    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_category'),)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # income | expense
    note = db.Column(db.String(255), default="")
    merchant = db.Column(db.String(120), default="")
    payment_method = db.Column(db.String(40), default="UPI")
    txn_date = db.Column(db.Date, default=date.today)
    source = db.Column(db.String(20), default="manual")
    receipt_path = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    category = db.relationship("Category")


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    saved_amount = db.Column(db.Float, default=0)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RecurringTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), default="")
    merchant = db.Column(db.String(120), default="")
    payment_method = db.Column(db.String(40), default="UPI")
    frequency = db.Column(db.String(20), nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")


class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    from_method = db.Column(db.String(40), nullable=False)
    to_method = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    txn_date = db.Column(db.Date, default=date.today)
    note = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ImportBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    fingerprint = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "fingerprint", name="unique_import_row"),)
