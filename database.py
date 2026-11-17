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


def run(sql, params=()):
    """Runs one SQL statement, saves the change and returns the rows (if any)."""
    with sqlite3.connect(DB_FILE) as conn:        # "with" commits automatically
        conn.row_factory = sqlite3.Row            # lets us write row["amount"]
        conn.execute("PRAGMA foreign_keys = ON")  # make SQLite check the foreign key
        return conn.execute(sql, params).fetchall()


def init_db():
    """Creates the two tables on first run and fills in the categories."""
    run("""CREATE TABLE IF NOT EXISTS categories (
               category_id INTEGER PRIMARY KEY AUTOINCREMENT,
               name        TEXT NOT NULL,
               type        TEXT NOT NULL CHECK (type IN ('Income', 'Expense')),
               UNIQUE (name, type))""")
    run("""CREATE TABLE IF NOT EXISTS transactions (
               txn_id      INTEGER PRIMARY KEY AUTOINCREMENT,
               txn_date    TEXT    NOT NULL,                  -- YYYY-MM-DD
               type        TEXT    NOT NULL CHECK (type IN ('Income', 'Expense')),
               amount      REAL    NOT NULL CHECK (amount > 0),
               category_id INTEGER NOT NULL REFERENCES categories (category_id),
               description TEXT,
               is_need     INTEGER NOT NULL DEFAULT 0)        -- 1 = need, 0 = want""")
    for txn_type, names in CATEGORIES.items():
        for name in names:
            run("INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)", (name, txn_type))


def category_id(name, txn_type):
    rows = run("SELECT category_id FROM categories WHERE name = ? AND type = ?", (name, txn_type))
    return rows[0]["category_id"]


# ------------------------------------------------------ Add, Update, Delete

def add_transaction(txn_date, txn_type, amount, category, description, is_need):
    run("""INSERT INTO transactions (txn_date, type, amount, category_id, description, is_need)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (txn_date, txn_type, amount, category_id(category, txn_type), description, is_need))


def update_transaction(txn_id, txn_date, txn_type, amount, category, description, is_need):
    run("""UPDATE transactions
              SET txn_date = ?, type = ?, amount = ?, category_id = ?, description = ?, is_need = ?
            WHERE txn_id = ?""",
        (txn_date, txn_type, amount, category_id(category, txn_type), description, is_need, txn_id))


def delete_transaction(txn_id):
    run("DELETE FROM transactions WHERE txn_id = ?", (txn_id,))


# ------------------------------------------------------- Search and Display

def get_transactions(start, end, search=""):
    """All transactions of the period, newest first. 'search' can be empty."""
    like = "%" + search + "%"
    return run("""SELECT t.*, c.name AS category
                    FROM transactions t JOIN categories c ON c.category_id = t.category_id
                   WHERE t.txn_date BETWEEN ? AND ?
                     AND (t.description LIKE ? OR c.name LIKE ? OR t.type LIKE ?)
                   ORDER BY t.txn_date DESC, t.txn_id DESC""", (start, end, like, like, like))


# ------------------------------------------------------------------ Reports
# TOTAL() is SQLite's SUM() that gives 0 instead of NULL when there are no rows.

def get_totals(start, end):
    """Returns (total income, total expenses, expenses marked as needs)."""
    row = run("""SELECT TOTAL(CASE WHEN type = 'Income'  THEN amount END) AS income,
                        TOTAL(CASE WHEN type = 'Expense' THEN amount END) AS expense,
                        TOTAL(CASE WHEN type = 'Expense' AND is_need = 1 THEN amount END) AS needs
                   FROM transactions WHERE txn_date BETWEEN ? AND ?""", (start, end))[0]
    return row["income"], row["expense"], row["needs"]


def get_monthly_summary(start, end):
    """One row per month: income and expenses."""
    return run("""SELECT strftime('%Y-%m', txn_date) AS month,
                         TOTAL(CASE WHEN type = 'Income'  THEN amount END) AS income,
                         TOTAL(CASE WHEN type = 'Expense' THEN amount END) AS expense
                    FROM transactions WHERE txn_date BETWEEN ? AND ?
                   GROUP BY month ORDER BY month""", (start, end))


def get_category_report(start, end):
    """Expenses added up category by category, biggest first."""
    return run("""SELECT c.name AS category, SUM(t.amount) AS total
                    FROM transactions t JOIN categories c ON c.category_id = t.category_id
                   WHERE t.type = 'Expense' AND t.txn_date BETWEEN ? AND ?
                   GROUP BY c.name ORDER BY total DESC""", (start, end))
