## Day 5: Metric Movement Diagnosis

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
- It is not a tracking outage. Sessions and purchases kept being recorded, and the decline continued gradually for two more weeks before recovering in mid-January. An outage would show a sudden break and recovery.
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

**6. So what**
- This is expected holiday seasonality, not a product or tracking problem. No product fix is needed.
- Three pieces of evidence support this. First, the decline is a broad rate effect across every device and channel. Second, it is concentrated in browsing and carting intent, while checkout completion held steady. Third, it recovers gradually through mid-January. A checkout bug or tracking failure would show up inside the checkout steps or on a single platform.
- Loyal repeat buyers finished their gift shopping first, which explains the smaller returning-user share in the week of Dec 21.
- Implications for the business:
  - Do not run or evaluate experiments between mid-December and mid-January. Results from this window would not generalize.
  - Compare late-December performance with the same weeks of the previous year, not with early December.
  - A possible opportunity to test next season: promoting expedited shipping, gift cards, or digital items after the ground shipping cutoff, since the drop is in purchase intent rather than checkout ability.