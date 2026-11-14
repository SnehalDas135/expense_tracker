"""
database.py - every SQL statement of the project is in this file.

Flow:  User -> Tkinter GUI (app.py) -> these functions -> SQLite -> Output

All queries use "?" placeholders, so whatever the user types is treated
as data and can never run as SQL (no SQL injection).
"""

import os
import sqlite3

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expense_tracker.db")

CATEGORIES = {
    "Expense": ["Food", "Travel", "Education", "Rent", "Shopping",
                "Healthcare", "Entertainment", "Bills", "Other"],
    "Income": ["Allowance", "Salary", "Freelance", "Scholarship", "Gift"],
}


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row            # lets us write row["amount"]
    conn.execute("PRAGMA foreign_keys = ON")  # make SQLite check the foreign key
    return conn


def run(sql, params=()):
    """Runs one statement, saves the change and returns the rows (if any)."""
    with connect() as conn:                   # "with" commits automatically
        return conn.execute(sql, params).fetchall()


def init_db():
    """Creates the two tables on first run and fills in the categories."""
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                type        TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
                UNIQUE (name, type)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_date     TEXT    NOT NULL,                 -- YYYY-MM-DD
                type         TEXT    NOT NULL CHECK (type IN ('Income', 'Expense')),
                amount       REAL    NOT NULL CHECK (amount > 0),
                category_id  INTEGER NOT NULL REFERENCES categories (category_id),
                description  TEXT,
                payment_mode TEXT,
                is_essential INTEGER NOT NULL DEFAULT 0        -- 1 = need, 0 = want
            );
        """)
        for txn_type, names in CATEGORIES.items():
            for name in names:
                conn.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                             (name, txn_type))


def category_id(name, txn_type):
    rows = run("SELECT category_id FROM categories WHERE name = ? AND type = ?", (name, txn_type))
    return rows[0]["category_id"]


# ----------------------------------------------------- Add, Update, Delete

def add_transaction(txn_date, txn_type, amount, category, description, mode, essential):
    run("""INSERT INTO transactions
               (txn_date, type, amount, category_id, description, payment_mode, is_essential)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (txn_date, txn_type, amount, category_id(category, txn_type), description, mode, essential))


def update_transaction(txn_id, txn_date, txn_type, amount, category, description, mode, essential):
    run("""UPDATE transactions
              SET txn_date = ?, type = ?, amount = ?, category_id = ?,
                  description = ?, payment_mode = ?, is_essential = ?
            WHERE txn_id = ?""",
        (txn_date, txn_type, amount, category_id(category, txn_type), description, mode,
         essential, txn_id))


def delete_transaction(txn_id):
    run("DELETE FROM transactions WHERE txn_id = ?", (txn_id,))


# ------------------------------------------------------- Search and Display

def period_filter(start, end):
    """WHERE conditions for the selected period. None means 'no limit'."""
    where, params = ["1 = 1"], []
    if start:
        where.append("t.txn_date >= ?")
        params.append(start)
    if end:
        where.append("t.txn_date <= ?")
        params.append(end)
    return where, params


def get_transactions(start=None, end=None, search="", txn_type="All"):
    where, params = period_filter(start, end)
    if txn_type != "All":
        where.append("t.type = ?")
        params.append(txn_type)
    if search:
        where.append("(t.description LIKE ? OR c.name LIKE ? OR t.payment_mode LIKE ?)")
        params += ["%" + search + "%"] * 3
    return run("""SELECT t.*, c.name AS category
                    FROM transactions t JOIN categories c ON c.category_id = t.category_id
                   WHERE """ + " AND ".join(where) + """
                   ORDER BY t.txn_date DESC, t.txn_id DESC""", params)


# ------------------------------------------------------------------ Reports

def get_totals(start=None, end=None):
    """Total income and total expenses for the period."""
    where, params = period_filter(start, end)
    row = run("""SELECT COALESCE(SUM(CASE WHEN t.type = 'Income'  THEN t.amount END), 0) AS income,
                        COALESCE(SUM(CASE WHEN t.type = 'Expense' THEN t.amount END), 0) AS expense
                   FROM transactions t WHERE """ + " AND ".join(where), params)[0]
    return row["income"], row["expense"]


def get_monthly_summary(start=None, end=None):
    """One row per month: income and expenses."""
    where, params = period_filter(start, end)
    return run("""SELECT strftime('%Y-%m', t.txn_date) AS month,
                         COALESCE(SUM(CASE WHEN t.type = 'Income'  THEN t.amount END), 0) AS income,
                         COALESCE(SUM(CASE WHEN t.type = 'Expense' THEN t.amount END), 0) AS expense
                    FROM transactions t WHERE """ + " AND ".join(where) + """
                   GROUP BY month ORDER BY month""", params)


def get_category_report(start=None, end=None):
    """Expenses added up category by category, biggest first."""
    where, params = period_filter(start, end)
    return run("""SELECT c.name AS category, SUM(t.amount) AS total, COUNT(*) AS count
                    FROM transactions t JOIN categories c ON c.category_id = t.category_id
                   WHERE t.type = 'Expense' AND """ + " AND ".join(where) + """
                   GROUP BY c.name ORDER BY total DESC""", params)
