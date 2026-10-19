## Day 3: Segmented Funnel

### Method
- Each segment was compared against all other sessions at each funnel transition, using Wilson 95% confidence intervals and two-proportion z-tests.
- 129 comparisons were tested. Benjamini-Hochberg correction controlled the false discovery rate at 5%.
- 23 comparisons were significant leaks, meaning the segment converted significantly worse than the rest.
- Leaks were ranked by lost sessions: the conversions the segment would gain at the rest-of-population rate. This is an upper-bound comparison, not a causal estimate.
- Checkout entry type was tested only on checkout transitions, since it is defined by checkout behavior.
- The two largest effects were then checked for confounding with stratified tables by user type, entry type, and device.

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
2. **The new-user gap is robust.** It holds within every entry type: among same-session carts, new users purchase at 35.0% vs 62.4% for returning users. It also holds on every device, with new-user payment rates between 43.4% and 44.5% against 80.9% to 87.7% for returning users. It is not explained by cart behavior or device.
3. **The opportunity is large.** If new users converted from checkout to purchase at the rate of the rest, the period would gain about 1,790 purchases, roughly $134K at a $74.70 AOV. This is a ceiling, since new and returning users differ in intent. Day 6 sizes realistic lift scenarios.
4. **Cart-less checkouts point to an add_to_cart tracking gap.** The no-cart-tracked share is nearly constant across devices (42.7% to 43.3%) and channels (38.4% to 44.8%). It includes about 2,790 first-ever sessions that reached checkout with no add_to_cart event. Since these users have no earlier sessions, an add-to-cart path that does not fire the event is the most likely cause.
5. **No-cart-tracked checkouts convert worse even after controlling for user type.** The gap holds within new users (23.9% vs 35.0%, z ≈ 9.4) and within returning users (54.6% vs 62.4%, z ≈ 5.4). User mix explains only a small part of it. A tracking gap alone would not lower conversion, so part of this group likely reaches checkout with an empty or stale cart. Day 4 tests this.
6. **Device is not a driver.** No device segment ranks among the top 15 leaks. Mobile slightly outperforms desktop for both new and returning users.
7. **Channel effects are statistically significant but practically small.** Organic sessions view products at 21.0% vs 21.6%, a 0.7 point gap that is significant only because of the 122K-session sample. The largest actionable channel gap is organic checkout to payment, at 6.6 points.
8. **Obfuscated categories are not actionable.** Segments such as "<Other>" and "(data deleted)" show significant gaps but cannot be targeted. They are excluded from recommendations.

### Implications
- Primary candidate for the Day 6 experiment: reduce payment-step friction for first-time buyers, for example with express wallet payments or a more prominent guest checkout. The effect is consistent across devices, so the test does not need to be device-specific.
- Secondary action, not an experiment: audit add_to_cart event coverage across all add-to-cart buttons and pages before trusting cart-stage metrics.
- Day 4 follow-up: check whether begin_checkout events in no-cart-tracked sessions contain items, to separate tracking gaps from empty-cart visits.
- Top-of-funnel gaps for new users (product discovery) are large in volume but less directly actionable from funnel data alone.