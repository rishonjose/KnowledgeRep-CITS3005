# --------------------------------------------------------
# Git-Onto-Logic Ontology Population Script (with Concurrent Contributor Detection)
# Author: Saayella
# --------------------------------------------------------
import json
from pathlib import Path
from owlready2 import *
from datetime import datetime
from collections import defaultdict

# === Load ontology schema ===
onto = get_ontology("ontology/git-onto-logic-redesigned.owl").load()

# === Add new inferred class ===
with onto:
    class ConcurrentContributor(onto.User): pass

# === Dataset folder path ===
DATA_DIR = Path("data")

# === Helper: load JSON ===
def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === Load dataset files ===
repos    = load_json("repos.json")
branches = load_json("branches.json")
commits  = load_json("commits.json")
users    = load_json("users.json")
files    = load_json("files.json")
issues   = load_json("issues.json")
prs      = load_json("pulls.json")

# === Cache dictionaries ===
repo_map = {}
branch_map = {}
user_map = {}
commit_map = {}

# --------------------------------------------------------
# === Create repository individuals ===
# --------------------------------------------------------
for r in repos:
    repo_iri = f"repo_{r['repo_id']}"
    repo = onto.Repository(repo_iri)
    repo.repoName = [r.get("repo_name", "Unknown")]
    repo.repoLanguage = [r.get("repo_language") or "Unknown"]
    repo.repoStars = [int(r.get("repo_stars", 0))]
    repo.repoForks = [int(r.get("repo_forks", 0))]
    repo_map[r["repo_id"]] = repo

# --------------------------------------------------------
# === Create user individuals ===
# --------------------------------------------------------
for u in users:
    safe_login = u["user_login"].replace("/", "_")
    user = onto.User(f"user_{safe_login}")
    user.userLogin = [u["user_login"]]
    user.userURL = [u.get("user_url", "")]
    user_map[u["user_login"]] = user

# --------------------------------------------------------
# === Create branches and link to repos ===
# --------------------------------------------------------
for b in branches:
    repo_id = b["repo_id"]
    repo = repo_map.get(repo_id)
    if not repo:
        continue

    branch_name = b["branch_name"].replace("/", "_")
    branch_iri = f"repo_{repo_id}__branch_{branch_name}"
    branch = onto.Branch(branch_iri)
    branch.branchName = [b["branch_name"]]
    branch.isDefault = [bool(b.get("is_default", False))]
    branch_map[(repo_id, b["branch_name"])] = branch
    repo.hasBranch.append(branch)

# --------------------------------------------------------
# === Create commits and link ===
# --------------------------------------------------------
for c in commits:
    repo_id = c["repo_id"]
    branch_key = (repo_id, c["branch_name"])
    branch = branch_map.get(branch_key)
    if not branch:
        continue

    safe_sha = c["commit_sha"].replace("/", "_")
    commit_iri = f"commit_{safe_sha}"

    commit = commit_map.get(c["commit_sha"])
    if not commit:
        commit = onto.Commit(commit_iri)
        commit_map[c["commit_sha"]] = commit

    commit.commitSHA = [c["commit_sha"]]
    commit.message = [c.get("commit_message", "")]
    commit.commitDate = [c.get("commit_date", "")]
    commit.isInitial = [bool(c.get("is_initial", False))]

    branch.hasCommit.append(commit)
    commit.onBranch.append(branch)

    author_login = c.get("commit_author_login")
    committer_login = c.get("commit_committer_login")

    if author_login and author_login in user_map:
        commit.authoredBy.append(user_map[author_login])
    if committer_login and committer_login in user_map:
        commit.committedBy.append(user_map[committer_login])

    parents = c.get("commit_parents", [])
    for psha in parents:
        safe_parent_sha = psha.replace("/", "_")
        parent_commit = commit_map.get(psha)
        if not parent_commit:
            parent_commit = onto.Commit(f"commit_{safe_parent_sha}")
            commit_map[psha] = parent_commit
        commit.parent.append(parent_commit)

    msg = c.get("commit_message", "").lower()
    if any(k in msg for k in ["security", "vulnerability"]):
        commit.is_a.append(onto.SecurityCommit)

# --------------------------------------------------------
# === Create files and link to commits ===
# --------------------------------------------------------
for fobj in files:
    commit_sha = fobj["commit_sha"]
    commit = commit_map.get(commit_sha)
    if not commit:
        continue

    safe_file = fobj["file_name"].replace("/", "_").replace(" ", "_")
    file_iri = f"{commit_sha}__{safe_file}"
    file_ind = onto.File(file_iri)
    file_ind.fileName = [fobj["file_name"]]
    file_ind.fileStatus = [fobj.get("file_status", "modified")]
    file_ind.fileChanges = [int(fobj.get("file_changes", 0))]
    commit.updatesFile.append(file_ind)

# --------------------------------------------------------
# === Create issues and link ===
# --------------------------------------------------------
for iobj in issues:
    repo = repo_map.get(iobj["repo_id"])
    if not repo:
        continue

    issue_iri = f"issue_{iobj['issue_id']}"
    issue = onto.Issue(issue_iri)
    issue.title = [iobj.get("title", "Untitled")]
    issue.state = [iobj.get("state", "open")]
    repo.hasIssue.append(issue)

    user_login = iobj.get("user_login")
    if user_login and user_login in user_map:
        issue.openedBy.append(user_map[user_login])

# --------------------------------------------------------
# === Create pull requests and link ===
# --------------------------------------------------------
for pobj in prs:
    repo = repo_map.get(pobj["repo_id"])
    if not repo:
        continue

    pr_iri = f"pr_{pobj['pr_id']}"
    pr = onto.PullRequest(pr_iri)
    pr.title = [pobj.get("title", "Untitled PR")]
    pr.state = [pobj.get("state", "open")]
    pr.mergedAt = [pobj.get("merged_at") or ""]

    repo.hasPullRequest.append(pr)

    user_login = pobj.get("user_login")
    if user_login and user_login in user_map:
        pr.openedBy.append(user_map[user_login])

    base_branch = branch_map.get((pobj["repo_id"], pobj.get("base_branch")))
    head_branch = branch_map.get((pobj["repo_id"], pobj.get("head_branch")))

    if base_branch:
        pr.hasBaseBranch.append(base_branch)
    if head_branch:
        pr.hasHeadBranch.append(head_branch)
        if pobj.get("merged_at"):
            head_branch.mergedInto.append(base_branch)

# --------------------------------------------------------
# === Detect Concurrent Contributors ===
# --------------------------------------------------------
print("🔍 Detecting concurrent contributors...")
user_repo_dates = defaultdict(lambda: defaultdict(list))

for c in commits:
    user = c.get("commit_author_login")
    repo = c.get("repo_id")
    date_str = c.get("commit_date")
    if not (user and repo and date_str):
        continue
    try:
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        continue
    user_repo_dates[user][repo].append(date)

concurrent_users = []

for user, repos in user_repo_dates.items():
    if len(repos) < 3:
        continue
    repo_periods = []
    for repo, dates in repos.items():
        repo_periods.append((min(dates), max(dates)))
    overlaps = 0
    for i, (s1, e1) in enumerate(repo_periods):
        for j, (s2, e2) in enumerate(repo_periods):
            if i >= j: continue
            if s1 <= e2 and s2 <= e1:
                overlaps += 1
    if overlaps >= 3:
        concurrent_users.append(user)

print(f"✅ Found {len(concurrent_users)} concurrent contributors.")

for user_login in concurrent_users:
    if user_login in user_map:
        user_map[user_login].is_a.append(onto.ConcurrentContributor)

# --------------------------------------------------------
# === Manual reasoning (lightweight inference) ===
# --------------------------------------------------------
for c in onto.Commit.instances():
    if len(c.parent) >= 2 and onto.MergeCommit not in c.is_a:
        c.is_a.append(onto.MergeCommit)
    elif len(c.parent) == 0 and onto.InitialCommit not in c.is_a:
        c.is_a.append(onto.InitialCommit)

for b in onto.Branch.instances():
    if not b.mergedInto:
        b.is_a.append(onto.UnmergedBranch)

print("🧠 Manual reasoning complete (MergeCommit, InitialCommit, UnmergedBranch, ConcurrentContributor).")

# --------------------------------------------------------
# === Save populated ontology ===
# --------------------------------------------------------
onto.save(file="ontology/git-onto-logic-populated_2.owl", format="rdfxml")
print("✅ Populated ontology saved: ontology/git-onto-logic-populated.owl")
