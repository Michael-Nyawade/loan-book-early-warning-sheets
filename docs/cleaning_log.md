# Cleaning Log

Source: `Raw_Import` (6,026 rows) and `Raw_Perf` (69,919 rows), both imported as text.

## Loans

| Issue | Count | Action |
|---|---|---|
| Duplicate rows | 25 | Removed with UNIQUE |
| Inconsistent case/spacing in member_group | about 3% of rows | Standardised with TRIM, LOWER and SWITCH |
| Blank branch | 60 | Set to "Unknown" (not guessed) |
| Missing member_deposits | 30 | Left blank and flagged; excluded from deposit-based analysis |
| Loan amount typed 10x too high | 3 | Detected by comparing loan_amount with the opening balance in Raw_Perf, and corrected to the opening balance |
| Numbers and dates stored as text | all rows | Converted with VALUE and DATEVALUE |

Reconciliation: the 3 corrections removed a total of KES 5,823,000 from the loan book.

## Monthly_Perf

| Issue | Count | Action |
|---|---|---|
| Duplicate rows | 100 | Removed with UNIQUE (69,919 → 69,818 rows) |
| Blank days_past_due | 50 | 46 filled with 0 where the loan's own record proves it (balance of 0, first month of the loan, or 0 in both neighbouring months); 4 left as REVIEW and excluded from roll rates |
| Months and balances stored as text | all rows | Converted with DATEVALUE and VALUE |

The 4 REVIEW rows are L004168, L005476, L004081 and L005766. L004081 and L005766 sit in the latest reporting month, so a sensitivity check on PAR30 will be shown in the analysis.