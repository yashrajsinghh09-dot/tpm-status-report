# TPM Weekly Status Report Generator

**Problem it solves:** in the PSI scenario we missed Sagar Publications' Friday status report. Writing two client reports by hand every Friday takes 30-45 minutes and is easy to skip when the week is busy. This tool turns the project tracker (Task 5) into one client-ready report per project in a few seconds, plus an internal checklist of what the TPM must fix before sending.

## What it does

| Input | Output (in `reports/`) |
|---|---|
| Tracker `.xlsx` with tabs **Summary** and **Risks and Issues** (or a folder with `summary.csv` + `risks.csv`) | `<Project>_<Client>_<date>.html` - email-ready report (paste into Gmail/Outlook) |
| | `<Project>_<Client>_<date>.md` - same report as plain text |
| | `TPM_check_<date>.md` - **internal only**: Red projects, overdue items, items due soon, missing owners, leaks |

Rules the tool follows:

- **Only risks marked `Share with client = Y`** and not `Closed` go to the client, top 5 by probability x impact. Internal items (staff leave, team load, our AI cost) stay internal.
- **No owner names in client reports.** The client sees the risk, what we are doing, and the date.
- **No cross-client leaks.** If any client-facing text names another project or client in the tracker, that risk is left out and flagged. If a Summary field leaks, that project's report is not written at all.
- Plain words. Status is explained in one line (Red = a key date is at risk).

## Run it

Needs Python 3.9+.

```bash
pip install -r requirements.txt
python status_report.py T5_Project_Tracker.xlsx --date 2026-11-16
```

(On Mac, use `python3` and `pip3`.)

Output:

```
[  RED] Kavach -> reports/Kavach_Nirmal_Finance_2026-11-16.html  (4 client risks)
[AMBER] Ledger -> reports/Ledger_Sagar_Publications_2026-11-16.html  (4 client risks)

TPM check (13 items) -> reports/TPM_check_2026-11-16.md
  - RED project: Kavach. Call the client, do not rely on the report alone.
  - DUE SOON: K-01 due Tue 17 Nov 2026 (owner: Meera (till Tue), then Arjun).
  ...
```

Other options:

```bash
python status_report.py . --date 2026-11-16              # CSV input: folder with summary.csv + risks.csv
python status_report.py my_tracker.xlsx --out friday       # date defaults to today
python -m unittest                                         # 5 tests
```

Reports are written to a `reports/` folder. Open the `.html` file in a browser, select all, copy, paste into an email.

Repo contents: the tool (`status_report.py`), the sample tracker (`T5_Project_Tracker.xlsx`, and the same data as `summary.csv` + `risks.csv`), tests (`test_status_report.py`), and sample output from the run above (`Kavach_...`, `Ledger_...`, `TPM_check_...`).

## Tracker columns

Column names are matched ignoring case and punctuation, so column order does not matter.

- **Summary:** Project, Client, Client contact, Status (RAG), Next milestone, Milestone date, Go-live date, Main problem, Progress this week, Next steps, Need from client, Last updated
- **Risks and Issues:** ID, Project, Type, Description, Probability, Impact, Score, Owner, Action, Due date, Status, Share with client

The tool works out the score itself (High 3, Medium 2, Low 1) so it does not depend on Excel formulas having been calculated.

## How I built it with AI

Built with Claude (Anthropic). The AI wrote the code from the prompts below. Every output file was run and read before use, and corrected where it was wrong.

### Prompts used

1. > Build a Python command-line tool. Input: my project tracker Excel with tabs "Summary" (one row per project: project, client, client contact, status RAG, next milestone, milestone date, go-live date, main problem, progress this week, next steps, need from client, last updated) and "Risks and Issues" (ID, project, type, description, probability, impact, score, owner, action, due date, status, share with client). Output: one weekly status report per project, as Markdown and as email-ready HTML with inline CSS. Use only openpyxl. The reader is a busy client executive: plain words, status first, then what we need from them.

2. > In the client report, only include risks where "Share with client" is Y and status is not Closed. Sort by probability x impact, show at most 5. Do not show owner names to the client: show the risk, what we are doing, and the date.

3. > Add an internal TPM check file that is never sent to clients: Red projects, overdue items, items due today or in the next 2 days, items with no owner/action/due date, top-score items still Open, and projects whose summary was not updated in 7 days.

4. > Also accept a folder with summary.csv and risks.csv. Match column names ignoring case and punctuation. Give a clear error if a tab or column is missing.

5. > The Ledger report for Sagar Publications mentions "Kavach", which is another client's project. Add a guard: any client-facing text that names another project or client from the tracker must not go into a report. Leave out such risks and list them in the TPM check. If a Summary field has a leak, do not write that report at all.

6. > Write unittest tests: an internal risk never reaches the client, a risk naming another client is left out, a Summary leak blocks the report, an overdue item is flagged, a closed risk is not shown.

### One error the AI made, and how I corrected it

**The error:** the first version filtered risks for each client only by the `Share with client` column. The code ran with no errors and the logic looked right. But the generated Ledger report, meant for Sagar Publications, contained this shared risk: *"WhatsApp birthday offers at go-live... could delay go-live and pull people from Kavach."* Kavach is Nirmal Finance's project. Sending it would leak one client's information to another.

**How it was found:** by reading the generated report, not the code. The column filter was correct; the problem was the text inside a row marked Y.

**How it was corrected:**
1. Prompt 5 above: a guard that checks all client-facing text against every other project and client name in the tracker. Leaking risks are left out and flagged in the TPM check; a leaking Summary field stops that report completely.
2. Reworded the risk in the tracker so it is client-safe (team load is tracked in internal rows instead).
3. Added tests (prompt 6). Writing the tests also found a second bug: a tracker with zero risks crashed the tool, because the column check looked at the first row instead of the header. Fixed.

**Lesson:** AI code that runs is not the same as output that is safe to send. The TPM still reads what goes to the client.

## Limits and next steps

- It does not send email. That is on purpose: a person reads the report before a client sees it.
- Next step: read the tracker directly from Google Sheets, and schedule it for Friday 3 PM so the draft is ready an hour before the report is due.
