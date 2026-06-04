-- Read-only production export commands used as inputs for the component builder.
-- Run from psql with \copy so CSVs are written on the local machine.
--
-- Expected destination from this standalone repo:
--   data/org_auth_accounts_non_merged_non_demo.csv
--   data/org_auth_user_account_edges_non_internal.csv
--
-- Example:
--   psql "$PROD_DATABASE_URL_OR_DSN" -P pager=off -f sql/export_account_access_inputs.sql

\copy (
  SELECT
    a.id AS account_id,
    a.ad_account_name,
    a.platform,
    a.ad_account_type,
    a.is_demo,
    a.creation_time_stamp
  FROM organization_auth_account a
  WHERE COALESCE(a.ad_account_type, '') <> 'MERGED'
    AND COALESCE(a.is_demo, false) = false
  ORDER BY a.id
) TO 'data/org_auth_accounts_non_merged_non_demo.csv' WITH CSV HEADER

\copy (
  SELECT
    ua.account_id,
    ua.user_id,
    lower(u.user_email) AS user_email,
    ua.status
  FROM organization_auth_user_account ua
  JOIN organization_auth_user u ON u.user_id = ua.user_id
  WHERE lower(u.user_email) NOT IN (
    'developers@getcrux.ai',
    lower('PrabhatNOV158@gmail.com')
  )
  ORDER BY ua.account_id, ua.user_id
) TO 'data/org_auth_user_account_edges_non_internal.csv' WITH CSV HEADER
