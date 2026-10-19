# Findings

## Day 2: Base Funnel

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
3. **Most carts never reach checkout.** Only 39.3% of cart sessions start checkout in the same session. This bridge step loses about 9,200 cart sessions. The earlier unordered figure of 73.1% overstated it, because it counted checkouts that had no cart in the session.
4. **Checkout to payment is the weakest step inside checkout.** 38.7% of checkout sessions (4,294) never add payment information. Payment to purchase is stronger at 71.1%.
5. **Checkouts with no tracked cart convert much worse.** These sessions make up 42.9% of all checkouts but convert at 36.6%, versus 47.8% for same-session carts. That is an 11.2 point gap. If this group converted at the same-session rate, it would add about 530 purchases, roughly $40K, or 11% of period revenue. This is an upper-bound comparison, not a causal estimate, because the groups may differ in intent and device mix.
6. **Returning carts convert best but are rare.** Checkouts with a cart from a prior session convert at 66.5%, but this group is only 379 sessions (3.4%).

### Ordered vs unordered comparison
- The strict ordered funnel captured only 545 purchase sessions, 11% of the 4,848 in the data.
- Most of the loss came from begin_checkout and add_shipping_info. Of 11,104 sessions with both events, 61.8% logged add_shipping_info first, 38.2% logged it after, and none shared a timestamp. Median gap: [median_sec] seconds.
- These two events have no consistent order, so they are merged into a single checkout_start step.
- Only 3 purchase sessions lack a checkout event, so purchase tracking is reliably tied to checkout.

### Open questions for Days 3 and 4
- Is "no cart tracked" concentrated in one device, browser, or channel? If so, that points to a tracking gap rather than user behavior.
- Do users with cart-less checkouts appear on multiple devices, or did they first arrive before Nov 1?
- Which segments drive the cart to checkout and checkout to payment leaks?

### Decision
- Primary analysis uses the two-stage nested funnel, plus the same-session cart to checkout bridge.
- The unordered funnel is kept as an upper bound. The strict ordered funnel is documented as a rejected method.
- Checkout entry type is used as a segment in Day 3 for checkout-stage transitions only, since it is defined by checkout behavior.

### Limitations
- user_pseudo_id identifies a browser or device, not a person. Cross-device journeys look like separate users.
- Carts created before Nov 1, 2020 are invisible, which inflates the "no cart tracked" group.
- Data is obfuscated. Revenue and some categorical values may be altered.
- The window covers the holiday season, so conversion may run higher than a typical quarter.