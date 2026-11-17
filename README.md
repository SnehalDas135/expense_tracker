# Personal Expense Tracker (Python Tkinter + SQLite)

## Run
    python app.py

Needs only Python 3.8 or newer. Tkinter and sqlite3 come with Python, so there is nothing to install.

## Files
- app.py              what the app does: events, validation, add, update, delete, search
- design.py           how the window looks: colours, widgets and their positions
- charts.py           how the three charts are drawn
- database.py         all SQL: create tables, add, update, delete, search, reports
- seed_data.py        optional: fills an empty database with 24 sample transactions
- expense_tracker.db  the SQLite database (created automatically if missing)

To start with an empty database, delete expense_tracker.db and run app.py.
