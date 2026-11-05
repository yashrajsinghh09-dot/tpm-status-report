# Kavach - Weekly status report
**Nirmal Finance** | To: CTO | Report date Mon 16 Nov 2026

## Overall status: RED
A key date is at risk. Our actions and your decisions below are needed now.

**Next milestone:** UAT starts (if IP approval and EMI fix are done by Wed 6 PM) - Thu 19 Nov 2026
**Go-live:** Wed 25 Nov 2026

**Main issue:** In our tests, 4 of 50 calls gave a wrong EMI amount and 2 calls ended at about 40 seconds. The provider's new IP addresses need approval from Nirmal's network team before calls can work.

## Progress this week
- 50 test calls completed.
- Problems found and owners assigned.
- IP approval request sent to Nirmal's network team.

## Next steps
- Tue 17 Nov: cause of wrong amounts shared.
- Wed 18 Nov: 100-call retest.
- Thu 19 Nov: UAT starts.
- Tue 24 Nov: go / no-go.
- Wed 25 Nov: go-live (moved from Mon 23 Nov, to be confirmed).

## What we need from you
- Approve the new IP addresses by Wed 18 Nov, 6 PM.
- Confirm the new go-live date (Wed 25 Nov) and invite the MD.

## Risks and what we are doing
| Risk | What we are doing | By |
|---|---|---|
| Agent said the wrong EMI amount in 4 of 50 test calls (8%). Cause not known yet. | Find the cause. Make the agent read the amount from loan data in a fixed sentence (the AI must not write numbers). Retest 100 calls: 0 wrong amounts. | Tue 17 Nov 2026 |
| 2 of 50 test calls stopped after about 40 seconds. | Check call logs. Test if it is linked to the provider IP change or a timeout setting. Retest with 3-minute calls. | Wed 18 Nov 2026 |
| Telephone provider changed its IP addresses. Nirmal's network team must approve them (normally 3 working days). No calls work until then. | Request sent Mon 10 AM. Nirmal CTO asked to get approval by Wed 6 PM. | Wed 18 Nov 2026 |
| A wrong amount reaches a real borrower after go-live (complaints, regulatory risk for the client). | Day 1 pilot with 200 borrowers, every call checked. Kill switch stops calls within 15 minutes. | Tue 24 Nov 2026 |

Questions? Reply to this email or call me any time.

Yashraj Singh, Technical Program Manager, PanScience Innovations
