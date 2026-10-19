CREATE OR REPLACE TABLE `funnelproject-511023.funnel_project.events_clean` AS
SELECT
  PARSE_DATE('%Y%m%d', event_date) AS event_date,
  TIMESTAMP_MICROS(event_timestamp) AS event_ts,
  event_name,
  user_pseudo_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id,
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_number') AS ga_session_number,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
  device.category AS device_category,
  device.operating_system AS operating_system,
  geo.country AS country,
  traffic_source.source AS traffic_source,
  traffic_source.medium AS traffic_medium,
  ecommerce.transaction_id AS transaction_id,
  ecommerce.purchase_revenue_in_usd AS purchase_revenue_usd,
  CONCAT(
    user_pseudo_id, '-',
    CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
  ) AS session_key
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131';
