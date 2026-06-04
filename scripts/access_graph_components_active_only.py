import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "outputs"

ACCOUNTS_CSV = DATA_DIR / "org_auth_accounts_non_merged_non_demo.csv"
EDGES_CSV = DATA_DIR / "org_auth_user_account_edges_non_internal.csv"

ACCESS_STATUSES = {"ACTIVE"}
EXCLUDED_EMAILS = {
    "developers@getcrux.ai",
    "prabhatnov158@gmail.com",
    "getcrux.zyra@gmail.com",
    "abhay.chauhan@getcrux.ai",
    "nichollsblaine@gmail.com",
    "himank@getcrux.ai",
}


class DSU:
    def __init__(self, values):
        self.parent = {value: value for value in values}
        self.size = {value: 1 for value in values}

    def find(self, value):
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left, right):
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.size[left_root] < self.size[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        self.size[left_root] += self.size[right_root]


def load_accounts():
    with ACCOUNTS_CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))
    accounts = {row["account_id"]: row for row in rows}
    for row in accounts.values():
        row["ad_account_name"] = row.get("ad_account_name") or row.get("name") or ""
    return accounts


def load_edges(accounts):
    edges_by_user = defaultdict(list)
    edges_by_account = defaultdict(list)
    with EDGES_CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            account_id = row["account_id"]
            if account_id not in accounts:
                continue
            if row["status"] not in ACCESS_STATUSES:
                continue
            email = (row.get("user_email") or "").lower()
            if email in EXCLUDED_EMAILS:
                continue
            account_name = accounts[account_id]["ad_account_name"]
            if "cloaked" in account_name.lower() and email.endswith("@gmail.com"):
                continue
            row["user_email"] = email
            edges_by_user[row["user_id"]].append(row)
            edges_by_account[account_id].append(row)
    return edges_by_user, edges_by_account


def build_components(accounts, edges_by_user, edges_by_account):
    participating_accounts = sorted(edges_by_account)
    dsu = DSU(participating_accounts)
    for user_edges in edges_by_user.values():
        account_ids = sorted({edge["account_id"] for edge in user_edges})
        for account_id in account_ids[1:]:
            dsu.union(account_ids[0], account_id)

    grouped = defaultdict(list)
    for account_id in participating_accounts:
        grouped[dsu.find(account_id)].append(account_id)

    raw_components = []
    for account_ids in grouped.values():
        account_ids = sorted(account_ids)
        users = {}
        edge_count = 0
        statuses = Counter()
        platforms = Counter()
        for account_id in account_ids:
            account = accounts[account_id]
            platforms[account.get("platform", "")] += 1
            for edge in edges_by_account[account_id]:
                edge_count += 1
                statuses[edge.get("status", "")] += 1
                users[edge["user_id"]] = edge["user_email"]

        emails = sorted(set(users.values()))
        domains = sorted({email.split("@", 1)[1] for email in emails if "@" in email})
        account_names = sorted(
            {accounts[account_id]["ad_account_name"] for account_id in account_ids if accounts[account_id]["ad_account_name"]}
        )
        raw_components.append(
            {
                "root_account_id": account_ids[0],
                "account_ids": account_ids,
                "account_count": len(account_ids),
                "user_count": len(users),
                "edge_count": edge_count,
                "email_domains": domains,
                "user_emails": emails,
                "sample_user_emails": emails if domains == ["gmail.com"] else emails[:20],
                "platforms": sorted(k for k in platforms if k),
                "statuses": sorted(k for k in statuses if k),
                "sample_account_names": account_names[:20],
            }
        )

    raw_components.sort(key=lambda row: (-row["account_count"], row["root_account_id"]))
    for index, row in enumerate(raw_components, start=1):
        row["component_rank"] = index
        row["component_id"] = f"component_{index:04d}"
    return raw_components


def write_csv(rows):
    path = OUT_DIR / "participating_non_demo_active_only_component_domains.csv"
    fields = [
        "component_rank",
        "component_id",
        "root_account_id",
        "account_count",
        "user_count",
        "edge_count",
        "unique_email_domain_count",
        "email_domains",
        "sample_user_emails",
        "platforms",
        "statuses",
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
                    "unique_email_domain_count": len(row["email_domains"]),
                    "email_domains": " | ".join(row["email_domains"]),
                    "sample_user_emails": " | ".join(row["sample_user_emails"]),
                    "platforms": " | ".join(row["platforms"]),
                    "statuses": " | ".join(row["statuses"]),
                    "sample_account_names": " | ".join(row["sample_account_names"]),
                }
            )
    return path


def write_html(rows):
    path = OUT_DIR / "participating_non_demo_active_only_component_domains.html"
    table_rows = "\n".join(
        f"""
        <tr>
          <td>{row['component_rank']}</td>
          <td>{html.escape(row['component_id'])}</td>
          <td>{row['account_count']}</td>
          <td>{row['user_count']}</td>
          <td>{row['edge_count']}</td>
          <td>{html.escape(', '.join(row['email_domains']))}</td>
          <td>{html.escape(', '.join(row['sample_user_emails']))}</td>
          <td>{html.escape(', '.join(row['sample_account_names']))}</td>
        </tr>"""
        for row in rows
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
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d6dde5; padding: 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #f3f6f9; text-align: left; position: sticky; top: 0; }}
    td:nth-child(3), td:nth-child(4), td:nth-child(5) {{ text-align: right; white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>Participating Non-Demo Account Components - Active Only</h1>
  <p class="muted">Generated from <code>Account <- UserAccount -> User</code>, excluding configured internal/broad bridge users.</p>
  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>Component</th>
        <th>Accounts</th>
        <th>Users</th>
        <th>Edges</th>
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    accounts = load_accounts()
    edges_by_user, edges_by_account = load_edges(accounts)
    rows = build_components(accounts, edges_by_user, edges_by_account)

    full_json = OUT_DIR / "participating_non_demo_active_only_components_full.json"
    full_json.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    csv_path = write_csv(rows)
    html_path = write_html(rows)

    print(
        json.dumps(
            {
                "components": len(rows),
                "largest_component_accounts": rows[0]["account_count"] if rows else 0,
                "non_merged_non_demo_accounts": len(accounts),
                "participating_accounts": sum(row["account_count"] for row in rows),
                "qualifying_edges": sum(row["edge_count"] for row in rows),
                "singleton_components": sum(1 for row in rows if row["account_count"] == 1),
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(csv_path)
    print(full_json)
    print(html_path)


if __name__ == "__main__":
    main()
