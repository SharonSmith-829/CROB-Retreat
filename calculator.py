import tkinter as tk
from tkinter import ttk


DEFAULT_INVESTMENT = 12000
DEFAULT_ANNUAL_PREMIUM = 20000
POLICY_TERMS = (1, 3, 5)

MITIGATION_ACTIONS = [
    (
        "0-5 Foot Noncombustible Zone",
        3000,
        5000,
        8.0,
        18.0,
        "Removes the most dangerous fuels closest to the structure.",
    ),
    (
        "Enclosed Eaves",
        3000,
        4500,
        2.0,
        6.0,
        "Limits ember buildup along open rafter tails and soffits.",
    ),
    (
        "Ember-Resistant Vents",
        1500,
        2500,
        2.0,
        8.0,
        "Reduces ember intrusion into attic and crawl-space openings.",
    ),
    (
        "Dual-Pane Tempered Glass Windows",
        2400,
        4800,
        4.0,
        12.0,
        "Improves resistance to heat stress and breakage near flame fronts.",
    ),
    (
        "Class A Fire-Rated Roof",
        10000,
        30000,
        5.0,
        10.0,
        "Improves roof assembly performance under heavy ember exposure.",
    ),
    (
        "1/8 in Ember Screens Retrofit",
        400,
        1200,
        1.0,
        4.0,
        "Low-cost screening upgrade where full vent replacement is not needed.",
    ),
    (
        "Noncombustible Fencing Near Home",
        1000,
        4000,
        1.0,
        4.0,
        "Prevents fence lines from acting as flame pathways to the structure.",
    ),
    (
        "Deck Hardening (noncombustible or enclosed)",
        5000,
        15000,
        2.0,
        7.0,
        "Reduces ignition risk from ember accumulation under and on decks.",
    ),
    (
        "Exterior Siding and Trim Hardening",
        10000,
        30000,
        2.0,
        8.0,
        "Improves wall assembly resilience to radiant heat and ember contact.",
    ),
    (
        "Defensible Space 5-100 Foot Zone",
        1000,
        5000,
        2.0,
        6.0,
        "Lowers fire intensity near the home by managing wider surrounding fuels.",
    ),
    (
        "IBHS Wildfire Prepared Home Suite",
        12000,
        30000,
        2.0,
        28.0,
        "Program-level verification can unlock larger insurer-recognized discounts.",
    ),
    (
        "IBHS Wildfire Prepared Home Plus Suite",
        20000,
        50000,
        3.8,
        39.0,
        "Higher performance suite with broader hardening and larger potential discount.",
    ),
]


def parse_money(value, label):
    cleaned = str(value).strip().replace("$", "").replace(",", "")
    if not cleaned:
        raise ValueError(f"{label} is required.")
    try:
        amount = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if amount < 0:
        raise ValueError(f"{label} must be non-negative.")
    return amount


def money(value):
    return f"${value:,.0f}"


def percent(value):
    return f"{value:.1f}%"


def years_text(value):
    if value == float("inf"):
        return "Not reachable"
    return f"{value:.1f} yrs"


def cost_range_text(low, high):
    return f"{money(low)}-{money(high)}"


def clear_tree(tree):
    for row_id in tree.get_children():
        tree.delete(row_id)


def update_results():
    status_var.set("")
    clear_tree(actions_table)
    clear_tree(policy_table)

    try:
        investment = parse_money(investment_var.get(), "Investment")
        annual_premium = parse_money(annual_premium_var.get(), "Annual premium")
    except ValueError as err:
        status_var.set(str(err))
        return

    baseline_savings = annual_premium * (12.5 / 100.0)
    payback_years = float("inf") if baseline_savings == 0 else investment / baseline_savings
    guaranteed_savings_result_var.set(f"Case-study annual savings (12.5%): {money(baseline_savings)}")

    if payback_years == float("inf"):
        payback_result_var.set("Case-study payback period: Not reachable")
    else:
        payback_result_var.set(f"Case-study payback period: {payback_years:.1f} years")

    term_result_var.set("Policy comparison shown below for 1-, 3-, and 5-year terms.")

    for idx, years in enumerate(POLICY_TERMS):
        guaranteed_total = baseline_savings * years
        net_after_term = guaranteed_total - investment
        payback_reached = "Yes" if guaranteed_total >= investment else "No"
        net_text = f"+{money(net_after_term)}" if net_after_term >= 0 else f"-{money(abs(net_after_term))}"

        policy_table.insert(
            "",
            "end",
            values=(f"{years}-Year", money(guaranteed_total), net_text, payback_reached),
            tags=("even" if idx % 2 == 0 else "odd",),
        )

    for idx, (name, cost_low, cost_high, disc_low, disc_high, why_text) in enumerate(MITIGATION_ACTIONS):
        annual_savings_low = annual_premium * (disc_low / 100.0)
        annual_savings_high = annual_premium * (disc_high / 100.0)

        payback_low_years = float("inf") if annual_savings_high == 0 else cost_low / annual_savings_high
        payback_high_years = float("inf") if annual_savings_low == 0 else cost_high / annual_savings_low

        actions_table.insert(
            "",
            "end",
            values=(
                name,
                cost_range_text(cost_low, cost_high),
                f"{percent(disc_low)}-{percent(disc_high)}",
                cost_range_text(annual_savings_low, annual_savings_high),
                f"{years_text(payback_low_years)}-{years_text(payback_high_years)}",
                why_text,
            ),
            tags=(("even",) if idx % 2 == 0 else ("odd",)),
        )


root = tk.Tk()
root.title("Wildfire Mitigation Payback Calculator")
root.geometry("1300x760")
root.minsize(1080, 620)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("Header.TLabel", font=("Segoe UI Semibold", 16))
style.configure("Sub.TLabel", font=("Segoe UI", 10))
style.configure("Result.TLabel", font=("Segoe UI Semibold", 10))

container = ttk.Frame(root)
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, highlightthickness=0)
canvas.pack(side="left", fill="both", expand=True)

app_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
app_scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=app_scrollbar.set)

main = ttk.Frame(canvas, padding=14)
canvas_window = canvas.create_window((0, 0), window=main, anchor="nw")


def on_main_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


def on_canvas_configure(event):
    canvas.itemconfigure(canvas_window, width=event.width)


def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


main.bind("<Configure>", on_main_configure)
canvas.bind("<Configure>", on_canvas_configure)
canvas.bind_all("<MouseWheel>", on_mousewheel)

ttk.Label(main, text="Wildfire Resilience Pays Off", style="Header.TLabel").pack(anchor="w")
ttk.Label(
    main,
    text="How Multi-year Insurance Savings Guarantees Unlock Return on Investment",
    style="Sub.TLabel",
).pack(anchor="w", pady=(0, 12))

inputs = ttk.LabelFrame(main, text="Inputs")
inputs.pack(fill="x", pady=(0, 10))

investment_var = tk.StringVar(value=str(DEFAULT_INVESTMENT))
annual_premium_var = tk.StringVar(value=str(DEFAULT_ANNUAL_PREMIUM))

ttk.Label(inputs, text="Total investment ($):").grid(row=0, column=0, sticky="w", padx=10, pady=8)
ttk.Entry(inputs, textvariable=investment_var, width=16).grid(row=0, column=1, sticky="w", pady=8)

ttk.Label(inputs, text="Annual wildfire premium portion ($/yr):").grid(row=0, column=2, sticky="w", padx=(20, 10), pady=8)
ttk.Entry(inputs, textvariable=annual_premium_var, width=16).grid(row=0, column=3, sticky="w", pady=8)

ttk.Button(inputs, text="Calculate", command=update_results).grid(row=0, column=4, padx=(20, 10), pady=8)

results = ttk.LabelFrame(main, text="Results")
results.pack(fill="x", pady=(0, 10))

guaranteed_savings_result_var = tk.StringVar(value="Guaranteed savings over 5 years: --")
payback_result_var = tk.StringVar(value="Payback period: --")
term_result_var = tk.StringVar(value="ROI after 5 years: --")
status_var = tk.StringVar(value="")

ttk.Label(results, textvariable=guaranteed_savings_result_var, style="Result.TLabel").pack(anchor="w", padx=10, pady=(8, 4))
ttk.Label(results, textvariable=payback_result_var, style="Result.TLabel").pack(anchor="w", padx=10, pady=4)
ttk.Label(results, textvariable=term_result_var, style="Result.TLabel").pack(anchor="w", padx=10, pady=(4, 8))
ttk.Label(results, textvariable=status_var, foreground="#b42318").pack(anchor="w", padx=10, pady=(0, 8))

policy_columns = ("term", "savings", "net", "payback")
policy_table = ttk.Treeview(results, columns=policy_columns, show="headings", height=3)
policy_table.heading("term", text="Policy Term")
policy_table.heading("savings", text="Guaranteed Savings")
policy_table.heading("net", text="Net After Term")
policy_table.heading("payback", text="Payback Reached")
policy_table.column("term", width=120, anchor="center")
policy_table.column("savings", width=180, anchor="e")
policy_table.column("net", width=160, anchor="e")
policy_table.column("payback", width=140, anchor="center")
policy_table.pack(fill="x", padx=10, pady=(0, 10))

policy_table.tag_configure("odd", background="#f6f8fb")
policy_table.tag_configure("even", background="#ffffff")

table_frame = ttk.LabelFrame(main, text="Wildfire Mitigation Actions")
table_frame.pack(fill="both", expand=True)

columns = ("action", "cost", "discount", "savings", "payback", "why")
actions_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
actions_table.heading("action", text="Mitigation Action")
actions_table.heading("cost", text="Cost Range")
actions_table.heading("discount", text="Discount Range")
actions_table.heading("savings", text="Annual Savings Range")
actions_table.heading("payback", text="Payback Range (Years)")
actions_table.heading("why", text="Why It Matters")
actions_table.column("action", width=260, anchor="w")
actions_table.column("cost", width=120, anchor="e")
actions_table.column("discount", width=110, anchor="center")
actions_table.column("savings", width=150, anchor="e")
actions_table.column("payback", width=170, anchor="center")
actions_table.column("why", width=420, anchor="w")

table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=actions_table.yview)
actions_table.configure(yscrollcommand=table_scroll.set)
actions_table.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
table_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8)

actions_table.tag_configure("odd", background="#f6f8fb")
actions_table.tag_configure("even", background="#ffffff")

info_tabs = ttk.Notebook(main)
info_tabs.pack(fill="x", pady=(10, 0))

assumptions_tab = ttk.Frame(info_tabs, padding=10)
sources_tab = ttk.Frame(info_tabs, padding=10)
info_tabs.add(assumptions_tab, text="Assumptions")
info_tabs.add(sources_tab, text="Sources")

assumptions_text = (
    "1) Annual savings per mitigation action are estimated from annual wildfire premium x discount range.\n"
    "2) Payback range uses low cost with high savings (best case) and high cost with low savings (conservative case).\n"
    "3) Discount ranges are indicative and insurer underwriting rules vary by carrier and location.\n"
    "4) Actions may not stack linearly in real policies; full-suite certifications may replace itemized discounts.\n"
    "5) Policy comparison uses 1-, 3-, and 5-year terms with a representative 12.5% annual savings rate."
)
ttk.Label(assumptions_tab, text=assumptions_text, wraplength=1220, justify="left").pack(anchor="w")

sources_text = (
    "FutureProof analysis; Headwaters Economics (Barrett & Quarles 2025); "
    "RFF WP 25-30 (Ludington, Liao & Walls, Dec. 2025); Insurance for Good (Kousky & You, Nov. 2025); "
    "IBHS Wildfire Prepared Home program materials and WUI hardening guidance."
)
ttk.Label(sources_tab, text=sources_text, wraplength=1220, justify="left").pack(anchor="w")

update_results()
root.mainloop()
