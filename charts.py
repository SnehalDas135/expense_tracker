"""
charts.py - HOW THE THREE CHARTS ARE DRAWN (also design).

Each function gets a Canvas and the numbers, and draws with arcs, rectangles
and text. "g" (grow) goes from 0 to 1 during the animation: at 0.5 every bar
is half its final length, at 1 the chart is complete.
"""

from datetime import datetime

from design import AMBER, BAR_COLOURS, BG, CORAL, FONT, JADE, MUTED, PANEL, TEXT, money


def text(c, x, y, words, colour=TEXT, size=11, anchor="w", weight="normal"):
    c.create_text(x, y, text=words, fill=colour, font=(FONT, size, weight), anchor=anchor)


def draw_pie(c, g, needs, expense):
    """Pie chart (ring): how much of the spending was needs and how much was wants."""
    c.delete("all")
    w, h = c.winfo_width(), c.winfo_height()
    if not expense:
        return text(c, 0, 12, "No expenses in this period.", MUTED)
    size = min(w - 20, h - 110)
    x, y, angle = (w - size) / 2, 10, 90             # start at 12 o'clock
    wants = expense - needs
    for value, colour in ((needs, JADE), (wants, AMBER)):
        extent = -359.9 * value / expense * g        # minus = clockwise
        if value:
            c.create_arc(x, y, x + size, y + size, start=angle, extent=extent,
                         fill=colour, outline=BG, width=3)
        angle += extent
    hole = size * 0.3                                # cover the middle to make a ring
    c.create_oval(x + hole, y + hole, x + size - hole, y + size - hole, fill=BG, outline=BG)
    text(c, w / 2, y + size / 2 - 8, "%.0f%%" % (100 * needs / expense * g), size=22,
         anchor="center", weight="bold")
    text(c, w / 2, y + size / 2 + 18, "needs", MUTED, 10, "center")
    for i, (name, value, colour) in enumerate([("Needs", needs, JADE), ("Wants", wants, AMBER)]):
        line = y + size + 28 + i * 28
        c.create_rectangle(x, line - 6, x + 12, line + 6, fill=colour, width=0)
        text(c, x + 22, line, name)
        text(c, x + size, line, "%s  (%.0f%%)" % (money(value, 0), 100 * value / expense), anchor="e")


def draw_bars(c, g, categories, expense):
    """Category-wise report: one horizontal bar per category, biggest first."""
    c.delete("all")
    w = c.winfo_width()
    if not categories:
        return text(c, 0, 12, "No expenses in this period.", MUTED)
    biggest = categories[0]["total"]
    for i, row in enumerate(categories):
        y = i * 44
        text(c, 0, y + 10, row["category"])
        text(c, w, y + 10, "%s  (%.0f%%)" % (money(row["total"], 0), 100 * row["total"] / expense),
             anchor="e")
        c.create_rectangle(0, y + 24, w, y + 32, fill=PANEL, width=0)
        c.create_rectangle(0, y + 24, w * row["total"] / biggest * g, y + 32,
                           fill=BAR_COLOURS[i % len(BAR_COLOURS)], width=0)


def draw_months(c, g, months):
    """Monthly summary: an income bar and an expense bar for each month."""
    c.delete("all")
    w, h = c.winfo_width(), c.winfo_height()
    if not months:
        return text(c, 0, 12, "No transactions in this period.", MUTED)
    text(c, 0, 10, "Income", JADE, 10)
    text(c, 56, 10, "Expenses", CORAL, 10)
    tallest = max(max(row["income"], row["expense"]) for row in months)
    slot = w / len(months)                           # width given to each month
    bar = min(44, slot * 0.32)
    floor = h - 52                                   # y position of the bottom of the bars
    for i, row in enumerate(months):
        middle = slot * i + slot / 2
        for left, value, colour in ((middle - bar - 2, row["income"], JADE),
                                    (middle + 2, row["expense"], CORAL)):
            top = floor - (floor - 60) * value / tallest * g
            c.create_rectangle(left, top, left + bar, floor, fill=colour, width=0)
            text(c, left + bar / 2, top - 10, "%.1fk" % (value / 1000), MUTED, 9, "center")
        saved = row["income"] - row["expense"]
        text(c, middle, floor + 16, datetime.strptime(row["month"], "%Y-%m").strftime("%b %Y"),
             anchor="center")
        text(c, middle, floor + 36, ("Saved " if saved >= 0 else "Over by ") + money(abs(saved), 0),
             JADE if saved >= 0 else CORAL, 9, "center")
