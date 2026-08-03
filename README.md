# Account Connected Components

Standalone scripts for generating the `account_connected_components.html` report from exported production account-access data.

Extracted from Codex thread `019e4062-53bc-7a71-bde4-23620b63dda9`.

## Layout

- `scripts/access_graph_components_active_only.py` builds connected components from account/user access edges.
- `scripts/enrich_account_components_with_label_counts.py` enriches components with synced ad and label-count data, then writes the HTML report.
- `resources/account_connected_components.html` is the historical generated HTML copied from `~/Downloads`.
- `sql/export_account_access_inputs.sql` exports the two account-access CSV inputs from Postgres.
- `data/` is where input CSV exports should be placed.
- `outputs/` is where generated CSV, JSON, SQL, and HTML files are written.

## Required Inputs

Place these files in `data/`:

- `org_auth_accounts_non_merged_non_demo.csv`
- `org_auth_user_account_edges_non_internal.csv`
- `account_ai_label_account_counts_last_30d.csv`

The original production export scripts were temp artifacts and are no longer present. The scripts expect these CSV shapes from the original run:

- accounts CSV: `account_id`, `ad_account_name` or `name`, `platform`
- edges CSV: `account_id`, `user_id`, `user_email`, `status`
- counts CSV: `account_id` plus the numeric fields listed in `scripts/enrich_account_components_with_label_counts.py`

The first two CSVs can be regenerated with:

```bash
psql "$PROD_DATABASE_DSN" -P pager=off -f sql/export_account_access_inputs.sql
```

The `account_ai_label_account_counts_last_30d.csv` export query was not fully preserved in the raw temp transcript and must be supplied separately.

## Rules

The graph is `Account <- UserAccount -> User` with `ACTIVE` edges only.

Excluded bridge emails:

- `developers@getcrux.ai`
- `prabhatnov158@gmail.com`
- `getcrux.zyra@gmail.com`
- `abhay.chauhan@getcrux.ai`
- `nichollsblaine@gmail.com`
- `himank@getcrux.ai`
- `rishabh.ranjan@getcrux.ai`
- `manik.bhagat@getcrux.ai`
- `manikdevbhagat@gmail.com`
- `pranav.anurag@getcrux.ai`

There is also a Cloaked-specific rule: Gmail user edges are ignored only when the account name contains `Cloaked`.

## Run

From this repo:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/access_graph_components_active_only.py
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/enrich_account_components_with_label_counts.py
```

The final report is written to:

```text
outputs/account_connected_components.html
```
