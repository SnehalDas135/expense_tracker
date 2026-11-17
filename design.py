"""
design.py - HOW THE WINDOW LOOKS (the design). Nothing here decides behaviour.

It does three things:
  1. holds the colours and the font
  2. make_styles()   applies the dark theme
  3. build_...()     creates the widgets and puts them in position

Each widget is connected to a function in app.py with command= or bind().
Widgets that app.py needs later are saved on the app, for example app.table.
"""

import tkinter as tk
from tkinter import ttk

# Colours: the jade-on-dark look of the Fintrix web app
BG, PANEL, LINE = "#0B1410", "#15231C", "#284035"
JADE, CORAL, AMBER, TEXT, MUTED = "#00A86B", "#F0796B", "#F2A65A", "#FFFFFF", "#9FB0A8"
BAR_COLOURS = ["#00A86B", "#5AA9E6", "#F2A65A", "#9D8DF1", "#F0796B",
               "#E3C567", "#4FC1B0", "#F283B6", "#8A9A93"]
FONT = "Segoe UI"


def money(amount, places=2):
    """4500 -> '₹4,500.00'"""
    return "₹{:,.{}f}".format(amount, places)


def build_window(app, periods):
    """Builds the whole screen, top to bottom."""
    app.title("Personal Expense Tracker")
    app.geometry("1180x720")
    app.minsize(1040, 640)
    app.configure(bg=BG)
    make_styles(app)
    build_top(app, periods)
    app.tabs = ttk.Notebook(app)
    app.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))
    build_transactions_tab(app)
    build_analysis_tab(app)
    app.tabs.bind("<<NotebookTabChanged>>", lambda e: app.animate())


def make_styles(app):
    """The dark theme: one configure() line for each kind of widget."""
    s = ttk.Style(app)
    s.theme_use("clam")              # the ttk theme that accepts custom colours
    s.configure(".", background=BG, foreground=TEXT, font=(FONT, 11), bordercolor=LINE,
                lightcolor=PANEL, darkcolor=PANEL, troughcolor=BG, focuscolor=BG)
    s.configure("Muted.TLabel", foreground=MUTED, font=(FONT, 10))
    s.configure("Card.TFrame", background=PANEL)
    s.configure("Card.TLabel", background=PANEL, foreground=MUTED, font=(FONT, 10))
    s.configure("TEntry", fieldbackground=PANEL, insertcolor=TEXT, padding=5)
    s.configure("TCombobox", fieldbackground=PANEL, background=PANEL, arrowcolor=MUTED, padding=5)
    s.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)],
          selectbackground=[("readonly", PANEL)], selectforeground=[("readonly", TEXT)])
    app.option_add("*TCombobox*Listbox.background", PANEL)
    app.option_add("*TCombobox*Listbox.foreground", TEXT)
    s.configure("TButton", background=PANEL, padding=(14, 7), font=(FONT, 10, "bold"))
    s.map("TButton", background=[("disabled", BG), ("active", LINE)], foreground=[("disabled", LINE)])
    s.configure("Add.TButton", background=JADE, foreground="#04130D")
    s.configure("Delete.TButton", foreground=CORAL)
    for name in ("TRadiobutton", "TCheckbutton"):
        s.configure(name, indicatorbackground=PANEL, indicatorforeground=JADE)
        s.map(name, background=[("active", BG)], foreground=[("disabled", LINE)])
    s.configure("TNotebook.Tab", background=BG, foreground=MUTED, padding=(18, 8))
    s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", TEXT)],
          padding=[("selected", (18, 8))])
    s.configure("Treeview", background=PANEL, fieldbackground=PANEL, rowheight=30, borderwidth=0)
    s.map("Treeview", background=[("selected", "#0F4A35")])
    s.configure("Treeview.Heading", background=LINE, foreground=MUTED, relief="flat",
                font=(FONT, 10, "bold"), padding=6)


def build_top(app, periods):
    """Title, Period combo box and the three cards. Saves app.cards."""
    bar = ttk.Frame(app)
    bar.pack(fill="x", padx=20, pady=(14, 10))
    ttk.Label(bar, text="Personal Expense Tracker", font=(FONT, 18, "bold")).pack(side="left")
    box = ttk.Combobox(bar, textvariable=app.period_var, values=periods, state="readonly", width=12)
    box.pack(side="right")
    box.bind("<<ComboboxSelected>>", app.period_changed)
    ttk.Label(bar, text="Period", style="Muted.TLabel").pack(side="right", padx=8)

    row = ttk.Frame(app)
    row.pack(fill="x", padx=20, pady=(0, 12))
    app.cards = {}
    for i, (name, colour) in enumerate([("Total income", JADE), ("Total expenses", CORAL),
                                        ("Balance", TEXT)]):
        card = ttk.Frame(row, style="Card.TFrame", padding=(18, 8))
        card.grid(row=0, column=i, sticky="ew", padx=(0, 0 if i == 2 else 14))
        row.columnconfigure(i, weight=1)
        ttk.Label(card, text=name, style="Card.TLabel").pack(anchor="w")
        app.cards[name] = ttk.Label(card, background=PANEL, foreground=colour, font=(FONT, 22, "bold"))
        app.cards[name].pack(anchor="w")


def build_transactions_tab(app):
    """Form on the left, search box and table on the right.
    Saves app.category_box, app.need_check, app.update_btn, app.delete_btn,
    app.count_label and app.table."""
    tab = ttk.Frame(app.tabs, padding=14)
    app.tabs.add(tab, text="Transactions")

    # Left side: the form
    form = ttk.Frame(tab)
    form.pack(side="left", fill="y", padx=(0, 20))
    radios = ttk.Frame(form)
    radios.pack(anchor="w", pady=(0, 8))
    for kind in ("Expense", "Income"):
        ttk.Radiobutton(radios, text=kind, value=kind, variable=app.type_var,
                        command=app.type_changed).pack(side="left", padx=(0, 16))
    app.category_box = ttk.Combobox(form, textvariable=app.category_var, state="readonly")
    app.category_box.bind("<<ComboboxSelected>>", app.category_changed)
    for label, widget in [("Date (DD-MM-YYYY)", ttk.Entry(form, textvariable=app.date_var, width=30)),
                          ("Amount (₹)", ttk.Entry(form, textvariable=app.amount_var)),
                          ("Category", app.category_box),
                          ("Description (optional)", ttk.Entry(form, textvariable=app.desc_var))]:
        ttk.Label(form, text=label, style="Muted.TLabel").pack(anchor="w")
        widget.pack(fill="x", pady=(1, 8))
    app.need_check = ttk.Checkbutton(form, text="This is a need, not a want", variable=app.need_var)
    app.need_check.pack(anchor="w", pady=(0, 10))

    buttons = ttk.Frame(form)                    # four buttons in a 2 x 2 grid
    buttons.pack(fill="x")
    buttons.columnconfigure((0, 1), weight=1, uniform="half")
    app.update_btn = ttk.Button(buttons, text="Update", command=app.update_transaction)
    app.delete_btn = ttk.Button(buttons, text="Delete", style="Delete.TButton",
                                command=app.delete_transaction)
    ttk.Button(buttons, text="Add", style="Add.TButton",
               command=app.add_transaction).grid(row=0, column=0, sticky="ew", padx=(0, 4))
    ttk.Button(buttons, text="Clear", command=app.clear_form).grid(row=0, column=1, sticky="ew", padx=(4, 0))
    app.update_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=8)
    app.delete_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=8)

    # Right side: search box and the table
    right = ttk.Frame(tab)
    right.pack(side="left", fill="both", expand=True)
    tools = ttk.Frame(right)
    tools.pack(fill="x", pady=(0, 10))
    ttk.Label(tools, text="Search", style="Muted.TLabel").pack(side="left")
    ttk.Entry(tools, textvariable=app.search_var, width=30).pack(side="left", padx=8)
    app.count_label = ttk.Label(tools, style="Muted.TLabel")
    app.count_label.pack(side="right")

    columns = {"id": ("ID", 45), "date": ("Date", 100), "type": ("Type", 80),
               "category": ("Category", 120), "desc": ("Description", 220),
               "kind": ("Need / Want", 100), "amount": ("Amount", 120)}
    app.table = ttk.Treeview(right, columns=list(columns), show="headings", selectmode="browse")
    for key, (heading, width) in columns.items():
        side = "e" if key in ("id", "amount") else "w"
        app.table.heading(key, text=heading, anchor=side)
        app.table.column(key, width=width, anchor=side, stretch=(key == "desc"))
    app.table.tag_configure("Income", foreground="#4FD6A0")
    scroll = ttk.Scrollbar(right, orient="vertical", command=app.table.yview)
    app.table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    app.table.pack(fill="both", expand=True)
    app.table.bind("<<TreeviewSelect>>", app.row_selected)


def build_analysis_tab(app):
    """Three empty canvases for the charts. Saves app.pie, app.bars, app.month_chart."""
    tab = ttk.Frame(app.tabs, padding=14)
    app.tabs.add(tab, text="Analysis")
    tab.rowconfigure(1, weight=1)
    canvases = []
    for column, (title, weight) in enumerate([("Needs vs wants", 2), ("Category-wise report", 3),
                                              ("Monthly summary", 3)]):
        tab.columnconfigure(column, weight=weight)
        ttk.Label(tab, text=title, font=(FONT, 13, "bold")).grid(row=0, column=column, sticky="w",
                                                                 padx=12, pady=(0, 10))
        canvas = tk.Canvas(tab, bg=BG, highlightthickness=0, width=10)
        canvas.grid(row=1, column=column, sticky="nsew", padx=12)
        canvas.bind("<Configure>", lambda e: app.draw_charts())      # redraw when resized
        canvases.append(canvas)
    app.pie, app.bars, app.month_chart = canvases
