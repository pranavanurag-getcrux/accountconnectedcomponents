import csv
import html
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "outputs"

COMPONENTS_JSON = OUT_DIR / "participating_non_demo_active_only_components_full.json"
ACCOUNTS_CSV = DATA_DIR / "org_auth_accounts_non_merged_non_demo.csv"
ACCOUNT_COUNTS_CSV = DATA_DIR / "account_ai_label_account_counts_last_30d.csv"
REPORT_SQL = OUT_DIR / "account_cluster_ai_label_counts_last_30d.sql"
FINAL_HTML = OUT_DIR / "account_connected_components.html"

MIN_SYNCED_ASSET_COUNT = 100

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


def load_account_metadata() -> dict[str, dict[str, str]]:
    with ACCOUNTS_CSV.open(newline="") as f:
        return {
            row["account_id"]: {
                "account_id": row.get("ad_account_id") or row["account_id"],
                "platform": row.get("platform") or "",
                "account_name": row.get("ad_account_name") or row.get("name") or "",
            }
            for row in csv.DictReader(f)
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
    display_rows = sorted(
        rows,
        key=lambda row: (-row["synced_asset_level_count"], row["component_rank"]),
    )
    max_accounts = max((row["account_count"] for row in display_rows), default=1)
    account_metadata = load_account_metadata()
    download_data = {}

    for index, row in enumerate(display_rows, start=1):
        download_data[str(index)] = [
            account_metadata.get(
                account_id,
                {"account_id": account_id, "platform": "", "account_name": ""},
            )
            for account_id in row["account_ids"]
        ]

    download_json = json.dumps(download_data, sort_keys=True).replace("</", "<\\/")

    table_rows = "\n".join(
        f"""
        <tr data-account-count="{row['account_count']}" data-synced-assets="{row['synced_asset_level_count']}">
          <td>{index}</td>
          <td><button class="bar" type="button" data-rank="{index}" title="Download account IDs, platforms, and names"><span style="width:{max(row['account_count'] / max_accounts * 100, 0.1):.2f}%"></span><b>{row['account_count']}</b></button></td>
          <td>{row['user_count']}</td>
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
    .stats {{ display: grid; grid-template-columns: repeat(3, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }}
    .stat {{ border: 1px solid #d7dde3; border-radius: 6px; padding: 12px; }}
    .stat b {{ display: block; font-size: 24px; margin-bottom: 4px; }}
    .controls {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0 0 14px; }}
    .controls label {{ color: #344054; font-weight: 600; }}
    .controls input {{ width: 96px; border: 1px solid #cfd6de; border-radius: 6px; padding: 7px 9px; font: inherit; }}
    .secondary-action {{ border: 1px solid #2f6fed; border-radius: 6px; background: #fff; color: #1f5fdb; cursor: pointer; font: inherit; font-weight: 600; padding: 8px 12px; }}
    .secondary-action:hover {{ background: #f3f7ff; }}
    .view-note {{ color: #5c6670; }}
    table {{ border-collapse: separate; border-spacing: 0; table-layout: fixed; width: 100%; margin-top: 12px; border: 1px solid #d8dee6; border-radius: 6px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #e2e6ea; border-right: 1px solid #e7ebf0; padding: 11px 12px; text-align: left; vertical-align: top; line-height: 1.35; }}
    th:last-child, td:last-child {{ border-right: 0; }}
    th {{ background: #f5f7f9; font-weight: 700; position: sticky; top: 0; z-index: 1; }}
    tbody tr:nth-child(even) {{ background: #fbfcfd; }}
    tbody tr:hover {{ background: #f6f9ff; }}
    .rank-col {{ width: 56px; }}
    .accounts-col {{ width: 210px; }}
    .users-col {{ width: 74px; }}
    .assets-col {{ width: 120px; }}
    .domains-col {{ width: 190px; }}
    .emails-col {{ width: 28%; }}
    .names-col {{ width: 32%; }}
    .bar {{ display: grid; grid-template-columns: 1fr 64px; gap: 8px; align-items: center; min-width: 180px; border: 0; padding: 0; background: transparent; color: inherit; cursor: pointer; font: inherit; text-align: left; }}
    .bar:hover b {{ text-decoration: underline; }}
    .bar:focus-visible {{ outline: 2px solid #2f6fed; outline-offset: 3px; }}
    .bar span {{ height: 14px; background: #2f6fed; border-radius: 2px; display: block; }}
    .bar b {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
    td:nth-child(4) {{ font-variant-numeric: tabular-nums; }}
    .hidden-row {{ display: none; }}
  </style>
</head>
<body>
  <h1>Customer Account Groups</h1>
  <p class="muted">This report shows groups of advertising accounts that are connected through shared users. Each row is one account group, sorted by the number of synced asset ids. Click the account count to download the account IDs, platform, and account names for that group.</p>
  <div class="stats">
    <div class="stat"><b id="visible-account-count">0</b><span>ad accounts shown</span></div>
    <div class="stat"><b id="visible-group-count">0</b><span>account groups shown</span></div>
    <div class="stat"><b id="visible-synced-asset-count">0</b><span>synced asset ids</span></div>
  </div>
  <div class="controls">
    <label for="min-synced-assets">Minimum synced asset ids</label>
    <input id="min-synced-assets" type="number" min="0" step="1" value="{MIN_SYNCED_ASSET_COUNT}">
    <button class="secondary-action" type="button" id="show-smaller-groups">Show smaller groups</button>
    <span class="view-note" id="view-note"></span>
  </div>
  <table>
    <thead>
      <tr><th class="rank-col">Rank</th><th class="accounts-col">Accounts</th><th class="users-col">Users</th><th class="assets-col">Synced asset ids</th><th class="domains-col">Email domains</th><th class="emails-col">User emails</th><th class="names-col">Sample account names</th></tr>
    </thead>
    <tbody>{table_rows}
    </tbody>
  </table>
  <script id="account-download-data" type="application/json">{download_json}</script>
  <script>
    const accountDownloadData = JSON.parse(document.getElementById("account-download-data").textContent);
    const tableRows = Array.from(document.querySelectorAll("tbody tr"));
    const thresholdInput = document.getElementById("min-synced-assets");
    const showSmallerGroupsButton = document.getElementById("show-smaller-groups");
    const viewNote = document.getElementById("view-note");
    const formatter = new Intl.NumberFormat("en-US");
    const csvEscape = (value) => {{
      const text = String(value ?? "");
      return /[",\\n\\r]/.test(text) ? `"${{text.replaceAll('"', '""')}}"` : text;
    }};
    const updateView = () => {{
      const threshold = Math.max(0, Number(thresholdInput.value) || 0);
      const visibleRows = [];
      tableRows.forEach((row) => {{
        const syncedAssets = Number(row.dataset.syncedAssets);
        const isVisible = syncedAssets >= threshold;
        row.classList.toggle("hidden-row", !isVisible);
        if (isVisible) {{
          visibleRows.push(row);
        }}
      }});
      const totals = visibleRows.reduce((acc, row) => {{
        acc.accounts += Number(row.dataset.accountCount);
        acc.syncedAssets += Number(row.dataset.syncedAssets);
        return acc;
      }}, {{ accounts: 0, syncedAssets: 0 }});
      document.getElementById("visible-account-count").textContent = formatter.format(totals.accounts);
      document.getElementById("visible-group-count").textContent = formatter.format(visibleRows.length);
      document.getElementById("visible-synced-asset-count").textContent = formatter.format(totals.syncedAssets);
      viewNote.textContent = `Showing ${{formatter.format(visibleRows.length)}} of ${{formatter.format(tableRows.length)}} account groups.`;
    }};
    const downloadAccounts = (rank) => {{
      const rows = accountDownloadData[rank] || [];
      const csv = [
        ["account_id", "platform", "account_name"],
        ...rows.map((row) => [row.account_id, row.platform, row.account_name]),
      ].map((row) => row.map(csvEscape).join(",")).join("\\n");
      const blob = new Blob([csv], {{ type: "text/csv;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `account_component_${{String(rank).padStart(4, "0")}}_accounts.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }};
    document.querySelectorAll(".bar[data-rank]").forEach((button) => {{
      button.addEventListener("click", () => downloadAccounts(button.dataset.rank));
    }});
    thresholdInput.addEventListener("input", updateView);
    showSmallerGroupsButton.addEventListener("click", () => {{
      thresholdInput.value = "0";
      updateView();
    }});
    updateView();
  </script>
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
        if row["synced_asset_level_count"] >= MIN_SYNCED_ASSET_COUNT
    ]
    enriched_for_html.sort(
        key=lambda row: (-row["synced_asset_level_count"], row["component_rank"])
    )

    full_json = OUT_DIR / "participating_non_demo_active_only_components_with_label_counts_last_30d.json"
    full_json.write_text(json.dumps(enriched_for_html, indent=2, sort_keys=True), encoding="utf-8")
    summary_csv = write_summary_csv(enriched_for_html)
    html_path = write_html(enriched)
    sql_path = write_sql(enriched_for_html)
    FINAL_HTML.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps({
        "components": len(enriched_for_html),
        "participating_accounts": sum(row["account_count"] for row in enriched_for_html),
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
