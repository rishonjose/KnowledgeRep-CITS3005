#Written by Henri Scaffidi, with modifications by Tim.
#Requires: pip install requests.

import requests, json, os
from tqdm import tqdm

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Add token to environment
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

#modify this to be a set of related repositories.
REPOS = [
    "codersforcauses/guild-volunteering",
    "cmdr2/github-actions-wizard",
]

OUTPUT_FILES = {
    "repos": "./data/repos.json",
    "branches": "./data/branches.json",
    "commits": "./data/commits.json",
    "users": "./data/users.json",
    "files": "./data/files.json"
}

# -----------------------------
# Fetch helpers
# -----------------------------
def fetch_json(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json(), r.headers
    return None, {}

def fetch_repo(full_name):
    data, _ = fetch_json(f"https://api.github.com/repos/{full_name}")
    return data

def fetch_branches(full_name):
    data, _ = fetch_json(f"https://api.github.com/repos/{full_name}/branches")
    return data or []

def fetch_commit_detail(full_name, sha):
    data, _ = fetch_json(f"https://api.github.com/repos/{full_name}/commits/{sha}")
    return data or {}

def count_commits(full_name, branch):
    """Estimate commit count using Link header on per_page=1"""
    url = f"https://api.github.com/repos/{full_name}/commits?sha={branch}&per_page=1"
    _, headers = fetch_json(url)
    if "Link" in headers:
        # Example: <https://api.github.com/...&page=500>; rel="last"
        links = headers["Link"].split(",")
        for link in links:
            if 'rel="last"' in link:
                last_url = link.split(";")[0].strip("<> ")
                last_page = int(last_url.split("page=")[-1])
                return last_page
    return None  # fallback if missing

def fetch_all_commits(full_name, branch):
    """Fetch all commits for a branch, 100 per page"""
    all_commits = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{full_name}/commits?sha={branch}&per_page=100&page={page}"
        commits, _ = fetch_json(url)
        if not commits:
            break
        all_commits.extend(commits)
        page += 1
    return all_commits

# -----------------------------
# Main
# -----------------------------
'''def main():
    repos_out, branches_out, commits_out, users_out, files_out = [], [], [], [], []
    seen_users = set()

    for repo_name in REPOS:
        repo = fetch_repo(repo_name)
        if not repo:
            continue

        repo_id = repo["id"]
        default_branch = repo.get("default_branch", "main")

        # Check commit count on default branch
        # commit_count = count_commits(repo_name, default_branch)
        # if commit_count and commit_count > 500:
        #     print(f"Skipping {repo_name}: {commit_count} commits")
        #     continue

        print(f"Processing {repo_name}")

        repos_out.append({
            "repo_id": repo_id,
            "repo_name": repo["full_name"],
            "repo_description": repo.get("description", ""),
            "repo_language": repo.get("language", ""),
            "repo_stars": repo.get("stargazers_count", 0),
            "repo_forks": repo.get("forks_count", 0),
            "repo_url": repo["html_url"]
        })

        branches = fetch_branches(repo_name)
        for br in branches:
            branch_name = br["name"]
            is_default = branch_name == default_branch
            branches_out.append({
                "repo_id": repo_id,
                "branch_name": branch_name,
                "commit_sha": br["commit"]["sha"],
                "is_default": is_default
            })

            commits = fetch_all_commits(repo_name, branch_name)
            for cm in commits:
                sha = cm["sha"]
                commit_info = cm["commit"]
                author = cm.get("author") or {}
                committer = cm.get("committer") or {}

                cm_detail = fetch_commit_detail(repo_name, sha) or {}
                parents = [p["sha"] for p in cm_detail.get("parents", [])]
                files = cm_detail.get("files", [])

                is_initial = len(parents) == 0
                commits_out.append({
                    "repo_id": repo_id,
                    "branch_name": branch_name,
                    "commit_sha": sha,
                    "commit_message": commit_info["message"],
                    "commit_date": commit_info["author"]["date"],
                    "commit_author_login": author.get("login", ""),
                    "commit_committer_login": committer.get("login", ""),
                    "commit_parent_count": len(parents),
                    "commit_parents": parents,
                    "is_initial": is_initial
                })

                for f in files:
                    files_out.append({
                        "repo_id": repo_id,
                        "commit_sha": sha,
                        "file_name": f["filename"],
                        "file_status": f.get("status", ""),
                        "file_additions": f.get("additions", 0),
                        "file_deletions": f.get("deletions", 0),
                        "file_changes": f.get("changes", 0)
                    })

                for u in (author, committer):
                    if u and u.get("login"):
                        key = (u["login"], repo_id)
                        if key not in seen_users:
                            users_out.append({
                                "user_login": u["login"],
                                "repo_id": repo_id,
                                "user_id": u.get("id", ""),
                                "user_url": u.get("html_url", "")
                            })
                            seen_users.add(key)

    # Save JSONs
    def save_json(fname, rows):
        if rows:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
            print(f"{fname}: {len(rows)} records")

    if not os.path.exists("data"):
        os.makedirs("data")

    save_json(OUTPUT_FILES["repos"], repos_out)
    save_json(OUTPUT_FILES["branches"], branches_out)
    save_json(OUTPUT_FILES["commits"], commits_out)
    save_json(OUTPUT_FILES["users"], users_out)
    save_json(OUTPUT_FILES["files"], files_out)
'''

from tqdm import tqdm

def main():
    repos_out, branches_out, commits_out, users_out, files_out = [], [], [], [], []
    seen_users = set()

    for repo_name in tqdm(REPOS, desc="Processing repositories"):
        repo = fetch_repo(repo_name)
        if not repo:
            continue
        repo_id = repo["id"]
        default_branch = repo.get("default_branch", "main")

        repos_out.append({
            "repo_id": repo_id,
            "repo_name": repo["full_name"],
            "repo_description": repo.get("description", ""),
            "repo_language": repo.get("language", ""),
            "repo_stars": repo.get("stargazers_count", 0),
            "repo_forks": repo.get("forks_count", 0),
            "repo_url": repo["html_url"]
        })

        branches = fetch_branches(repo_name)
        for br in tqdm(branches, desc=f"Branches in {repo_name}", leave=False):
            branch_name = br["name"]
            is_default = branch_name == default_branch
            branches_out.append({
                "repo_id": repo_id,
                "branch_name": branch_name,
                "commit_sha": br["commit"]["sha"],
                "is_default": is_default
            })

            commits = fetch_all_commits(repo_name, branch_name)
            for cm in tqdm(commits, desc=f"Commits in {branch_name}", leave=False):
                sha = cm["sha"]
                commit_info = cm["commit"]
                author = cm.get("author") or {}
                committer = cm.get("committer") or {}
                cm_detail = fetch_commit_detail(repo_name, sha) or {}
                parents = [p["sha"] for p in cm_detail.get("parents", [])]
                files = cm_detail.get("files", [])
                is_initial = len(parents) == 0

                commits_out.append({
                    "repo_id": repo_id,
                    "branch_name": branch_name,
                    "commit_sha": sha,
                    "commit_message": commit_info["message"],
                    "commit_date": commit_info["author"]["date"],
                    "commit_author_login": author.get("login", ""),
                    "commit_committer_login": committer.get("login", ""),
                    "commit_parent_count": len(parents),
                    "commit_parents": parents,
                    "is_initial": is_initial
                })

                for f in files:
                    files_out.append({
                        "repo_id": repo_id,
                        "commit_sha": sha,
                        "file_name": f["filename"],
                        "file_status": f.get("status", ""),
                        "file_additions": f.get("additions", 0),
                        "file_deletions": f.get("deletions", 0),
                        "file_changes": f.get("changes", 0)
                    })

                for u in (author, committer):
                    if u and u.get("login"):
                        key = (u["login"], repo_id)
                        if key not in seen_users:
                            users_out.append({
                                "user_login": u["login"],
                                "repo_id": repo_id,
                                "user_id": u.get("id", ""),
                                "user_url": u.get("html_url", "")
                            })
                            seen_users.add(key)

    # Save JSONs
    def save_json(fname, rows):
        if rows:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
            print(f"{fname}: {len(rows)} records")
    if not os.path.exists("data"):
        os.makedirs("data")
    save_json(OUTPUT_FILES["repos"], repos_out)
    save_json(OUTPUT_FILES["branches"], branches_out)
    save_json(OUTPUT_FILES["commits"], commits_out)
    save_json(OUTPUT_FILES["users"], users_out)
    save_json(OUTPUT_FILES["files"], files_out)
    
if __name__ == "__main__":
    main()
