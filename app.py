"""
app.py - Personal Expense Tracker (Python Tkinter + SQLite)

Run with:   python app.py

The window has three parts:
  1. Top bar      - choose the period (From / To dates)
  2. Three cards  - total income, total expenses, balance
  3. Two tabs     - Transactions (add, update, delete, search, display)
                  - Reports (monthly summary, category-wise report)
"""

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import database as db

# Colours: the jade-on-dark look of the Fintrix web app
BG, PANEL, LINE = "#0B1410", "#15231C", "#284035"
JADE, CORAL, TEXT, MUTED = "#00A86B", "#F0796B", "#FFFFFF", "#9FB0A8"
BAR_COLOURS = ["#00A86B", "#5AA9E6", "#F2A65A", "#9D8DF1", "#F0796B",
               "#E3C567", "#4FC1B0", "#F283B6", "#8A9A93"]
FONT = "Segoe UI"
MODES = ["UPI", "Cash", "Card", "Net Banking"]
PERIODS = ["This month", "Last month", "This year", "All time"]
NEEDS = ["Food", "Travel", "Education", "Rent", "Healthcare", "Bills"]
MAX_AMOUNT = 1000000


def money(amount):
    return "₹{:,.2f}".format(amount)


def to_iso(text):
    """'14-11-2026' -> '2026-11-14'. Raises ValueError if it is not a real date."""
    return datetime.strptime(text.strip(), "%d-%m-%Y").date().isoformat()


def to_dmy(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d-%m-%Y")


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        db.init_db()
        self.title("Personal Expense Tracker")
        self.geometry("1180x720")
        self.minsize(1040, 640)
        self.configure(bg=BG)
        self.selected_id = None          # id of the row being edited (None = new)
        self.start = self.end = None     # selected period as YYYY-MM-DD
        self.category_rows = []

        self.make_styles()
        self.build_top_bar()
        self.build_cards()
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.build_transactions_tab(tabs)
        self.build_reports_tab(tabs)
        self.choose_period()

    # ------------------------------------------------------------- styling

    def make_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")              # the ttk theme that accepts custom colours
        s.configure(".", background=BG, foreground=TEXT, font=(FONT, 11), bordercolor=LINE,
                    lightcolor=PANEL, darkcolor=PANEL, troughcolor=BG, focuscolor=BG)
        s.configure("Muted.TLabel", foreground=MUTED, font=(FONT, 10))
        s.configure("Title.TLabel", font=(FONT, 18, "bold"))
        s.configure("Card.TFrame", background=PANEL)
        s.configure("Card.TLabel", background=PANEL, foreground=MUTED, font=(FONT, 10))
        s.configure("Value.TLabel", background=PANEL, font=(FONT, 22, "bold"))

        s.configure("TEntry", fieldbackground=PANEL, insertcolor=TEXT, padding=5)
        s.configure("TCombobox", fieldbackground=PANEL, background=PANEL, arrowcolor=MUTED, padding=5)
        s.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", PANEL)], selectforeground=[("readonly", TEXT)])
        self.option_add("*TCombobox*Listbox.background", PANEL)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", JADE)

        s.configure("TButton", background=PANEL, padding=(14, 7), font=(FONT, 10, "bold"))
        s.map("TButton", background=[("disabled", BG), ("active", LINE)],
              foreground=[("disabled", LINE)])
        s.configure("Add.TButton", background=JADE, foreground="#04130D")
        s.map("Add.TButton", background=[("active", "#00C27C")])
        s.configure("Delete.TButton", foreground=CORAL)
        for name in ("TRadiobutton", "TCheckbutton"):
            s.configure(name, indicatorbackground=PANEL, indicatorforeground=JADE,
                        upperbordercolor=MUTED, lowerbordercolor=MUTED)
            s.map(name, background=[("active", BG)], foreground=[("disabled", LINE)])

        s.configure("TNotebook", borderwidth=0)
        s.configure("TNotebook.Tab", background=BG, foreground=MUTED, padding=(18, 8))
        s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", TEXT)],
              padding=[("selected", (18, 8))], lightcolor=[("selected", PANEL)])
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, rowheight=30, borderwidth=0)
        s.map("Treeview", background=[("selected", "#0F4A35")])
        s.configure("Treeview.Heading", background=LINE, foreground=MUTED, relief="flat",
                    font=(FONT, 10, "bold"), padding=6)
        s.map("Treeview.Heading", background=[("active", LINE)])

    # ------------------------------------------------- top bar: the period

    def build_top_bar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=20, pady=(14, 10))
        ttk.Label(bar, text="Personal Expense Tracker", style="Title.TLabel").pack(side="left")

        self.period_var = tk.StringVar(value="This year")
        self.from_var, self.to_var = tk.StringVar(), tk.StringVar()
        ttk.Button(bar, text="Apply", command=self.apply_period).pack(side="right")
        ttk.Entry(bar, textvariable=self.to_var, width=11).pack(side="right", padx=8)
        ttk.Label(bar, text="To", style="Muted.TLabel").pack(side="right")
        ttk.Entry(bar, textvariable=self.from_var, width=11).pack(side="right", padx=8)
        ttk.Label(bar, text="From", style="Muted.TLabel").pack(side="right")
        box = ttk.Combobox(bar, textvariable=self.period_var, values=PERIODS, state="readonly", width=12)
        box.pack(side="right", padx=(8, 16))
        box.bind("<<ComboboxSelected>>", self.choose_period)
        ttk.Label(bar, text="Period", style="Muted.TLabel").pack(side="right")

    def choose_period(self, event=None):
        """A preset from the ComboBox fills the From and To boxes."""
        today = date.today()
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        start, end = {"This month": (first, today),
                      "Last month": (last_month_end.replace(day=1), last_month_end),
                      "This year": (date(today.year, 1, 1), today),
                      "All time": (None, None)}[self.period_var.get()]
        self.from_var.set(start.strftime("%d-%m-%Y") if start else "")
        self.to_var.set(end.strftime("%d-%m-%Y") if end else "")
        self.apply_period()

    def apply_period(self):
        """Reads the From and To boxes. An empty box means 'no limit'."""
        try:
            start = to_iso(self.from_var.get()) if self.from_var.get().strip() else None
            end = to_iso(self.to_var.get()) if self.to_var.get().strip() else None
        except ValueError:
            messagebox.showerror("Invalid period", "Enter the dates as DD-MM-YYYY, for example 01-11-2026.")
            return
        if start and end and start > end:
            messagebox.showerror("Invalid period", "The From date must be on or before the To date.")
            return
        self.start, self.end = start, end
        self.refresh()

    # ----------------------------------------- cards: income, expenses, balance

    def build_cards(self):
        row = ttk.Frame(self)
        row.pack(fill="x", padx=20, pady=(0, 12))
        self.cards = {}
        for i, (name, colour) in enumerate([("Total income", JADE), ("Total expenses", CORAL),
                                            ("Balance", TEXT)]):
            card = ttk.Frame(row, style="Card.TFrame", padding=(18, 8))
            card.grid(row=0, column=i, sticky="ew", padx=(0, 0 if i == 2 else 14))
            row.columnconfigure(i, weight=1)
            ttk.Label(card, text=name, style="Card.TLabel").pack(anchor="w")
            self.cards[name] = ttk.Label(card, style="Value.TLabel", foreground=colour)
            self.cards[name].pack(anchor="w")

    def refresh(self):
        """Reads the database again and redraws everything on the screen."""
        income, expense = db.get_totals(self.start, self.end)
        balance = income - expense
        self.cards["Total income"].config(text=money(income))
        self.cards["Total expenses"].config(text=money(expense))
        self.cards["Balance"].config(text=money(balance), foreground=CORAL if balance < 0 else TEXT)
        self.load_table()
        self.load_reports()

    # ---------------------------------------------------- Transactions tab

    def build_transactions_tab(self, tabs):
        tab = ttk.Frame(tabs, padding=14)
        tabs.add(tab, text="Transactions")

        # Left side: the form
        form = ttk.Frame(tab)
        form.pack(side="left", fill="y", padx=(0, 20))
        self.type_var = tk.StringVar(value="Expense")
        self.date_var, self.amount_var = tk.StringVar(), tk.StringVar()
        self.category_var, self.mode_var = tk.StringVar(), tk.StringVar()
        self.desc_var = tk.StringVar()
        self.need_var = tk.IntVar()

        radios = ttk.Frame(form)
        radios.pack(anchor="w", pady=(0, 6))
        for kind in ("Expense", "Income"):
            ttk.Radiobutton(radios, text=kind, value=kind, variable=self.type_var,
                            command=self.type_changed).pack(side="left", padx=(0, 16))

        def field(label, widget):
            ttk.Label(form, text=label, style="Muted.TLabel").pack(anchor="w")
            widget.pack(fill="x", pady=(1, 6))
            return widget

        field("Date (DD-MM-YYYY)", ttk.Entry(form, textvariable=self.date_var, width=30))
        field("Amount (₹)", ttk.Entry(form, textvariable=self.amount_var))
        self.category_box = field("Category", ttk.Combobox(form, textvariable=self.category_var,
                                                           state="readonly"))
        self.category_box.bind("<<ComboboxSelected>>", self.category_changed)
        field("Payment mode", ttk.Combobox(form, textvariable=self.mode_var, values=MODES,
                                           state="readonly"))
        field("Description (optional)", ttk.Entry(form, textvariable=self.desc_var))
        self.need_check = ttk.Checkbutton(form, text="This is a need, not a want", variable=self.need_var)
        self.need_check.pack(anchor="w", pady=(0, 8))

        buttons = ttk.Frame(form)                 # four buttons in a 2 x 2 grid
        buttons.pack(fill="x")
        buttons.columnconfigure((0, 1), weight=1, uniform="half")
        self.update_btn = ttk.Button(buttons, text="Update", command=self.update_transaction)
        self.delete_btn = ttk.Button(buttons, text="Delete", style="Delete.TButton",
                                     command=self.delete_transaction)
        ttk.Button(buttons, text="Add", style="Add.TButton",
                   command=self.add_transaction).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(buttons, text="Clear", command=self.clear_form).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.update_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=8)
        self.delete_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=8)

        # Right side: search box and the table
        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True)
        tools = ttk.Frame(right)
        tools.pack(fill="x", pady=(0, 10))
        self.search_var, self.filter_var = tk.StringVar(), tk.StringVar(value="All")
        ttk.Label(tools, text="Search", style="Muted.TLabel").pack(side="left")
        ttk.Entry(tools, textvariable=self.search_var, width=28).pack(side="left", padx=(8, 18))
        ttk.Label(tools, text="Show", style="Muted.TLabel").pack(side="left")
        show = ttk.Combobox(tools, textvariable=self.filter_var, state="readonly", width=10,
                            values=["All", "Income", "Expense"])
        show.pack(side="left", padx=8)
        self.search_var.trace_add("write", lambda *args: self.load_table())   # search while typing
        show.bind("<<ComboboxSelected>>", lambda e: self.load_table())
        self.count_label = ttk.Label(tools, style="Muted.TLabel")
        self.count_label.pack(side="right")

        columns = {"id": ("ID", 45), "date": ("Date", 95), "type": ("Type", 75),
                   "category": ("Category", 110), "desc": ("Description", 190),
                   "mode": ("Mode", 110), "amount": ("Amount", 115)}
        self.table = ttk.Treeview(right, columns=list(columns), show="headings", selectmode="browse")
        for key, (heading, width) in columns.items():
            side = "e" if key in ("id", "amount") else "w"
            self.table.heading(key, text=heading, anchor=side)
            self.table.column(key, width=width, anchor=side, stretch=(key == "desc"))
        self.table.tag_configure("Income", foreground="#4FD6A0")
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", self.row_selected)
        self.clear_form()

    # ---- events of the form

    def type_changed(self):
        """Income and Expense have different categories."""
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
        self.mode_var.set(MODES[0])
        self.desc_var.set("")
        self.update_btn.state(["disabled"])
        self.delete_btn.state(["disabled"])

    def row_selected(self, event=None):
        """Clicking a row copies it into the form so it can be edited or deleted."""
        if not self.table.selection():
            return
        row = self.rows[int(self.table.selection()[0])]
        self.selected_id = row["txn_id"]
        self.type_var.set(row["type"])
        self.type_changed()
        self.date_var.set(to_dmy(row["txn_date"]))
        self.amount_var.set("{:g}".format(row["amount"]))
        self.category_var.set(row["category"])
        self.mode_var.set(row["payment_mode"])
        self.desc_var.set(row["description"])
        self.need_var.set(row["is_essential"])
        self.update_btn.state(["!disabled"])
        self.delete_btn.state(["!disabled"])

    def error(self, title, message):
        messagebox.showerror(title, message)
        return None

    def read_form(self):
        """Input validation. Returns the cleaned values, or None after showing an error."""
        try:
            txn_date = to_iso(self.date_var.get())
        except ValueError:
            return self.error("Invalid date", "Enter a real date as DD-MM-YYYY, for example 14-11-2026.")
        if txn_date > date.today().isoformat():
            return self.error("Invalid date", "The date cannot be in the future.")
        try:
            amount = round(float(self.amount_var.get().replace(",", "")), 2)
        except ValueError:
            return self.error("Invalid amount", "Enter the amount as a number, for example 250 or 99.50.")
        if not 0 < amount <= MAX_AMOUNT:        # also rejects 'nan' and 'inf'
            return self.error("Invalid amount",
                                        "The amount must be more than 0 and at most %s." % money(MAX_AMOUNT))
        if not self.category_var.get():
            return self.error("Category missing", "Choose a category.")
        description = self.desc_var.get().strip()
        if len(description) > 50:
            return self.error("Description too long", "Keep the description within 50 characters.")
        return (txn_date, self.type_var.get(), amount, self.category_var.get(),
                description, self.mode_var.get(), self.need_var.get())

    # ---- Add, Update, Delete

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

    # ---- Search and Display

    def load_table(self):
        found = db.get_transactions(self.start, self.end, self.search_var.get().strip(),
                                    self.filter_var.get())
        self.rows = {row["txn_id"]: row for row in found}
        self.table.delete(*self.table.get_children())
        for row in found:
            self.table.insert("", "end", iid=row["txn_id"], tags=(row["type"],), values=(
                row["txn_id"], to_dmy(row["txn_date"]), row["type"], row["category"],
                row["description"], row["payment_mode"], money(row["amount"])))
        self.count_label.config(text="%d transaction(s)" % len(found) if found
                                else "No transactions found for this period or search")

    # ---------------------------------------------------------- Reports tab

    def build_reports_tab(self, tabs):
        tab = ttk.Frame(tabs, padding=14)
        tabs.add(tab, text="Reports")

        left = ttk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        ttk.Label(left, text="Monthly summary", font=(FONT, 13, "bold")).pack(anchor="w", pady=(0, 10))
        self.month_table = ttk.Treeview(left, show="headings", selectmode="none",
                                        columns=("month", "income", "expense", "balance"))
        for key, heading in (("month", "Month"), ("income", "Income"),
                             ("expense", "Expenses"), ("balance", "Balance")):
            side = "w" if key == "month" else "e"
            self.month_table.heading(key, text=heading, anchor=side)
            self.month_table.column(key, width=120, anchor=side)
        self.month_table.tag_configure("total", background=LINE)
        self.month_table.pack(fill="both", expand=True)

        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Category-wise report (expenses)",
                  font=(FONT, 13, "bold")).pack(anchor="w", pady=(0, 10))
        self.chart = tk.Canvas(right, bg=BG, highlightthickness=0, width=440)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda e: self.draw_chart())   # redraw when resized

    def load_reports(self):
        self.month_table.delete(*self.month_table.get_children())
        total_in = total_out = 0
        for row in db.get_monthly_summary(self.start, self.end):
            name = datetime.strptime(row["month"], "%Y-%m").strftime("%B %Y")
            self.month_table.insert("", "end", values=(
                name, money(row["income"]), money(row["expense"]), money(row["income"] - row["expense"])))
            total_in += row["income"]
            total_out += row["expense"]
        self.month_table.insert("", "end", tags=("total",), values=(
            "Total", money(total_in), money(total_out), money(total_in - total_out)))
        self.category_rows = db.get_category_report(self.start, self.end)
        self.draw_chart()

    def draw_chart(self):
        """Category-wise report: one horizontal bar per category, drawn on a Canvas."""
        c, rows, width = self.chart, self.category_rows, self.chart.winfo_width()
        c.delete("all")
        if not rows:
            c.create_text(0, 12, anchor="w", fill=MUTED, font=(FONT, 11),
                          text="No expenses in this period.")
            return
        total = sum(row["total"] for row in rows)
        for i, row in enumerate(rows):
            y = i * 44
            c.create_text(0, y + 10, anchor="w", fill=TEXT, font=(FONT, 11), text=row["category"])
            c.create_text(width, y + 10, anchor="e", fill=TEXT, font=(FONT, 11),
                          text="%s  (%.0f%%)" % (money(row["total"]), 100 * row["total"] / total))
            c.create_rectangle(0, y + 24, width, y + 31, fill=PANEL, width=0)
            c.create_rectangle(0, y + 24, width * row["total"] / rows[0]["total"], y + 31,
                               fill=BAR_COLOURS[i % len(BAR_COLOURS)], width=0)


if __name__ == "__main__":
    App().mainloop()
