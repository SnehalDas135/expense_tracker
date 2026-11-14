"""
seed_data.py - optional. Fills an EMPTY database with sample transactions
so the app has something to show in the demo.

Run once with:   python seed_data.py
"""

import database as db

# (date, type, amount, category, description, payment mode, need?)
SAMPLE = [
    ("2026-09-01", "Income", 12000, "Allowance", "Monthly allowance", "Net Banking", 0),
    ("2026-09-02", "Expense", 4500, "Rent", "Hostel mess and room", "UPI", 1),
    ("2026-09-05", "Expense", 320, "Food", "Biryani with friends", "UPI", 0),
    ("2026-09-09", "Expense", 850, "Education", "DSA reference book", "Card", 1),
    ("2026-09-14", "Expense", 240, "Travel", "Train to Chennai", "Cash", 1),
    ("2026-09-20", "Expense", 499, "Entertainment", "Movie night", "UPI", 0),
    ("2026-09-26", "Expense", 1200, "Shopping", "Shoes", "Card", 0),
    ("2026-10-01", "Income", 12000, "Allowance", "Monthly allowance", "Net Banking", 0),
    ("2026-10-03", "Expense", 4500, "Rent", "Hostel mess and room", "UPI", 1),
    ("2026-10-07", "Income", 3500, "Freelance", "Logo design work", "UPI", 0),
    ("2026-10-10", "Expense", 410, "Food", "Canteen for the week", "Cash", 1),
    ("2026-10-12", "Expense", 299, "Bills", "Mobile recharge", "UPI", 1),
    ("2026-10-18", "Expense", 650, "Healthcare", "Medicines", "Cash", 1),
    ("2026-10-22", "Expense", 1800, "Travel", "Bus tickets home", "UPI", 1),
    ("2026-10-29", "Expense", 560, "Food", "Pizza", "UPI", 0),
    ("2026-11-01", "Income", 12000, "Allowance", "Monthly allowance", "Net Banking", 0),
    ("2026-11-02", "Expense", 4500, "Rent", "Hostel mess and room", "UPI", 1),
    ("2026-11-04", "Income", 5000, "Scholarship", "Merit scholarship", "Net Banking", 0),
    ("2026-11-06", "Expense", 380, "Food", "Dinner outside", "UPI", 0),
    ("2026-11-08", "Expense", 1499, "Education", "Online course", "Card", 1),
    ("2026-11-10", "Expense", 299, "Bills", "Mobile recharge", "UPI", 1),
    ("2026-11-12", "Expense", 180, "Travel", "Auto to college", "Cash", 1),
]

db.init_db()
if db.get_transactions():
    print("The database already has transactions, so nothing was added.")
else:
    for row in SAMPLE:
        db.add_transaction(*row)
    print("Added %d sample transactions." % len(SAMPLE))
