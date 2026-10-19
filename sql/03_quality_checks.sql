-- Check 1: rows with no session key
SELECT
  COUNTIF(session_key IS NULL) AS rows_missing_session,
  COUNT(*) AS total_rows,
  ROUND(COUNTIF(session_key IS NULL) / COUNT(*), 4) AS pct_missing
FROM `funnelproject-511023.funnel_project.events_clean`;
 
-- Check 2: exact duplicate events
SELECT COUNT(*) AS duplicate_groups
FROM (
  SELECT user_pseudo_id, event_ts, event_name, COUNT(*) AS n
  FROM `funnelproject-511023.funnel_project.events_clean`
  GROUP BY user_pseudo_id, event_ts, event_name
  HAVING n > 1
);
 
-- Check 3: purchases and transaction IDs
SELECT
  COUNT(*) AS purchase_events,
  COUNT(DISTINCT transaction_id) AS distinct_transactions,
  COUNTIF(transaction_id IS NULL OR transaction_id = '(not set)') AS missing_transaction_id,
  ROUND(SUM(purchase_revenue_usd), 2) AS total_revenue_usd
FROM `funnelproject-511023.funnel_project.events_clean`
WHERE event_name = 'purchase';
 
-- Check 4: purchase sessions that skipped earlier funnel steps
WITH s AS (
  SELECT
    session_key,
    COUNTIF(event_name = 'purchase') > 0 AS has_purchase,
    COUNTIF(event_name = 'add_to_cart') > 0 AS has_cart,
    COUNTIF(event_name = 'begin_checkout') > 0 AS has_checkout
  FROM `funnelproject-511023.funnel_project.events_clean`
  WHERE session_key IS NOT NULL
  GROUP BY session_key
)
SELECT
  COUNTIF(has_purchase) AS purchase_sessions,
  COUNTIF(has_purchase AND NOT has_cart) AS purchase_without_cart,
  COUNTIF(has_purchase AND NOT has_checkout) AS purchase_without_checkout
FROM s;
 
-- Check 5: placeholder values in segment fields
SELECT device_category, traffic_medium, COUNT(*) AS n
FROM `funnelproject-511023.funnel_project.events_clean`
GROUP BY device_category, traffic_medium
ORDER BY n DESC;
