"""
app.py - Personal Expense Tracker: WHAT THE APP DOES (the functionality).

Run with:   python app.py

The project is split so that each file has one job:
  app.py       what happens when the user does something (this file)
  design.py    how the window looks: colours, widgets and their positions
  charts.py    how the three charts are drawn
  database.py  all the SQL
"""

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox

import charts
import database as db
import design

PERIODS = ["This month", "Last month", "This year", "All time"]
NEEDS = ["Food", "Travel", "Education", "Rent", "Healthcare", "Bills"]
MAX_AMOUNT = 1000000


def to_dmy(iso):
    """'2026-11-14' (how the database stores it) -> '14-11-2026' (how we show it)."""
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d-%m-%Y")


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        db.init_db()
        self.selected_id = None      # id of the row being edited (None = new)
        self.grow = 1                # 0 to 1: how far the chart animation has got
        self.job = None

        # Variables shared between the widgets and the code.
        # When the user types or clicks, these change by themselves.
        self.period_var = tk.StringVar(value="This year")
        self.type_var = tk.StringVar(value="Expense")
        self.date_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.need_var = tk.IntVar()
        self.search_var = tk.StringVar()

        design.build_window(self, PERIODS)       # design.py creates every widget
        self.search_var.trace_add("write", lambda *args: self.load_table())   # search while typing
        self.clear_form()
        self.period_changed()

    # ------------------------------------------------------- period and totals

    def period_changed(self, event=None):
        """Turns the chosen period into a start date and an end date."""
        today = date.today()
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        start, end = {"This month": (first, today),
                      "Last month": (last_month_end.replace(day=1), last_month_end),
                      "This year": (date(today.year, 1, 1), today),
                      "All time": (date.min, today)}[self.period_var.get()]
        self.start, self.end = str(start), str(end)     # str(date) gives YYYY-MM-DD
        self.refresh()

    def refresh(self):
        """Reads the database again and redraws everything on the screen."""
        self.income, self.expense, self.needs = db.get_totals(self.start, self.end)
        self.months = db.get_monthly_summary(self.start, self.end)[-6:]     # last 6 at most
        self.categories = db.get_category_report(self.start, self.end)
        balance = self.income - self.expense
        self.cards["Total income"].config(text=design.money(self.income))
        self.cards["Total expenses"].config(text=design.money(self.expense))
        self.cards["Balance"].config(text=design.money(balance),
                                     foreground=design.CORAL if balance < 0 else design.TEXT)
        self.load_table()
        self.animate()

    # ------------------------------------------------------ events of the form

    def type_changed(self):
        """Income and Expense have different categories; only expenses can be needs."""
        kind = self.type_var.get()
        self.category_box.config(values=db.CATEGORIES[kind])
        self.category_var.set("")
        self.need_var.set(0)
        self.need_check.state(["!disabled"] if kind == "Expense" else ["disabled"])

    def category_changed(self, event=None):
        """Pre-tick 'need' for categories like Rent; the user can still change it."""
        if self.type_var.get() == "Expense":
            self.need_var.set(1 if self.category_var.get() in NEEDS else 0)

    def clear_form(self):
        self.selected_id = None
        self.table.selection_remove(self.table.selection())
        self.type_var.set("Expense")
        self.type_changed()
        self.date_var.set(date.today().strftime("%d-%m-%Y"))
        self.amount_var.set("")
        self.desc_var.set("")
        self.update_btn.state(["disabled"])
        self.delete_btn.state(["disabled"])

    def row_selected(self, event=None):
        """Clicking a row copies it into the form so it can be updated or deleted."""
        if not self.table.selection():
            return
        row = self.rows[int(self.table.selection()[0])]
        self.selected_id = row["txn_id"]
        self.type_var.set(row["type"])
        self.type_changed()
        self.date_var.set(to_dmy(row["txn_date"]))
        self.amount_var.set("{:g}".format(row["amount"]))
        self.category_var.set(row["category"])
        self.desc_var.set(row["description"])
        self.need_var.set(row["is_need"])
        self.update_btn.state(["!disabled"])
        self.delete_btn.state(["!disabled"])

    # -------------------------------------------------------------- validation

    def error(self, title, message):
        messagebox.showerror(title, message)
        return None

    def read_form(self):
        """Input validation. Returns the cleaned values, or None after showing an error."""
        try:
            txn_date = datetime.strptime(self.date_var.get().strip(), "%d-%m-%Y").date()
        except ValueError:
            return self.error("Invalid date", "Enter a real date as DD-MM-YYYY, for example 14-11-2026.")
        if txn_date > date.today():
            return self.error("Invalid date", "The date cannot be in the future.")
        try:
            amount = round(float(self.amount_var.get().replace(",", "")), 2)
        except ValueError:
            return self.error("Invalid amount", "Enter the amount as a number, for example 250 or 99.50.")
        if not 0 < amount <= MAX_AMOUNT:             # also rejects 'nan' and 'inf'
            return self.error("Invalid amount", "The amount must be more than 0 and at most %s."
                              % design.money(MAX_AMOUNT))
        if not self.category_var.get():
            return self.error("Category missing", "Choose a category.")
        description = self.desc_var.get().strip()
        if len(description) > 50:
            return self.error("Description too long", "Keep the description within 50 characters.")
        return (str(txn_date), self.type_var.get(), amount, self.category_var.get(),
                description, self.need_var.get())

    # ----------------------------------------------------- Add, Update, Delete

    def add_transaction(self):
        values = self.read_form()
        if values:
            db.add_transaction(*values)
            self.clear_form()
            self.refresh()

    def update_transaction(self):
        values = self.read_form()
        if values:
            db.update_transaction(self.selected_id, *values)
            self.clear_form()
            self.refresh()

    def delete_transaction(self):
        if messagebox.askyesno("Delete transaction",
                               "Delete transaction #%d? This cannot be undone." % self.selected_id):
            db.delete_transaction(self.selected_id)
            self.clear_form()
            self.refresh()

    # ------------------------------------------------------ Search and Display

    def load_table(self):
        found = db.get_transactions(self.start, self.end, self.search_var.get().strip())
        self.rows = {row["txn_id"]: row for row in found}
        self.table.delete(*self.table.get_children())
        for row in found:
            kind = "" if row["type"] == "Income" else ("Need" if row["is_need"] else "Want")
            self.table.insert("", "end", iid=row["txn_id"], tags=(row["type"],), values=(
                row["txn_id"], to_dmy(row["txn_date"]), row["type"], row["category"],
                row["description"], kind, design.money(row["amount"])))
        self.count_label.config(text="%d transaction(s)" % len(found) if found
                                else "No transactions found for this period or search")

    # ------------------------------------------------------------------ Charts

    def animate(self, step=1):
        """Redraws the charts 20 times in a third of a second, so they grow into place."""
        if self.job:
            self.after_cancel(self.job)
        self.grow = 1 - (1 - step / 20) ** 3             # fast at first, slower at the end
        self.draw_charts()
        self.job = self.after(16, self.animate, step + 1) if step < 20 else None

    def draw_charts(self):
        """Hands the numbers to charts.py, which does the drawing."""
        charts.draw_pie(self.pie, self.grow, self.needs, self.expense)
        charts.draw_bars(self.bars, self.grow, self.categories, self.expense)
        charts.draw_months(self.month_chart, self.grow, self.months)


if __name__ == "__main__":
    App().mainloop()
