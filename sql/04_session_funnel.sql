CREATE OR REPLACE TABLE `funnelproject-511023.funnel_project.session_funnel` AS
WITH session_events AS (
  SELECT
    session_key,
    user_pseudo_id,
    MIN(event_date) AS session_date,
    MIN(event_ts) AS session_start_ts,
    ANY_VALUE(device_category) AS device_category,
    ANY_VALUE(country) AS country,
    ANY_VALUE(traffic_medium) AS traffic_medium,
    MAX(ga_session_number) AS session_number,
    MIN(IF(event_name = 'view_item', event_ts, NULL)) AS ts_view_item,
    MIN(IF(event_name = 'add_to_cart', event_ts, NULL)) AS ts_add_to_cart,
    MIN(IF(event_name = 'begin_checkout', event_ts, NULL)) AS ts_begin_checkout,
    MIN(IF(event_name = 'add_shipping_info', event_ts, NULL)) AS ts_add_shipping_info,
    MIN(IF(event_name = 'add_payment_info', event_ts, NULL)) AS ts_add_payment_info,
    MIN(IF(event_name = 'purchase', event_ts, NULL)) AS ts_purchase,
    SUM(IF(event_name = 'purchase', IFNULL(purchase_revenue_usd, 0), 0)) AS revenue_usd
  FROM `funnelproject-511023.funnel_project.events_clean`
  WHERE session_key IS NOT NULL
  GROUP BY session_key, user_pseudo_id
)
SELECT
  *,
  CASE
    WHEN session_number IS NULL THEN 'unknown'
    WHEN session_number = 1 THEN 'new'
    ELSE 'returning'
  END AS user_type,

  -- Unordered flags
  ts_view_item IS NOT NULL AS u_view_item,
  ts_add_to_cart IS NOT NULL AS u_add_to_cart,
  ts_begin_checkout IS NOT NULL AS u_begin_checkout,
  ts_add_shipping_info IS NOT NULL AS u_add_shipping_info,
  ts_add_payment_info IS NOT NULL AS u_add_payment_info,
  ts_purchase IS NOT NULL AS u_purchase,

  -- Ordered flags
  ts_view_item IS NOT NULL AS o_view_item,
  IFNULL(ts_add_to_cart >= ts_view_item, FALSE) AS o_add_to_cart,
  IFNULL(ts_add_to_cart >= ts_view_item
     AND ts_begin_checkout >= ts_add_to_cart, FALSE) AS o_begin_checkout,
  IFNULL(ts_add_to_cart >= ts_view_item
     AND ts_begin_checkout >= ts_add_to_cart
     AND ts_add_shipping_info >= ts_begin_checkout, FALSE) AS o_add_shipping_info,
  IFNULL(ts_add_to_cart >= ts_view_item
     AND ts_begin_checkout >= ts_add_to_cart
     AND ts_add_shipping_info >= ts_begin_checkout
     AND ts_add_payment_info >= ts_add_shipping_info, FALSE) AS o_add_payment_info,
  IFNULL(ts_add_to_cart >= ts_view_item
     AND ts_begin_checkout >= ts_add_to_cart
     AND ts_add_shipping_info >= ts_begin_checkout
     AND ts_add_payment_info >= ts_add_shipping_info
     AND ts_purchase >= ts_add_payment_info, FALSE) AS o_purchase
FROM session_events;