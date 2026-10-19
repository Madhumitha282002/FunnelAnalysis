# Findings

## Executive summary
- **Biggest leak:** first-time visitors who reach checkout add payment information at 43.9%, against 81.6% for all other users. The gap holds on every device and every checkout entry type.
- **Lost checkouts are mostly lost purchases:** only 4.65% of new users who abandon checkout buy in a later session.
- **Carts rarely reach checkout:** 39.3% of cart sessions start checkout in the same session, and same-session cart abandonment is 81.2%.
- **Seasonality, not a defect:** the largest weekly drop (1.64% to 1.06%, week of Dec 21) is a broad rate effect concentrated before checkout, consistent with post-shipping-cutoff demand.
- **Tracking gap:** about 29% of begin_checkout sessions fire without item data. This path converts worse and should be fixed before any checkout experiment.
- **Recommendation:** A/B test express wallet payments for first-time buyers. See [experiment_proposal.md](experiment_proposal.md).

---

## Base Funnel

### Scale
- 360,129 sessions from 270,154 users (1.33 sessions per user), Nov 1 2020 to Jan 31 2021.
- 4,848 sessions included a purchase. Session conversion rate is 1.35%.
- Average order value is $74.70, for about $362K in total purchase revenue.

### Funnel design
Event timing inside checkout is unreliable, and many checkouts happen without an add to cart in the same session. The funnel is therefore analyzed in two nested stages, joined by a same-session bridge.

**Browse funnel (nested within session)**

| Step | Sessions | % of all sessions | Step conversion |
|---|---|---|---|
| session_start | 360,129 | 100.0% | |
| view_item | 77,020 | 21.4% | 21.4% |
| add_to_cart | 15,173 | 4.2% | 19.7% |

**Bridge: cart to checkout (same session)**

| Metric | Value |
|---|---|
| Sessions with add_to_cart | 15,188 |
| Of those, started checkout in the same session | 5,962 (39.3%) |
| Of those, purchased in the same session | 2,848 (18.8% of cart sessions) |
| Same-session cart abandonment | 81.2% |

**Checkout funnel (nested from checkout entry)**

| Step | Sessions | % of checkouts | Step conversion |
|---|---|---|---|
| checkout_start | 11,107 | 100.0% | |
| add_payment_info | 6,813 | 61.3% | 61.3% |
| purchase | 4,845 | 43.6% | 71.1% |

The nested checkout funnel retains 4,845 of 4,848 purchase sessions (99.9%).

**Checkout sessions by entry type**

| Entry type | Checkout sessions | Share | Purchases | Checkout to purchase |
|---|---|---|---|---|
| Cart added this session | 5,962 | 53.7% | 2,848 | 47.8% |
| No cart tracked for this user | 4,766 | 42.9% | 1,745 | 36.6% |
| Cart added in a prior session | 379 | 3.4% | 252 | 66.5% |

### Key findings
1. **Most sessions never reach a product.** 78.6% of sessions end without a product view. Part of this is expected browsing behavior, so it is the least actionable drop.
2. **Product page to cart is the largest leak by volume.** Only 19.7% of product-viewing sessions add to cart. About 61,800 high-intent sessions view a product and leave without adding it.
3. **Most carts never reach checkout.** Only 39.3% of cart sessions start checkout in the same session. This bridge step loses about 9,200 cart sessions. The unordered funnel figure of 73.1% overstated it, because it counted checkouts with no cart in the session.
4. **Checkout to payment is the weakest step inside checkout.** 38.7% of checkout sessions (4,294) never add payment information. Payment to purchase is stronger at 71.1%.
5. **Checkouts with no tracked cart convert worse.** These sessions make up 42.9% of all checkouts but convert at 36.6%, against 47.8% for same-session carts. Day 4 traces this gap to a checkout path that fires without item data.
6. **Returning carts convert best but are rare.** Checkouts with a cart from a prior session convert at 66.5%, but this group is only 379 sessions (3.4%).

### Ordered vs unordered comparison
- The strict ordered funnel captured only 545 purchase sessions, 11% of the 4,848 in the data.
- Most of the loss came from begin_checkout and add_shipping_info. Of 11,104 sessions with both events, 61.8% logged add_shipping_info first, 38.2% logged it after, and none shared a timestamp.
- These two events have no consistent order, so they are merged into a single checkout_start step.
- Only 3 purchase sessions lack a checkout event, so purchase tracking is reliably tied to checkout.

### Follow-up questions and where they were answered
- Is "no cart tracked" concentrated in one device or channel? No. The share is nearly constant across segments (Day 3).
- Did those users add to cart on an earlier visit? Rarely. Only 379 checkouts had a prior-session cart (Day 2), and 62% of cart-less checkouts carried no item data at all (Day 4).
- Which segments drive the checkout leaks? New users, at the payment step (Day 3).

### Decision
- Primary analysis uses the two-stage nested funnel, plus the same-session cart to checkout bridge.
- The unordered funnel is kept as an upper bound. The strict ordered funnel is documented as a rejected method.
- Checkout entry type is used as a segment only for checkout-stage transitions, since it is defined by checkout behavior.

### Limitations
- user_pseudo_id identifies a browser or device, not a person. Cross-device journeys look like separate users.
- Carts created before Nov 1, 2020 are invisible, which inflates the "no cart tracked" group.
- Data is obfuscated. Revenue and some categorical values may be altered.
- The window covers the holiday season, so conversion may run higher than a typical quarter.

---

## Segmented Funnel

### Method
- Each segment was compared against all other sessions at each funnel transition, using Wilson 95% confidence intervals and two-proportion z-tests.
- 129 comparisons were tested. Benjamini-Hochberg correction controlled the false discovery rate at 5%.
- 23 comparisons were significant leaks, meaning the segment converted significantly worse than the rest.
- Leaks were ranked by lost sessions: the conversions the segment would gain at the rest-of-population rate. This is an upper-bound comparison, not a causal estimate.
- Checkout entry type was tested only on checkout transitions, since it is defined by checkout behavior.
- The two largest effects were checked for confounding with stratified tables by user type, entry type, and device.

### Top leaks

| Transition | Segment | Segment rate | Rest | Gap (pts) | Lost sessions |
|---|---|---|---|---|---|
| session_start to view_item | New users | 20.0% | 25.1% | -5.2 | 13,472 |
| view_item to add_to_cart | New users | 17.0% | 25.5% | -8.5 | 4,435 |
| add_to_cart to checkout_start | New users | 36.0% | 43.8% | -7.9 | 696 |
| checkout_start to add_payment_info | New users | 43.9% | 81.6% | -37.7 | 2,255 |
| checkout_start to purchase | New users | 29.8% | 59.7% | -29.9 | 1,788 |
| checkout_start to purchase | No cart tracked | 36.6% | 48.9% | -12.3 | 585 |
| checkout_start to add_payment_info | No cart tracked | 55.2% | 66.0% | -10.8 | 516 |
| checkout_start to add_payment_info | Organic traffic | 56.8% | 63.4% | -6.6 | 224 |
| session_start to view_item | Organic traffic | 21.0% | 21.6% | -0.7 | 807 |

All listed results have adjusted p-values below 0.005. Several underflow to zero, meaning p < 1e-300.

### Stratified checkout outcomes

| User type | Entry type | Checkouts | Payment rate | Purchase rate |
|---|---|---|---|---|
| New | Same-session cart | 3,185 | 48.4% | 35.0% |
| New | No cart tracked | 2,790 | 38.7% | 23.9% |
| Returning | Same-session cart | 2,777 | 83.4% | 62.4% |
| Returning | No cart tracked | 1,976 | 78.3% | 54.6% |
| Returning | Prior-session cart | 379 | 86.0% | 66.5% |

| User type | Device | Checkouts | Payment rate | Purchase rate |
|---|---|---|---|---|
| New | Desktop | 3,439 | 43.4% | 29.3% |
| New | Mobile | 2,402 | 44.5% | 30.7% |
| New | Tablet | 134 | 44.0% | 27.6% |
| Returning | Desktop | 2,953 | 80.9% | 59.0% |
| Returning | Mobile | 2,073 | 82.3% | 60.6% |
| Returning | Tablet | 106 | 87.7% | 63.2% |

### Key findings
1. **New users are the dominant leak, and it is sharpest at payment.** New users reach payment info at 43.9%, against 81.6% for everyone else, a ratio of 0.54. At other steps the ratio ranges from 0.67 to 0.82. Returning users likely benefit from saved accounts, addresses, and payment methods. This makes first-time buyer payment friction the leading hypothesis.
2. **The new-user gap is robust.** It holds within every entry type: among same-session carts, new users purchase at 35.0% against 62.4% for returning users. It also holds on every device, with new-user payment rates between 43.4% and 44.5% against 80.9% to 87.7% for returning users.
3. **The ceiling is large.** If new users converted from checkout to purchase at the rate of the rest, the period would gain about 1,790 purchases, roughly $134K at a $74.70 AOV. This assumes new users could fully match returning users, which is not realistic. Day 6 sizes plausible lift scenarios.
4. **Cart-less checkouts reflect a tracking gap.** The no-cart-tracked share is nearly constant across devices (42.7% to 43.3%) and channels (38.4% to 44.8%). It includes about 2,790 first-ever sessions that reached checkout with no add_to_cart event. Day 4 confirmed that most of these checkouts carry no item data.
5. **No-cart-tracked checkouts convert worse even after controlling for user type.** The gap holds within new users (23.9% vs 35.0%, z ≈ 9.4) and within returning users (54.6% vs 62.4%, z ≈ 5.4). Day 4 shows the gap comes mainly from checkouts that fire without item data.
6. **Device is not a driver.** No device segment ranks among the top 15 leaks. Mobile slightly outperforms desktop for both new and returning users.
7. **Channel effects are statistically significant but practically small.** Organic sessions view products at 21.0% against 21.6%, a 0.7 point gap that is significant only because of the 122K-session sample. The largest actionable channel gap is organic checkout to payment, at 6.6 points.
8. **Obfuscated categories are not actionable.** Segments such as "<Other>" and "(data deleted)" show significant gaps but cannot be targeted. They are excluded from recommendations.

### Implications
- Primary candidate for the experiment: reduce payment-step friction for first-time buyers. The effect is consistent across devices, so the test does not need to be device-specific.
- Secondary action, not an experiment: audit add_to_cart and begin_checkout event coverage on all checkout paths.
- Top-of-funnel gaps for new users (product discovery) are large in volume but less directly actionable from funnel data alone.

---

## Behavior and Path Analysis

### Method
- Time to convert: hours from a user's first observed session to their first purchase.
- To limit right censoring, only users first seen before Jan 1, 2021 are included. This gives every user at least 31 days to convert.
- Sessions to purchase counts all of a user's sessions up to and including the first purchase session.
- Cart abandonment is measured within the session.
- Checkout payload check: the items array on each begin_checkout event was inspected to see whether checkout carried product data.
- Category analysis: item IDs were mapped to product categories from checkout and purchase events, then used to label view and cart events.

### Time to convert

| Metric | Value |
|---|---|
| Users first seen before Jan 1 | 179,085 |
| Users who purchased | 3,598 (2.01%) |
| 25th percentile | 0.3 hours (18 minutes) |
| Median | 2.1 hours |
| 75th percentile | 145 hours (about 6 days) |
| 90th percentile | 537 hours (about 22 days) |

### Sessions to first purchase

| Sessions | Buyers | Share |
|---|---|---|
| 1 | 1,635 | 45.4% |
| 2 | 722 | 20.1% |
| 3 | 485 | 13.5% |
| 4 or more | 756 | 21.0% |

### Cart abandonment by device (same session)

| Device | Cart sessions | Purchased | Abandonment |
|---|---|---|---|
| Desktop | 8,790 | 1,606 | 81.7% |
| Mobile | 6,077 | 1,180 | 80.6% |
| Tablet | 321 | 62 | 80.7% |
| Overall | 15,188 | 2,848 | 81.2% |

### Checkout item data by entry type

| Entry type | Checkout carried items | Sessions | Share of entry type | Payment rate | Purchase rate |
|---|---|---|---|---|---|
| Same-session cart | Yes | 5,688 | 95.4% | 65.2% | 48.3% |
| Same-session cart | No | 273 | 4.6% | 54.2% | 36.6% |
| No cart tracked | Yes | 1,814 | 38.1% | 65.7% | 44.6% |
| No cart tracked | No | 2,952 | 61.9% | 48.7% | 31.7% |
| Prior-session cart | Yes | 357 | 94.2% | 86.0% | 66.4% |
| Prior-session cart | No | 22 | 5.8% | 86.4% | 68.2% |

### Purchase revenue by product category

| Category | Share of purchase revenue |
|---|---|
| Apparel | 48.5% |
| New | 7.2% |
| Bags | 6.6% |
| Campus Collection | 5.7% |
| Accessories | 5.0% |
| Shop by Brand | 4.8% |
| Drinkware | 4.4% |
| Lifestyle | 3.9% |
| All other categories | 13.9% |

### Key findings
1. **Buyers split into two groups: fast buyers and considered buyers.** Half of buyers purchase within 2.1 hours of their first visit, and a quarter within 18 minutes. Another quarter take 6 days or more, and 10% take over 3 weeks.
2. **Most buyers need more than one visit.** 54.6% of buyers purchase on their second session or later, and 21.0% need four or more. Single-session conversion therefore understates purchase intent across the whole user base.
3. **Later-visit recovery is small for new-user checkout abandoners.** Multi-session buying could mean the Day 3 new-user gap overstates lost purchases. Day 6 measured this directly: only 4.65% of new-user checkout abandoners purchase in a later session. For this segment, the session-level gap is close to the true loss.
4. **Cart abandonment is high and uniform across devices.** 81.2% of cart sessions end without a purchase in the same session, ranging only from 80.6% to 81.7% across devices.
5. **Cart-less checkouts are a tracking gap on a specific checkout path.** 61.9% of no-cart-tracked checkouts fired begin_checkout with no item data, against 4.6% for same-session carts. These sessions still purchase at 31.7%, so the cart existed but the event did not send its contents. One plausible cause is signed-in users whose cart is stored in their account and loaded at checkout.
6. **The no-payload path, not missing cart tracking, drives the conversion gap.** No-cart-tracked checkouts that carried items convert at 44.6%, close to the 48.3% of same-session carts. Checkouts without item data convert at 31.7% to 36.6% regardless of entry type.
7. **Apparel drives almost half of revenue.** Apparel accounts for 48.5% of purchase revenue. No other category exceeds 7.2%.
8. **A category-level funnel is not possible with this dataset.** View and cart events use different item IDs and category labels than checkout and purchase events. After mapping by item ID, 97.6% of cart rows had no match, and mapped categories showed more purchases than carts. Category results are limited to purchase-side revenue mix.

### Implications
- Experiment metrics should be user-level, such as purchase within 7 days of first exposure. Session metrics would reward shifting purchases between visits without increasing total purchases.
- Re-engagement is a real lever for the overall user base. With 54.6% of buyers returning before they buy, cart-reminder or saved-cart features target a large group.
- Tracking fix: the checkout path that fires begin_checkout without item data affects about 3,250 checkout sessions (29% of all begin_checkout sessions). Identify the page or button behind it before trusting cart and checkout metrics.

### Limitations
- user_pseudo_id is browser-level. Users who switch devices appear as separate users, which inflates single-session buyers and understates sessions to purchase.
- Users first seen in late December had the shortest observation window, so the long tail of time to convert is slightly truncated.
- Item identifiers are not consistent across event types in the obfuscated dataset, which prevents item- or category-level funnel analysis.

---

## Metric Movement Diagnosis

### Weekly trend (full Monday to Sunday weeks only)

| Week starting | Sessions | Purchases | Conversion | Revenue | AOV |
|---|---|---|---|---|---|
| Nov 2 | 24,991 | 249 | 1.00% | $21,820 | $87.63 |
| Nov 9 | 22,508 | 341 | 1.52% | $23,694 | $69.48 |
| Nov 16 | 25,914 | 374 | 1.44% | $38,086 | $101.83 |
| Nov 23 | 27,780 | 515 | 1.85% | $47,973 | $93.15 |
| Nov 30 | 31,088 | 590 | 1.90% | $43,042 | $72.95 |
| Dec 7 | 38,729 | 772 | 1.99% | $59,721 | $77.36 |
| Dec 14 | 33,411 | 549 | 1.64% | $47,276 | $86.11 |
| Dec 21 | 22,083 | 233 | 1.06% | $14,716 | $63.16 |
| Dec 28 | 20,444 | 138 | 0.68% | $10,368 | $75.13 |
| Jan 4 | 29,029 | 162 | 0.56% | $9,402 | $58.04 |
| Jan 11 | 27,707 | 227 | 0.82% | $13,150 | $57.93 |
| Jan 18 | 27,478 | 375 | 1.36% | $26,966 | $71.91 |
| Jan 25 | 26,342 | 310 | 1.18% | $5,178 | $16.70 (suspect) |

### Root cause: the largest week-over-week drop

**1. What happened**
Session conversion fell from 1.64% in the week of Dec 14 to 1.06% in the week of Dec 21. That is a drop of 0.59 points, or 36% relative. Purchases fell 58% (549 to 233) on 34% fewer sessions. Revenue fell 69% ($47,276 to $14,716), because AOV also dropped from $86 to $63.

**2. Is it real**
- Both are full Monday to Sunday weeks. The partial first week was excluded.
- The drop is statistically significant (two-proportion z ≈ 5.8).
- It is not a tracking outage. Sessions and purchases kept being recorded, and the decline continued gradually for two more weeks before recovering in mid-January.
- The drop appears on every device and every traffic channel. A tracking failure would typically hit one platform or path.

**3. Context**
- Dec 14 to 20 is the last full shopping week before Christmas. Dec 21 to 27 contains Christmas Eve and Christmas Day.
- Standard ground shipping cutoffs for Christmas delivery generally fall in mid-December. Gift buyers who missed them had little reason to order merchandise.
- Conversion peaked in the week of Dec 7 (1.99%) and bottomed in the week of Jan 4 (0.56%), recovering to 1.36% by the week of Jan 18.

**4. Where**
- By funnel step, the entire drop happened before checkout:

| Step | Week of Dec 14 | Week of Dec 21 | Relative change |
|---|---|---|---|
| Session to product view | 21.2% | 18.6% | -12.1% |
| View to cart | 29.5% | 23.9% | -19.1% |
| Cart to checkout | 35.8% | 30.7% | -14.4% |
| Checkout to payment | 73.9% | 74.0% | +0.2% |
| Payment to purchase | 73.1% | 75.7% | +3.5% |
| Checkout to purchase | 54.0% | 56.0% | +3.7% |

- View to cart had the largest relative decline (-19%). The three pre-checkout declines compound to roughly the full 36% drop in session conversion.
- Checkout performance held steady or improved. Shoppers who reached checkout completed it at the usual rate.
- By device, desktop explains 64% of the drop (1.60% to 0.94%, down 41%) and mobile explains 37% (1.75% to 1.19%, down 32%). Tablet moved slightly up on a small base.
- By channel, organic explains 34% (1.40% to 0.82%), direct "(none)" 24%, and referral 20%. Every channel declined.
- By user type, returning users explain 68% of the drop and new users 31%.

**5. Why: mix vs rate**

| Decomposition | Rate effect | Mix effect | Interaction | Total |
|---|---|---|---|---|
| Device | -0.59 pts | 0.00 pts | 0.00 pts | -0.59 pts |
| Traffic medium | -0.56 pts | -0.03 pts | +0.01 pts | -0.59 pts |
| User type | -0.47 pts | -0.15 pts | +0.03 pts | -0.59 pts |

- The drop is mostly a rate effect. Every segment converted worse, rather than traffic shifting toward weaker segments.
- The one meaningful mix effect is user type. The returning-user share fell from 26.7% to 22.0%. Returning users convert about five times better than new users (4.06% vs 0.76% in the week of Dec 14), so losing them explains about a quarter of the drop (-0.15 points).
- Within each group, conversion also fell: returning users from 4.06% to 3.10%, new users from 0.76% to 0.48%.

**6. So what**
- This is expected holiday seasonality, not a product or tracking problem. No product fix is needed.
- Three pieces of evidence support this. First, the decline is a broad rate effect across every device and channel. Second, it is concentrated in browsing and carting intent, while checkout completion held steady. Third, it recovers gradually through mid-January. A checkout bug or tracking failure would show up inside the checkout steps or on a single platform.
- Loyal repeat buyers finished their gift shopping first, which explains the smaller returning-user share in the week of Dec 21.
- Implications for the business:
  - Do not run or evaluate experiments between mid-December and mid-January. Results from this window would not generalize.
  - Compare late-December performance with the same weeks of the previous year, not with early December.
  - A possible opportunity to test next season: promoting expedited shipping, gift cards, or digital items after the ground shipping cutoff, since the drop is in purchase intent rather than checkout ability.

### Contrast with the Day 3 leak
The Day 3 leak is new users stalling inside checkout at the payment step. That is a friction problem a product change can address. The Day 5 drop is all users stalling before checkout. That is a demand problem tied to the calendar.

### Data quality flag
The week of Jan 25 shows 310 purchases but only $5,178 in revenue, an AOV of $16.70 against $58 to $102 in every other week. This is likely missing or obfuscated revenue values, not real behavior. This week is excluded from revenue trend conclusions.

---

## Opportunity Sizing and Experiment Design

### Target
New users at checkout to payment info. Baseline step conversion is 43.9% across 5,975 checkout sessions over 92 days.

### Inputs

| Input | Value |
|---|---|
| Purchase rate after reaching payment info | 67.86% |
| Abandoned new-user checkout sessions | 4,195 |
| Share of abandoners who purchase in a later session | 4.65% |
| AOV, new buyers (excluding suspect final week) | $71.49 |
| AOV, all buyers (excluding suspect final week) | $78.67 |
| Eligible new users for the primary metric | 5,737 |
| Baseline 7-day purchase rate after first reaching checkout | 31.79% |
| Daily eligible users, non-holiday | about 92 |

### Opportunity sizing (net of later-session recapture)

| Payment step lift | New step rate | Net extra purchases (92 days) | Net extra revenue (92 days) | Per 30 days |
|---|---|---|---|---|
| 5% | 46.1% | 85 | $6,067 | $1,978 |
| 10% | 48.3% | 170 | $12,133 | $3,956 |
| 20% | 52.7% | 339 | $24,266 | $7,913 |

### Power analysis (alpha 0.05, power 0.80, two-sided)

**Primary metric: user-level 7-day purchase**

| Relative MDE | Target rate | Users per arm | Enrollment needed |
|---|---|---|---|
| 5% | 33.4% | 13,645 | 43 weeks |
| 10% | 35.0% | 3,452 | 11 weeks |
| 15% | 36.6% | 1,551 | 5 weeks |

**Secondary metric: session-level checkout to payment**

| Relative MDE | Target rate | Sessions per arm | Enrollment needed |
|---|---|---|---|
| 5% | 46.1% | 8,063 | 28 weeks |
| 10% | 48.3% | 2,023 | 7 weeks |
| 20% | 52.7% | 508 | 2 weeks |

### Key findings
1. **Recapture is small.** Only 4.65% of new-user checkout abandoners buy later, so improving the payment step produces mostly incremental purchases.
2. **Payment-step lifts carry through to the primary metric.** About 94% of new users who buy within 7 days of reaching checkout buy in that same session. A lift at the payment step translates almost one-for-one into the user-level metric.
3. **Traffic limits the detectable effect.** At about 92 eligible users per day, detecting a 5% lift would take 43 weeks. The test is powered for a 15% relative lift, which needs 5 weeks of enrollment plus 7 days of follow-up.
4. **The realistic opportunity is far below the Day 3 ceiling.** A 10% to 20% payment-step lift yields $12K to $24K in net revenue per 92 days, against the $134K ceiling that assumed new users could fully match returning users.

### Caveats
- The 92-day period includes the holiday peak, so per-30-day figures may overstate a typical month.
- Sizing assumes the payment-to-purchase rate stays constant under treatment.
- Estimates exclude implementation cost and payment processing fees.

The full test design, guardrails, and decision rules are in [experiment_proposal.md](experiment_proposal.md).