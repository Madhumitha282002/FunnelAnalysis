# Experiment Proposal: Express Payment for First-Time Buyers

## Summary
New users who reach checkout add payment information at 43.9%, against 81.6% for all other users. This proposal tests whether showing express wallet payment options at the top of checkout closes part of that gap. The test randomizes first-time visitors who reach checkout, measures purchase within 7 days, and runs for 5 weeks of enrollment plus 1 week of follow-up. It is powered to detect a 15% relative lift. A lift of that size would add roughly $12K to $24K in revenue over a comparable 92-day period.

## Problem
- New users are the largest leak in the funnel (Day 3). At checkout, they reach the payment step at 43.9%, against 81.6% for everyone else.
- The gap is sharpest at payment. Across other funnel steps, new users convert at 0.67 to 0.82 times the rate of other users. At checkout to payment, the ratio is 0.54.
- 4,195 new-user checkout sessions ended without a purchase over the 92-day period.

## Evidence
| Source | Finding |
|---|---|
| Day 3 | New-user payment gap holds on every device: 43.4% to 44.5% for new users, against 80.9% to 87.7% for returning users. |
| Day 3 | The gap holds within every checkout entry type, so it is not explained by cart behavior. |
| Day 4 | Returning users purchase faster and need fewer steps, consistent with saved accounts and payment details. |
| Day 6 | Only 4.65% of new-user checkout abandoners purchase in a later session. Lost checkouts are mostly lost purchases. |
| Day 6 | About 94% of new users who buy within 7 days of reaching checkout buy in that same session. |

## Hypothesis
If first-time visitors see express wallet payment options at the top of the checkout page, more of them will complete payment and purchase. Returning users likely benefit from saved addresses and payment methods. First-time buyers must enter everything manually, which creates friction at exactly the step where they drop off.

## Design

| Element | Specification |
|---|---|
| Treatment | Express wallet buttons (for example, Google Pay and PayPal) shown above the standard payment form |
| Control | Current checkout experience |
| Eligibility | Users reaching checkout during their first visit to the store |
| Unit of randomization | User (first-party browser cookie) |
| Split | 50/50 |
| Enrollment period | 5 weeks, outside the mid-December to mid-January holiday window |
| Follow-up | 7 days after the last enrollment, so every user has a full measurement window |
| Total runtime | 6 weeks |

## Metrics

| Type | Metric | Baseline |
|---|---|---|
| Primary | Purchase within 7 days of first reaching checkout (user-level) | 31.79% |
| Secondary | Checkout to payment info (session-level) | 43.90% |
| Secondary | Payment info to purchase (session-level) | 67.86% |
| Secondary | Revenue per eligible user | Derived from primary and AOV |
| Guardrail | Average order value, new buyers | $71.49 |
| Guardrail | Payment error rate | To be instrumented before launch |
| Guardrail | Checkout page load time | To be instrumented before launch |
| Health check | Sample ratio mismatch (chi-square test on arm sizes) | Expected 50/50 |

## Power analysis
Inputs: two-sided test, alpha 0.05, power 0.80. About 92 eligible users per day, estimated from non-holiday traffic (excluding Dec 14 to Jan 17).

**Primary metric (user-level 7-day purchase)**

| Relative MDE | Target rate | Users per arm | Enrollment needed |
|---|---|---|---|
| 5% | 33.4% | 13,645 | 43 weeks |
| 10% | 35.0% | 3,452 | 11 weeks |
| **15%** | **36.6%** | **1,551** | **5 weeks** |

**Secondary metric (session-level checkout to payment)**

| Relative MDE | Target rate | Sessions per arm | Enrollment needed |
|---|---|---|---|
| 5% | 46.1% | 8,063 | 28 weeks |
| 10% | 48.3% | 2,023 | 7 weeks |
| 20% | 52.7% | 508 | 2 weeks |

**Chosen MDE: 15% relative on the primary metric.** Detecting 5% would take 43 weeks, which is impractical and exposed to seasonal drift. Detecting 10% would take 11 weeks, which is feasible but long. A 15% lift is plausible for this treatment, because the starting gap is large: returning users reach payment at nearly twice the new-user rate. Since about 94% of 7-day purchases happen in the exposure session, a 15% lift on the primary metric corresponds to roughly a 16% lift at the payment step.

**Tradeoff:** if the true effect is smaller than 15%, this test will likely be inconclusive. That outcome would be reported as "no large effect detected," not as evidence of no effect.

## Opportunity sizing
Sizing assumes the payment-to-purchase rate (67.86%) stays constant under treatment. It removes the 4.65% of abandoners who purchase later anyway, and values purchases at the new-buyer AOV of $71.49.

| Payment step lift | Net extra purchases (92 days) | Net extra revenue (92 days) | Per 30 days |
|---|---|---|---|
| 5% | 85 | $6,067 | $1,978 |
| 10% | 170 | $12,133 | $3,956 |
| 20% | 339 | $24,266 | $7,913 |

- The Day 3 ceiling of about $134K assumed new users could match returning users entirely. That is not realistic. A 10% to 20% lift is the plausible range for a single checkout change.
- The 92-day period includes the holiday peak, so per-30-day figures may overstate a typical month.
- These estimates exclude implementation cost and payment processing fees.

## Analysis plan
- Fixed-horizon analysis at the end of the follow-up period. No early stopping based on interim results.
- Primary analysis: two-proportion z-test on 7-day purchase rate, with a 95% confidence interval on the absolute and relative difference.
- Users are the unit of both randomization and analysis. Eligibility is a first visit, so almost every user contributes one checkout session, and session-level secondary metrics need no clustering correction.
- Pre-registered segment cuts: device category and traffic medium. These are descriptive only, not for ship decisions.
- Check sample ratio mismatch before reading any outcome. Pause the analysis if the SRM p-value falls below 0.001.

## Decision rule
- **Ship** if the primary metric improves significantly (p < 0.05), no guardrail worsens significantly, and the SRM check passes.
- **Do not ship** if any guardrail worsens significantly, such as AOV falling or payment errors rising, regardless of the primary result.
- **Inconclusive** if the primary metric is not significant. Then inspect the secondary metrics:
  - If checkout to payment improved but purchases did not, friction has moved downstream to order confirmation. Investigate that step next.
  - If neither moved, the treatment did not address the real barrier. Run qualitative research, such as session recordings or a checkout survey, before the next iteration.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Tracking gap: 29% of checkouts fire begin_checkout without item data (Day 4) | Fix event coverage on all checkout paths before launch, and confirm with an A/A test |
| Cookie churn: users who clear cookies may be re-randomized | Expected to be small over a 6-week test; monitor exposure counts per user |
| Cross-device users appear as new users | Affects both arms equally; note as a limitation |
| Seasonality (Day 5) | Run outside mid-December to mid-January |
| Novelty effect | Compare week 1 with weeks 4 to 5 of enrollment; a fading effect suggests novelty |
| Small traffic limits detectable effects | Accept the 15% MDE explicitly; consider extending eligibility to all users without saved payment details in a follow-up test |

## Prerequisites before launch
1. Fix add_to_cart and begin_checkout item tracking on all checkout paths.
2. Instrument payment error events and checkout page load time.
3. Run an A/A test for one week to validate randomization and event logging.
4. Confirm that revenue values are recorded correctly. The final week of the analysis period showed an implausible AOV of $16.70.