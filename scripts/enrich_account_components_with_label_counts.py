import csv
import html
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "outputs"

COMPONENTS_JSON = OUT_DIR / "participating_non_demo_active_only_components_full.json"
ACCOUNT_COUNTS_CSV = DATA_DIR / "account_ai_label_account_counts_last_30d.csv"
REPORT_SQL = OUT_DIR / "account_cluster_ai_label_counts_last_30d.sql"
FINAL_HTML = OUT_DIR / "account_connected_components.html"

MIN_SYNCED_AD_COUNT = 100

NUMERIC_FIELDS = [
    "synced_ad_count",
    "synced_asset_level_count",
    "synced_ad_or_asset_count",
    "recent_label_config_count",
    "recent_labeled_ad_or_asset_count",
    "recent_label_ad_pairs",
    "recent_ad_grain_label_ad_pairs",
    "recent_asset_grain_label_asset_pairs",
]


def load_account_counts() -> dict[str, dict[str, int]]:
    with ACCOUNT_COUNTS_CSV.open(newline="") as f:
        rows = csv.DictReader(f)
        return {
            row["account_id"]: {
                field: int(row.get(field) or 0)
                for field in NUMERIC_FIELDS
            }
            for row in rows
        }


def write_summary_csv(rows: list[dict]) -> Path:
    path = OUT_DIR / "participating_non_demo_active_only_component_label_counts_last_30d.csv"
    fields = [
        "component_rank",
        "component_id",
        "root_account_id",
        "account_count",
        "user_count",
        "edge_count",
        "synced_ad_count",
        "synced_asset_level_count",
        "synced_ad_or_asset_count",
        "recent_label_config_count",
        "recent_labeled_ad_or_asset_count",
        "recent_label_ad_pairs",
        "recent_ad_grain_label_ad_pairs",
        "recent_asset_grain_label_asset_pairs",
        "email_domains",
        "sample_user_emails",
        "sample_account_names",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "component_rank": row["component_rank"],
                    "component_id": row["component_id"],
                    "root_account_id": row["root_account_id"],
                    "account_count": row["account_count"],
                    "user_count": row["user_count"],
                    "edge_count": row["edge_count"],
                    "synced_ad_count": row["synced_ad_count"],
                    "synced_asset_level_count": row["synced_asset_level_count"],
                    "synced_ad_or_asset_count": row["synced_ad_or_asset_count"],
                    "recent_label_config_count": row["recent_label_config_count"],
                    "recent_labeled_ad_or_asset_count": row["recent_labeled_ad_or_asset_count"],
                    "recent_label_ad_pairs": row["recent_label_ad_pairs"],
                    "recent_ad_grain_label_ad_pairs": row["recent_ad_grain_label_ad_pairs"],
                    "recent_asset_grain_label_asset_pairs": row["recent_asset_grain_label_asset_pairs"],
                    "email_domains": " | ".join(row["email_domains"]),
                    "sample_user_emails": " | ".join(row["sample_user_emails"]),
                    "sample_account_names": " | ".join(row["sample_account_names"]),
                }
            )
    return path


def write_html(rows: list[dict]) -> Path:
    path = OUT_DIR / "participating_non_demo_active_only_component_domains.html"
    display_rows = [
        row for row in rows
        if row["synced_ad_count"] >= MIN_SYNCED_AD_COUNT
    ]
    display_rows.sort(key=lambda row: (-row["synced_ad_count"], row["component_rank"]))

    table_rows = "\n".join(
        f"""
        <tr>
          <td>{index}</td>
          <td>{html.escape(row['component_id'])}</td>
          <td>{row['account_count']}</td>
          <td>{row['user_count']}</td>
          <td>{row['edge_count']}</td>
          <td>{row['synced_ad_count']:,}</td>
          <td>{row['synced_asset_level_count']:,}</td>
          <td>{html.escape(', '.join(row['email_domains'][:12]))}</td>
          <td>{html.escape(', '.join(row['sample_user_emails']))}</td>
          <td>{html.escape(', '.join(row['sample_account_names']))}</td>
        </tr>"""
        for index, row in enumerate(display_rows, start=1)
    )

    path.write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Participating Non-Demo Account Components - Active Only</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    .muted {{ color: #5c6670; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }}
    .stat {{ border: 1px solid #d6dde5; border-radius: 8px; padding: 12px; background: #f8fafc; }}
    .stat b {{ display: block; font-size: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d6dde5; padding: 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #f3f6f9; text-align: left; position: sticky; top: 0; }}
    td:nth-child(1), td:nth-child(3), td:nth-child(4), td:nth-child(5), td:nth-child(6), td:nth-child(7) {{
      text-align: right;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <h1>Participating Non-Demo Account Components - Active Only</h1>
  <p class="muted">Sorted by synced ads descending. Components with fewer than {MIN_SYNCED_AD_COUNT} synced ads are hidden.</p>
  <div class="stats">
    <div class="stat"><b>{len(display_rows):,}</b><span>components shown</span></div>
    <div class="stat"><b>{sum(row['account_count'] for row in display_rows):,}</b><span>participating accounts</span></div>
    <div class="stat"><b>{sum(row['synced_ad_count'] for row in display_rows):,}</b><span>synced ads</span></div>
    <div class="stat"><b>{sum(row['synced_asset_level_count'] for row in display_rows):,}</b><span>synced asset rows</span></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Rank by ads</th>
        <th>Component</th>
        <th>Accounts</th>
        <th>Users</th>
        <th>Edges</th>
        <th>Synced ads</th>
        <th>Synced asset rows</th>
        <th>Email domains</th>
        <th>User emails</th>
        <th>Sample account names</th>
      </tr>
    </thead>
    <tbody>{table_rows}
    </tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return path


def write_sql(rows: list[dict]) -> Path:
    account_ids = sorted({account_id for row in rows for account_id in row["account_ids"]})
    values = ",\n".join(f"('{account_id}')" for account_id in account_ids)
    REPORT_SQL.write_text(
        f"""-- Account ids present in the active-only non-demo connected-component report.
-- Generated by scripts/enrich_account_components_with_label_counts.py
with selected_account_ids(account_id) as (
  values
{values}
)
select account_id
from selected_account_ids;
""",
        encoding="utf-8",
    )
    return REPORT_SQL


def main():
    rows = json.loads(COMPONENTS_JSON.read_text(encoding="utf-8"))
    account_counts = load_account_counts()
    enriched = []
    for row in rows:
        totals = {field: 0 for field in NUMERIC_FIELDS}
        for account_id in row["account_ids"]:
            counts = account_counts.get(account_id, {})
            for field in NUMERIC_FIELDS:
                totals[field] += counts.get(field, 0)
        new_row = dict(row)
        new_row.update(totals)
        new_row["recent_label_config_count_sum"] = totals["recent_label_config_count"]
        enriched.append(new_row)

    enriched_for_html = [
        row for row in enriched
        if row["synced_ad_count"] >= MIN_SYNCED_AD_COUNT
    ]
    enriched_for_html.sort(key=lambda row: (-row["synced_ad_count"], row["component_rank"]))

    full_json = OUT_DIR / "participating_non_demo_active_only_components_with_label_counts_last_30d.json"
    full_json.write_text(json.dumps(enriched_for_html, indent=2, sort_keys=True), encoding="utf-8")
    summary_csv = write_summary_csv(enriched_for_html)
    html_path = write_html(enriched)
    sql_path = write_sql(enriched_for_html)
    FINAL_HTML.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps({
        "components": len(enriched_for_html),
        "participating_accounts": sum(row["account_count"] for row in enriched_for_html),
        "synced_ad_count": sum(row["synced_ad_count"] for row in enriched_for_html),
        "synced_asset_level_count": sum(row["synced_asset_level_count"] for row in enriched_for_html),
        "recent_labeled_ad_or_asset_count": sum(row["recent_labeled_ad_or_asset_count"] for row in enriched_for_html),
        "recent_label_ad_pairs": sum(row["recent_label_ad_pairs"] for row in enriched_for_html),
    }, indent=2, sort_keys=True))
    print(summary_csv)
    print(full_json)
    print(html_path)
    print(sql_path)
    print(FINAL_HTML)


if __name__ == "__main__":
    main()
