#!/usr/bin/env python3
"""
Weekly client status report generator.

Reads the project tracker (Excel file with a "Summary" tab and a
"Risks and Issues" tab, or a folder with summary.csv and risks.csv)
and writes, for each project:
  - a client status report as Markdown and as email-ready HTML
and one internal "TPM check" file with things the TPM must fix first.

Usage:
  python status_report.py tracker.xlsx
  python status_report.py tracker.xlsx --date 2026-11-20 --out reports
  python status_report.py sample/csv            (folder with summary.csv + risks.csv)
"""
import argparse
import csv
import html
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Column names we need, after normalising the header text.
SUMMARY_REQUIRED = ["project", "client", "status", "next milestone", "milestone date", "main problem"]
RISK_REQUIRED = ["id", "project", "type", "description", "probability", "impact",
                 "owner", "action", "due date", "status", "share with client"]
ALIASES = {"status rag": "status", "rag": "status", "rag status": "status"}

LEVEL = {"high": 3, "medium": 2, "low": 1}
STATUS_TEXT = {
    "red": "A key date is at risk. Our actions and your decisions below are needed now.",
    "amber": "There is a problem, but the date is safe if the actions below work.",
    "green": "On track.",
}
STATUS_COLOUR = {"red": "#C62828", "amber": "#EF6C00", "green": "#2E7D32"}
MAX_CLIENT_RISKS = 5


# ---------------------------------------------------------------- reading
class Rows(list):
    """A list of row dicts that also remembers the header (works when there are no rows)."""
    def __init__(self, columns):
        super().__init__()
        self.columns = list(columns)


def norm(header):
    key = re.sub(r"[^a-z0-9]+", " ", str(header or "").lower()).strip()
    return ALIASES.get(key, key)


def rows_from_table(header, rows):
    keys = [norm(h) for h in header]
    out = Rows(k for k in keys if k)
    for r in rows:
        if r is None or all(v in (None, "") for v in r):
            continue
        out.append({k: v for k, v in zip(keys, r) if k})
    return out


def read_xlsx(path):
    from openpyxl import load_workbook  # only needed for Excel input
    wb = load_workbook(path, data_only=True)
    tabs = {norm(name): wb[name] for name in wb.sheetnames}
    if "summary" not in tabs or "risks and issues" not in tabs:
        sys.exit(f"Error: {path} needs tabs 'Summary' and 'Risks and Issues'. Found: {wb.sheetnames}")
    result = []
    for tab in ("summary", "risks and issues"):
        values = list(tabs[tab].iter_rows(values_only=True))
        result.append(rows_from_table(values[0], values[1:]))
    return result


def read_csv_folder(folder):
    result = []
    for name in ("summary.csv", "risks.csv"):
        f = folder / name
        if not f.exists():
            sys.exit(f"Error: {folder} must contain summary.csv and risks.csv")
        with f.open(newline="", encoding="utf-8-sig") as fh:
            values = list(csv.reader(fh))
        result.append(rows_from_table(values[0], values[1:]))
    return result


def check_columns(rows, required, tab, need_rows=True):
    if need_rows and not rows:
        sys.exit(f"Error: tab '{tab}' has no rows.")
    missing = [c for c in required if c not in rows.columns]
    if missing:
        sys.exit(f"Error: tab '{tab}' is missing columns: {', '.join(missing)}")


def to_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d/%m/%Y", "%d %b %Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def text(value):
    return "" if value is None else str(value).strip()


def nice_date(d):
    return d.strftime("%a %d %b %Y") if d else "date not set"


def sentences(value):
    """Split a tracker cell into bullet points, one per sentence."""
    parts = re.split(r"(?<=\.)\s+(?=[A-Z0-9])", text(value))
    return [p.strip() for p in parts if p.strip()]


def other_names(summary, project):
    """Names of the OTHER projects and clients in the tracker."""
    names = set()
    for p in summary:
        if text(p["project"]).lower() != project.lower():
            names.update({text(p["project"]), text(p.get("client"))})
    return {n for n in names if n}


def leaks(value, names):
    """Return the other-client names that appear in this text."""
    return sorted(n for n in names if re.search(rf"\b{re.escape(n)}\b", text(value), re.IGNORECASE))


def score(risk):
    return LEVEL.get(text(risk["probability"]).lower(), 1) * LEVEL.get(text(risk["impact"]).lower(), 1)


# ---------------------------------------------------------------- building
def client_risks(project, risks):
    picked = [r for r in risks
              if text(r["project"]).lower() == project.lower()
              and text(r["share with client"]).upper().startswith("Y")
              and text(r["status"]).lower() != "closed"]
    picked.sort(key=lambda r: (-score(r), to_date(r["due date"]) or date.max))
    return picked[:MAX_CLIENT_RISKS]


SUMMARY_CLIENT_FIELDS = ["next milestone", "main problem", "progress this week", "next steps", "need from client"]


def build_report(p, risks, report_date, names, warnings):
    """Build one client report. Text that names another client is kept out."""
    project = text(p["project"])
    blocked = {f: leaks(p.get(f), names) for f in SUMMARY_CLIENT_FIELDS}
    blocked = {f: n for f, n in blocked.items() if n}
    if blocked:
        for f, n in blocked.items():
            warnings.append(f"BLOCKED: {project} report NOT written. Summary field '{f}' names {', '.join(n)}.")
        return None
    shared = []
    for r in client_risks(project, risks):
        found = leaks(r["description"], names) + leaks(r["action"], names)
        if found:
            warnings.append(f"LEFT OUT: {text(r['id'])} not sent to {text(p['client'])}: it names "
                            f"{', '.join(sorted(set(found)))}. Reword it for the client.")
        else:
            shared.append(r)
    status = text(p["status"]).lower()
    milestone_date = to_date(p.get("milestone date"))
    golive = to_date(p.get("go live date"))
    return {
        "project": text(p["project"]),
        "client": text(p["client"]),
        "contact": text(p.get("client contact")),
        "status": status,
        "status_label": status.upper() or "NOT SET",
        "status_text": STATUS_TEXT.get(status, "Status not set in the tracker."),
        "milestone": f"{text(p['next milestone'])} - {nice_date(milestone_date)}",
        "golive": nice_date(golive) if golive else "",
        "problem": text(p["main problem"]),
        "progress": sentences(p.get("progress this week")),
        "next": sentences(p.get("next steps")),
        "need": sentences(p.get("need from client")),
        "risks": [{"risk": text(r["description"]), "action": text(r["action"]),
                   "by": nice_date(to_date(r["due date"]))} for r in shared],
        "date": nice_date(report_date),
    }


def to_markdown(r):
    lines = [f"# {r['project']} - Weekly status report",
             f"**{r['client']}** | To: {r['contact'] or 'client'} | Report date {r['date']}", "",
             f"## Overall status: {r['status_label']}", r["status_text"], "",
             f"**Next milestone:** {r['milestone']}"]
    if r["golive"]:
        lines.append(f"**Go-live:** {r['golive']}")
    lines += ["", f"**Main issue:** {r['problem']}", ""]
    for title, items in (("Progress this week", r["progress"]), ("Next steps", r["next"]),
                         ("What we need from you", r["need"])):
        if items:
            lines += [f"## {title}"] + [f"- {i}" for i in items] + [""]
    if r["risks"]:
        lines += ["## Risks and what we are doing", "| Risk | What we are doing | By |", "|---|---|---|"]
        lines += [f"| {x['risk']} | {x['action']} | {x['by']} |" for x in r["risks"]]
        lines.append("")
    lines += ["Questions? Reply to this email or call me any time.", "",
              "Yashraj Singh, Technical Program Manager, PanScience Innovations"]
    return "\n".join(lines) + "\n"


def to_html(r):
    e = html.escape
    colour = STATUS_COLOUR.get(r["status"], "#555")

    def section(title, items):
        if not items:
            return ""
        li = "".join(f"<li style='margin:0 0 4px'>{e(i)}</li>" for i in items)
        return f"<h3 style='color:#1F3A5F;margin:18px 0 6px;font-size:15px'>{e(title)}</h3><ul style='margin:0;padding-left:20px'>{li}</ul>"

    risk_rows = "".join(
        f"<tr><td style='{TD}'>{e(x['risk'])}</td><td style='{TD}'>{e(x['action'])}</td>"
        f"<td style='{TD};white-space:nowrap'>{e(x['by'])}</td></tr>" for x in r["risks"])
    risk_table = "" if not r["risks"] else (
        "<h3 style='color:#1F3A5F;margin:18px 0 6px;font-size:15px'>Risks and what we are doing</h3>"
        f"<table style='border-collapse:collapse;width:100%;font-size:13px'><tr>"
        f"<th style='{TH}'>Risk</th><th style='{TH}'>What we are doing</th><th style='{TH}'>By</th></tr>{risk_rows}</table>")
    golive = f"<div><b>Go-live:</b> {e(r['golive'])}</div>" if r["golive"] else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{e(r['project'])} - weekly status</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;color:#222;max-width:720px;margin:24px auto;padding:0 16px;font-size:14px;line-height:1.45">
<h2 style="color:#1F3A5F;margin:0">{e(r['project'])} - Weekly status report</h2>
<div style="color:#666;margin:4px 0 16px">{e(r['client'])} | To: {e(r['contact'] or 'client')} | Report date {e(r['date'])}</div>
<div style="border-left:6px solid {colour};background:#F7F7F7;padding:10px 14px;margin-bottom:14px">
  <div style="font-size:16px"><b>Overall status: <span style="color:{colour}">{e(r['status_label'])}</span></b></div>
  <div>{e(r['status_text'])}</div>
</div>
<div><b>Next milestone:</b> {e(r['milestone'])}</div>
{golive}
<div style="margin-top:10px"><b>Main issue:</b> {e(r['problem'])}</div>
{section('Progress this week', r['progress'])}
{section('Next steps', r['next'])}
{section('What we need from you', r['need'])}
{risk_table}
<p style="margin-top:22px">Questions? Reply to this email or call me any time.</p>
<p>Yashraj Singh<br>Technical Program Manager, PanScience Innovations</p>
</body></html>
"""


TH = "background:#1F3A5F;color:#fff;text-align:left;padding:6px 8px;border:1px solid #ccc"
TD = "padding:6px 8px;border:1px solid #ccc;vertical-align:top"


def tpm_check(summary, risks, report_date, warnings):
    """Internal list: what the TPM must fix before sending anything."""
    out = list(warnings)
    soon = report_date + timedelta(days=2)
    for p in summary:
        name = text(p["project"])
        if text(p["status"]).lower() == "red":
            out.append(f"RED project: {name}. Call the client, do not rely on the report alone.")
        updated = to_date(p.get("last updated"))
        if updated and (report_date - updated).days > 7:
            out.append(f"STALE: {name} summary last updated {nice_date(updated)}. Update it before sending.")
    for r in risks:
        rid, st = text(r["id"]), text(r["status"]).lower()
        if st == "closed":
            continue
        due = to_date(r["due date"])
        if not text(r["owner"]) or not text(r["action"]) or not due:
            out.append(f"INCOMPLETE: {rid} has no owner, action or due date.")
        elif due < report_date:
            out.append(f"OVERDUE: {rid} was due {nice_date(due)} (owner: {text(r['owner'])}).")
        elif due == report_date:
            out.append(f"DUE TODAY: {rid} (owner: {text(r['owner'])}).")
        elif due <= soon:
            out.append(f"DUE SOON: {rid} due {nice_date(due)} (owner: {text(r['owner'])}).")
        if score(r) == 9 and st == "open":
            out.append(f"NOT STARTED: {rid} has the top score (9) but is still 'Open'.")
    return out


def safe(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def main():
    ap = argparse.ArgumentParser(description="Make weekly client status reports from the TPM tracker.")
    ap.add_argument("tracker", help="tracker .xlsx file, or a folder with summary.csv and risks.csv")
    ap.add_argument("--date", help="report date YYYY-MM-DD (default: today)")
    ap.add_argument("--out", default="reports", help="output folder (default: reports)")
    args = ap.parse_args()

    src = Path(args.tracker)
    if not src.exists():
        sys.exit(f"Error: {src} not found")
    summary, risks = read_csv_folder(src) if src.is_dir() else read_xlsx(src)
    check_columns(summary, SUMMARY_REQUIRED, "Summary")
    check_columns(risks, RISK_REQUIRED, "Risks and Issues", need_rows=False)

    report_date = to_date(args.date) if args.date else date.today()
    if report_date is None:
        sys.exit("Error: --date must look like 2026-11-20")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    stamp = report_date.isoformat()
    warnings = []
    for p in summary:
        r = build_report(p, risks, report_date, other_names(summary, text(p["project"])), warnings)
        if r is None:
            print(f"[ STOP] {text(p['project'])} -> not written, see TPM check")
            continue
        base = out / f"{safe(r['project'])}_{safe(r['client'])}_{stamp}"
        base.with_suffix(".md").write_text(to_markdown(r), encoding="utf-8")
        base.with_suffix(".html").write_text(to_html(r), encoding="utf-8")
        print(f"[{r['status_label']:>5}] {r['project']} -> {base}.html  ({len(r['risks'])} client risks)")

    checks = tpm_check(summary, risks, report_date, warnings)
    (out / f"TPM_check_{stamp}.md").write_text(
        f"# TPM check - {nice_date(report_date)} (internal, do not send)\n\n"
        + ("\n".join(f"- {c}" for c in checks) if checks else "- Nothing to fix.") + "\n", encoding="utf-8")
    print(f"\nTPM check ({len(checks)} items) -> {out / f'TPM_check_{stamp}.md'}")
    for c in checks:
        print("  -", c)


if __name__ == "__main__":
    main()
