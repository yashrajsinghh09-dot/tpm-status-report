"""Run with:  python -m unittest"""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "status_report.py"

SUMMARY = ["Project", "Client", "Client contact", "Status (RAG)", "Next milestone", "Milestone date",
           "Go-live date", "Main problem", "Progress this week", "Next steps", "Need from client", "Last updated"]
RISKS = ["ID", "Project", "Type", "Description", "Probability", "Impact", "Score",
         "Owner", "Action", "Due date", "Status", "Share with client"]


def write(folder, name, header, rows):
    with (folder / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def run(folder, out):
    return subprocess.run([sys.executable, str(TOOL), str(folder), "--date", "2026-11-20", "--out", str(out)],
                          capture_output=True, text=True, check=True)


class StatusReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "out"
        self.summary = [
            ["Alpha", "Acme Ltd", "CEO", "Green", "Demo", "2026-11-25", "2026-12-01", "None", "Work done.", "Demo on Wed.", "Nothing.", "2026-11-20"],
            ["Beta", "Bolt Pvt", "COO", "Amber", "UAT", "2026-11-27", "2026-12-10", "Data issue.", "Fix built.", "Test fix.", "Answers.", "2026-11-20"],
        ]

    def risks(self, rows):
        write(self.tmp, "summary.csv", SUMMARY, self.summary)
        write(self.tmp, "risks.csv", RISKS, rows)
        return run(self.tmp, self.out)

    def test_internal_risk_never_reaches_client(self):
        self.risks([["B-1", "Beta", "Risk", "Staff leave next week", "High", "High", "", "TPM", "Cover plan", "2026-11-24", "Open", "N"]])
        report = (self.out / "Beta_Bolt_Pvt_2026-11-20.md").read_text()
        self.assertNotIn("Staff leave", report)

    def test_risk_naming_other_client_is_left_out(self):
        self.risks([["B-1", "Beta", "Risk", "Could pull people from Alpha", "High", "High", "", "TPM", "Plan", "2026-11-24", "Open", "Y"]])
        report = (self.out / "Beta_Bolt_Pvt_2026-11-20.md").read_text()
        check = (self.out / "TPM_check_2026-11-20.md").read_text()
        self.assertNotIn("Alpha", report)
        self.assertIn("LEFT OUT: B-1", check)

    def test_summary_naming_other_client_blocks_report(self):
        self.summary[1][7] = "Delayed because Acme Ltd needs the team."
        self.risks([])
        self.assertFalse((self.out / "Beta_Bolt_Pvt_2026-11-20.md").exists())
        self.assertIn("BLOCKED: Beta", (self.out / "TPM_check_2026-11-20.md").read_text())

    def test_overdue_item_is_flagged(self):
        self.risks([["A-1", "Alpha", "Issue", "Late vendor", "High", "Low", "", "Dev", "Chase", "2026-11-18", "Open", "Y"]])
        self.assertIn("OVERDUE: A-1", (self.out / "TPM_check_2026-11-20.md").read_text())

    def test_closed_risk_not_in_report(self):
        self.risks([["A-1", "Alpha", "Issue", "Old problem fixed", "High", "High", "", "Dev", "Done", "2026-11-18", "Closed", "Y"]])
        self.assertNotIn("Old problem", (self.out / "Alpha_Acme_Ltd_2026-11-20.md").read_text())


if __name__ == "__main__":
    unittest.main()
