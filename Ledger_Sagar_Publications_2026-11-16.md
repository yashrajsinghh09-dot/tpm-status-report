# Ledger - Weekly status report
**Sagar Publications** | To: COO | Report date Mon 16 Nov 2026

## Overall status: AMBER
There is a problem, but the date is safe if the actions below work.

**Next milestone:** Duplicate-customer fix done in test system - Fri 20 Nov 2026
**Go-live:** Mon 21 Dec 2026

**Main issue:** The test migration created 1,200 duplicate customers (1.5% of 80,000), most likely because the old CRM stores phone numbers in different formats.

## Progress this week
- Sprint 4 of 6 in progress.
- Test migration of 80,000 records run.
- Duplicate cause found; fix specified.
- Live data and the old CRM are not affected.

## Next steps
- Wed 18 Nov: fix built.
- Fri 20 Nov: clean result in test system.
- Fri 20 Nov: decision on the WhatsApp change request.
- Mon 23 Nov: Sprint 5 starts.

## What we need from you
- Answer 5 questions on duplicate rules by Tue 17 Nov, 6 PM.
- Decide on the WhatsApp birthday offer change request by Fri 20 Nov.

## Risks and what we are doing
| Risk | What we are doing | By |
|---|---|---|
| New request: WhatsApp birthday offers at go-live. It is not in the agreed scope and adding it now could delay go-live. | Change request with 3 options sent Wed. No build before the COO signs. | Fri 20 Nov 2026 |
| Test migration created 1,200 duplicate customers (of 80,000). Likely cause: phone numbers in different formats. | Spec ready Mon. Fix built Wed with Claude Code. Code review Thu. QA check by Tue 24 Nov. | Fri 20 Nov 2026 |
| More data problems in the old CRM (emails, addresses, birth dates) cause new errors in the full run. | Run data quality checks on all 80,000 records before the Sprint 5 test run. | Fri 27 Nov 2026 |
| Client answers on the duplicate rules come late and the fix waits. | Questions sent Mon. If no answer by Tue 6 PM, build with stated rules (test system only) and adjust. | Tue 17 Nov 2026 |

Questions? Reply to this email or call me any time.

Yashraj Singh, Technical Program Manager, PanScience Innovations
