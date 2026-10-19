## Day 4: Behavior and Path Analysis

### Method
- Time to convert: hours from a user's first observed session to their first purchase.
- To limit right censoring, only users first seen before Jan 1, 2021 are included. This gives every user at least 31 days to convert.
- Sessions to purchase counts all of a user's sessions up to and including the first purchase session.
- Cart abandonment is measured within the session.
- Empty-cart check: the items array on each begin_checkout event was inspected to see whether checkout carried product data.
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
2. **Most buyers need more than one visit.** 54.6% of buyers purchase on their second session or later, and 21.0% need four or more. Single-session conversion therefore understates true purchase intent.
3. **The Day 3 new-user gap overstates lost purchases.** Some new users who leave checkout return later and buy as returning users. The session-level comparison counts them as lost, so the true gap is smaller than the 1,790-purchase ceiling estimated on Day 3.
4. **Cart abandonment is high and uniform across devices.** 81.2% of cart sessions end without a purchase in the same session, ranging only from 80.6% to 81.7% across devices. Since most buyers need several visits, some of these carts convert later.
5. **Cart-less checkouts are a tracking gap on a specific checkout path.** 61.9% of no-cart-tracked checkouts fired begin_checkout with no item data, against 4.6% for same-session carts. These sessions still purchase at 31.7%, so the cart existed but the event did not send its contents. One plausible cause is signed-in users whose cart is stored in their account and loaded at checkout.
6. **The no-payload path, not missing cart tracking, drives the Day 3 conversion gap.** No-cart-tracked checkouts that carried items convert at 44.6%, close to the 48.3% of same-session carts. Checkouts without item data convert at 31.7% to 36.6% regardless of entry type. Sessions entering checkout without item data form a distinct, lower-converting path.
7. **Apparel drives almost half of revenue.** Apparel accounts for 48.5% of purchase revenue. No other category exceeds 7.2%.
8. **A category-level funnel is not possible with this dataset.** View and cart events use different item IDs and category labels than checkout and purchase events. After mapping by item ID, 97.6% of cart rows had no match, and mapped categories showed more purchases than carts. Category results are limited to purchase-side revenue mix.

### Implications
- Experiment metrics should be user-level, such as purchase within 7 days of first exposure, not session-level. Session metrics would reward shifting purchases between visits without increasing total purchases.
- Re-engagement is a real lever. With 54.6% of buyers returning before they buy, cart-reminder or saved-cart features target a large group.
- Tracking fix: the checkout path that fires begin_checkout without item data affects about 3,250 checkout sessions (29% of all begin_checkout sessions). Identify the page or button behind it before trusting cart and checkout metrics.
- Day 6 opportunity sizing should discount the Day 3 new-user ceiling to reflect buyers who convert on a later visit.

### Limitations
- user_pseudo_id is browser-level. Users who switch devices appear as separate users, which inflates single-session buyers and understates sessions to purchase.
- Users first seen in late December had the shortest observation window, so the long tail of time to convert is slightly truncated.
- Item identifiers are not consistent across event types in the obfuscated dataset, which prevents item- or category-level funnel analysis.