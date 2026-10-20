# Data Dictionary

All data is synthetic, generated with Python. No real members or loans.

## Loans (one row per loan)

| Column | Meaning | Type | Example |
|---|---|---|---|
| loan_id | Unique loan number | Text | L000123 |
| member_id | Unique member number | Text | M00456 |
| disbursement_date | Date the loan was paid out | Date | 2024-03-15 |
| loan_amount | Amount borrowed (KES) | Number | 250000 |
| term_months | Repayment period in months | Number | 24 |
| interest_rate_monthly | Interest per month, reducing balance | Percent | 1.0% |
| product | Type of loan | Text | Development |
| member_group | Member occupation group | Text | Teacher |
| branch | Branch where the member banks | Text | Nakuru |
| member_deposits | Member savings at the time of the loan (KES) | Number | 120000 |
| guarantor_cover | Savings of guarantors pledged (KES) | Number | 90000 |
| status | Current loan status | Text | Active / Closed / Written-off |

## Monthly_Perf (one row per loan per month)

| Column | Meaning | Type | Example |
|---|---|---|---|
| loan_id | Links to Loans | Text | L000123 |
| reporting_month | Month-end date | Date | 2024-06-30 |
| outstanding_balance | Principal still owed (KES) | Number | 198000 |
| days_past_due | Days the loan is behind on payments | Number | 35 |