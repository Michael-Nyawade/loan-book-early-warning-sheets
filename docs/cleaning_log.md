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