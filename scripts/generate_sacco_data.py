"""
generate_sacco_data.py
Generates a synthetic SACCO loan book and its monthly performance history.
Output (written to the data/ folder):
  raw_loans.csv          one row per loan (with deliberate data-quality issues)
  raw_monthly_perf.csv   one row per loan per month (with deliberate issues)
All data is synthetic. No real members or loans.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- settings
SEED = 2026                     # same seed = same data every time you run it
rng = np.random.default_rng(SEED)

N_MEMBERS = 4000
N_LOANS = 6000
FIRST_MONTH = pd.Period("2023-10", freq="M")
N_MONTHS = 36
END_MONTH = FIRST_MONTH + (N_MONTHS - 1)          # 2026-09 (reporting date)
OUT = Path(__file__).resolve().parent.parent / "data"

GROUPS = ["Teacher", "Civil Servant", "Trader/SME", "Farmer", "Other"]
GROUP_P = [0.30, 0.20, 0.25, 0.12, 0.13]
BRANCHES = ["Nairobi", "Nakuru", "Eldoret", "Kisumu", "Mombasa"]
BRANCH_P = [0.35, 0.20, 0.15, 0.15, 0.15]

# Typical monthly savings (KES) by group
MONTHLY_SAVING = {"Teacher": 5000, "Civil Servant": 6000, "Trader/SME": 3000,
                  "Farmer": 1500, "Other": 2500}

PRODUCT_NAMES = ["Emergency", "Development", "School Fees", "Biashara", "Asset Finance"]
PRODUCTS = {
    "Emergency":     dict(low=20_000,  high=150_000,   terms=[6, 9, 12],         rate=0.010, risk=1.3),
    "Development":   dict(low=100_000, high=800_000,   terms=[12, 18, 24, 36],   rate=0.010, risk=0.8),
    "School Fees":   dict(low=30_000,  high=250_000,   terms=[6, 9, 12],         rate=0.009, risk=0.9),
    "Biashara":      dict(low=50_000,  high=600_000,   terms=[12, 18, 24, 36],   rate=0.012, risk=1.7),
    "Asset Finance": dict(low=300_000, high=1_500_000, terms=[24, 36, 48],       rate=0.011, risk=1.0),
}
# Which products each group tends to take (same order as PRODUCT_NAMES)
PRODUCT_P = {
    "Teacher":       [0.20, 0.30, 0.30, 0.05, 0.15],
    "Civil Servant": [0.20, 0.30, 0.20, 0.05, 0.25],
    "Trader/SME":    [0.15, 0.15, 0.10, 0.50, 0.10],
    "Farmer":        [0.25, 0.20, 0.20, 0.25, 0.10],
    "Other":         [0.30, 0.20, 0.15, 0.20, 0.15],
}

# ---- risk settings: the monthly chance a current loan misses a payment
BASE_HAZARD = 0.013
GROUP_RISK = {"Teacher": 0.5, "Civil Servant": 0.6, "Trader/SME": 1.8,
              "Farmer": 1.6, "Other": 1.2}
VINTAGE_START, VINTAGE_END = pd.Period("2025-03", "M"), pd.Period("2025-08", "M")
VINTAGE_MULT = 1.8              # loans given out in those months are riskier
SHOCK_START, SHOCK_END = pd.Period("2026-05", "M"), pd.Period("2026-08", "M")
SHOCK_MULT = 1.7                # a bad patch for everyone in these calendar months
# Chance a late loan catches up this month, by how many payments it is behind
CURE_PROB = {1: 0.40, 2: 0.20, 3: 0.06}
WRITE_OFF_AT = 6                # 6 missed payments (about 180 days) = written off


def scheduled_balance(principal, rate, n_payments, paid):
    """Balance left after `paid` equal monthly instalments (reducing balance)."""
    if paid <= 0:
        return principal
    if paid >= n_payments:
        return 0.0
    pmt = principal * rate / (1 - (1 + rate) ** -n_payments)
    growth = (1 + rate) ** paid
    return principal * growth - pmt * (growth - 1) / rate


# ---------------------------------------------------------------- members
members = pd.DataFrame({
    "member_id": [f"M{i:05d}" for i in range(1, N_MEMBERS + 1)],
    "member_group": rng.choice(GROUPS, size=N_MEMBERS, p=GROUP_P),
    "branch": rng.choice(BRANCHES, size=N_MEMBERS, p=BRANCH_P),
    "join_date": pd.Timestamp("2014-01-01")
                 + pd.to_timedelta(rng.integers(0, 3200, size=N_MEMBERS), unit="D"),
})
members["monthly_saving"] = (
    members["member_group"].map(MONTHLY_SAVING) * rng.lognormal(0, 0.35, N_MEMBERS)
)
member_rows = members.to_dict("records")

# ---------------------------------------------------------------- loans
month_w = np.linspace(0.6, 1.4, N_MONTHS)       # lending grows over time
month_w = month_w / month_w.sum()
loan_month_idx = rng.choice(N_MONTHS, size=N_LOANS, p=month_w)
loan_member_idx = rng.integers(0, N_MEMBERS, size=N_LOANS)

loan_rows, perf_rows = [], []

for i in range(N_LOANS):
    mem = member_rows[loan_member_idx[i]]
    group = str(mem["member_group"])
    period = FIRST_MONTH + int(loan_month_idx[i])
    disb = pd.Timestamp(year=period.year, month=period.month, day=int(rng.integers(1, 29)))

    # savings the member has built up by the loan date
    tenure_months = max(6, (disb - mem["join_date"]).days // 30)
    deposits = int(max(10_000, round(mem["monthly_saving"] * tenure_months, -3)))

    product = str(rng.choice(PRODUCT_NAMES, p=PRODUCT_P[group]))
    spec = PRODUCTS[product]
    wanted = float(np.exp(rng.uniform(np.log(spec["low"]), np.log(spec["high"]))))
    guarantor_cover = wanted * rng.uniform(0, 1)         # savings pledged by guarantors
    # loan limit = 3 x own savings, topped up by guarantor savings
    amount = int(max(20_000, round(min(wanted, 3 * deposits + guarantor_cover), -3)))
    guarantor_cover = int(round(guarantor_cover, -3))
    term = int(rng.choice(spec["terms"]))
    rate = spec["rate"]

    # --- how risky is this loan?
    cover_ratio = (deposits + guarantor_cover) / amount
    cover_mult = 1.4 if cover_ratio < 1.0 else (0.8 if cover_ratio >= 1.5 else 1.0)
    vintage_mult = VINTAGE_MULT if VINTAGE_START <= period <= VINTAGE_END else 1.0
    base_h = BASE_HAZARD * GROUP_RISK[group] * spec["risk"] * cover_mult * vintage_mult

    # --- simulate month by month. k = number of payments the loan is behind
    k, m, status = 0, 0, "Active"
    loan_id = f"L{i + 1:06d}"
    perf_rows.append((loan_id, period.end_time.strftime("%Y-%m-%d"), amount, 0))

    while True:
        m += 1
        current = period + m
        if current > END_MONTH:
            break
        in_shock = SHOCK_START <= current <= SHOCK_END

        if k == 0:
            h = base_h * (0.3 if m <= 2 else 1.0)       # new loans rarely go bad at once
            if in_shock:
                h *= SHOCK_MULT * (1.3 if group in ("Trader/SME", "Farmer") else 1.0)
            if rng.random() < min(h, 0.25):
                k = 1
        else:
            cure = CURE_PROB[min(k, 3)] * (0.7 if in_shock else 1.0)
            k = 0 if rng.random() < cure else k + 1

        paid = max(0, min(m, term) - k)
        balance = int(round(scheduled_balance(amount, rate, term, paid)))
        dpd = 0 if k == 0 else 30 * k + int(rng.integers(0, 15))
        perf_rows.append((loan_id, current.end_time.strftime("%Y-%m-%d"), balance, dpd))

        if k >= WRITE_OFF_AT:
            status = "Written-off"
            break
        if m >= term and k == 0:
            status = "Closed"
            break

    loan_rows.append((loan_id, mem["member_id"], disb.strftime("%Y-%m-%d"), amount, term,
                      rate, product, group, mem["branch"], deposits, guarantor_cover, status))

loans = pd.DataFrame(loan_rows, columns=[
    "loan_id", "member_id", "disbursement_date", "loan_amount", "term_months",
    "interest_rate_monthly", "product", "member_group", "branch",
    "member_deposits", "guarantor_cover", "status"])
perf = pd.DataFrame(perf_rows, columns=[
    "loan_id", "reporting_month", "outstanding_balance", "days_past_due"])

# ---------------------------------------------------------------- quick sanity check
latest = perf[perf["reporting_month"] == END_MONTH.end_time.strftime("%Y-%m-%d")]
par30 = latest.loc[latest["days_past_due"] >= 30, "outstanding_balance"].sum() \
        / latest["outstanding_balance"].sum()
print(f"Loans: {len(loans):,}   Monthly rows: {len(perf):,}")
print(loans["status"].value_counts().to_string())
print(f"PAR30 at {END_MONTH}: {par30:.1%}")

# ---------------------------------------------------------------- add deliberate mess
# 1) inconsistent text in member_group
groups = loans["member_group"].tolist()
for j in rng.choice(len(groups), size=int(0.03 * len(groups)), replace=False):
    groups[j] = str(rng.choice([groups[j].lower(), groups[j].upper(), groups[j] + " "]))
loans["member_group"] = groups

# 2) trailing spaces and blanks in branch
branches = loans["branch"].tolist()
for j in rng.choice(len(branches), size=int(0.02 * len(branches)), replace=False):
    branches[j] = branches[j] + " "
for j in rng.choice(len(branches), size=int(0.01 * len(branches)), replace=False):
    branches[j] = None
loans["branch"] = branches

# 3) missing deposits
loans["member_deposits"] = loans["member_deposits"].astype("Int64")
loans.loc[rng.choice(len(loans), size=30, replace=False), "member_deposits"] = pd.NA

# 4) a few absurd loan amounts (an extra zero typed by mistake)
loans.loc[rng.choice(len(loans), size=3, replace=False), "loan_amount"] *= 10

# 5) duplicate rows
loans = pd.concat([loans, loans.sample(25, random_state=SEED)]).sort_values("loan_id", kind="stable")
perf["days_past_due"] = perf["days_past_due"].astype("Int64")
perf.loc[rng.choice(len(perf), size=50, replace=False), "days_past_due"] = pd.NA
perf = pd.concat([perf, perf.sample(100, random_state=SEED)]).sort_values(
    ["loan_id", "reporting_month"], kind="stable")

# ---------------------------------------------------------------- save
OUT.mkdir(exist_ok=True)
loans.to_csv(OUT / "raw_loans.csv", index=False)
perf.to_csv(OUT / "raw_monthly_perf.csv", index=False)
print(f"Saved files to {OUT}")