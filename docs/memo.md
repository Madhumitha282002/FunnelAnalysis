# Memo: Reduce Payment Friction for First-Time Buyers

**To:** Product and Growth Leads
**From:** Madhumitha Katam, Data Science
**Re:** Highest-value checkout fix, Google Merchandise Store (Nov 2020 to Jan 2021 data)

## Recommendation
Run a 6-week A/B test of express wallet payment options (such as Google Pay and PayPal) for first-time buyers at checkout. Fix checkout event tracking before launch. If the test succeeds at a 10% to 20% lift, it would add an estimated $12K to $24K in net revenue per 92 days.

## The problem
First-time visitors who reach checkout add payment information at 43.9%. All other users do so at 81.6%. That gap is the largest leak in the funnel, and it sits at the step where returning shoppers benefit from saved addresses and payment details.

## Evidence
- **The gap is consistent.** New users reach payment at 43.4% to 44.5% on every device, against 80.9% to 87.7% for returning users. It also holds regardless of how the shopper arrived at checkout.
- **Lost checkouts are lost sales.** Only 4.65% of new users who abandon checkout come back and buy later. Fixing this step produces new revenue, not purchases shifted from a later visit.
- **The rest of checkout works.** Payment to purchase converts at about 71%, and checkout completion held steady even during the holiday slowdown. The friction is specific to the payment step.

## The test

| Element | Plan |
|---|---|
| Who | Users reaching checkout on their first visit, split 50/50 |
| Primary metric | Purchase within 7 days of first reaching checkout (baseline 31.79%) |
| Guardrails | Average order value, payment errors, checkout load time |
| Duration | 5 weeks of enrollment plus 1 week of follow-up |
| Detectable effect | 15% relative lift, with 1,551 users per arm |
| Timing | Avoid mid-December to mid-January, when demand drops for seasonal reasons |

## Risks and limitations
- **Traffic limits precision.** The store sees about 92 eligible users per day, so the test can detect a 15% lift but not a 5% one. A smaller real effect would likely read as inconclusive.
- **Tracking needs repair first.** About 29% of checkout sessions fire without item data. These sessions convert worse and could distort results.
- **The source data has known gaps.** It is an obfuscated public sample, covers the holiday season, and identifies browsers rather than people.

## Next steps
1. Engineering: fix checkout event tracking and add payment error logging. Then run a one-week A/A test.
2. Product: confirm which express payment methods are feasible to integrate.
3. Data Science: launch the test outside the holiday window and report results at week 6.

Full analysis: [findings.md](findings.md). Test design: [experiment_proposal.md](experiment_proposal.md).