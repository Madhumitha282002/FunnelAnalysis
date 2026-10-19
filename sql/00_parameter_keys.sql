SELECT
  param.key AS param_key,
  COUNT(*) AS occurrences
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(event_params) AS param
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY param_key
ORDER BY occurrences DESC;
