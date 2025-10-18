import json
from pathlib import Path
from owlready2 import *
from datetime import datetime
from collections import defaultdict

# === Load ontology schema ===
onto = get_ontology("ontology.owl").load()

# === Dataset folder path ===
DATA_DIR = Path("data")

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

# === Create repository individuals ===
for r in repos:
    repo_iri = f"repo_{r['repo_id']}"
    repo = onto.Repository(repo_iri)
    repo.repoName = [r.get("repo_name", "Unknown")]
    repo.repoLanguage = [r.get("repo_language") or "Unknown"]
    repo.repoStars = [int(r.get("repo_stars", 0))]
    repo.repoForks = [int(r.get("repo_forks", 0))]
    repo_map[r["repo_id"]] = repo

# === Create user individuals ===
for u in users:
    safe_login = u["user_login"].replace("/", "_")
    user = onto.User(f"user_{safe_login}")
    user.userLogin = [u["user_login"]]
    user.userURL = [u.get("user_url", "")]
    user_map[u["user_login"]] = user

# === Create branches and link to repos ===
for b in branches:
    repo = repo_map.get(b["repo_id"])
    if not repo:
        continue
    branch_name = b["branch_name"].replace("/", "_")
    branch_iri = f"repo_{b['repo_id']}__branch_{branch_name}"
    branch = onto.Branch(branch_iri)
    branch.branchName = [b["branch_name"]]
    branch.isDefault = [bool(b.get("is_default", False))]
    branch_map[(b["repo_id"], b["branch_name"])] = branch
    repo.hasBranch.append(branch)

# === Create commits ===
for c in commits:
    repo_id = c["repo_id"]
    branch_key = (repo_id, c["branch_name"])
    branch = branch_map.get(branch_key)
    if not branch:
        continue

    commit_iri = f"commit_{c['commit_sha'].replace('/', '_')}"
    commit = commit_map.get(c["commit_sha"]) or onto.Commit(commit_iri)
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

    # Parent commits
    for psha in c.get("commit_parents", []):
        parent_commit = commit_map.get(psha) or onto.Commit(f"commit_{psha.replace('/', '_')}")
        commit_map[psha] = parent_commit
        commit.parent.append(parent_commit)

    msg = c.get("commit_message", "").lower()
    if any(k in msg for k in ["security", "vulnerability"]):
        commit.is_a.append(onto.SecurityCommit)

# === Create files ===
for fobj in files:
    commit = commit_map.get(fobj["commit_sha"])
    if not commit:
        continue
    file_iri = f"{fobj['commit_sha']}__{fobj['file_name'].replace('/', '_')}"
    file_ind = onto.File(file_iri)
    file_ind.fileName = [fobj["file_name"]]
    file_ind.fileStatus = [fobj.get("file_status", "modified")]
    file_ind.fileChanges = [int(fobj.get("file_changes", 0))]
    commit.updatesFile.append(file_ind)

# === Create issues ===
for iobj in issues:
    repo = repo_map.get(iobj["repo_id"])
    if not repo:
        continue
    issue = onto.Issue(f"issue_{iobj['issue_id']}")
    issue.title = [iobj.get("title", "Untitled")]
    issue.state = [iobj.get("state", "open")]
    repo.hasIssue.append(issue)
    if (u := iobj.get("user_login")) and u in user_map:
        issue.openedBy.append(user_map[u])

# === Create pull requests ===
for pobj in prs:
    repo = repo_map.get(pobj["repo_id"])
    if not repo:
        continue
    pr = onto.PullRequest(f"pr_{pobj['pr_id']}")
    pr.title = [pobj.get("title", "Untitled PR")]
    pr.state = [pobj.get("state", "open")]
    pr.mergedAt = [pobj.get("merged_at") or ""]
    repo.hasPullRequest.append(pr)
    if (u := pobj.get("user_login")) and u in user_map:
        pr.openedBy.append(user_map[u])
    base_branch = branch_map.get((pobj["repo_id"], pobj.get("base_branch")))
    head_branch = branch_map.get((pobj["repo_id"], pobj.get("head_branch")))
    if base_branch:
        pr.hasBaseBranch.append(base_branch)
    if head_branch:
        pr.hasHeadBranch.append(head_branch)
        if pobj.get("merged_at"):
            head_branch.mergedInto.append(base_branch)

# === Detect concurrent contributors ===
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
    repo_periods = [(min(d), max(d)) for d in repos.values()]
    overlaps = sum(1 for i, (s1, e1) in enumerate(repo_periods)
                     for j, (s2, e2) in enumerate(repo_periods)
                     if i < j and s1 <= e2 and s2 <= e1)
    if overlaps >= 3:
        concurrent_users.append(user)

print(f"✅ Found {len(concurrent_users)} concurrent contributors.")
for user_login in concurrent_users:
    if user_login in user_map:
        user_map[user_login].isConcurrentContributor = [True]

# Optional: mark all others as False
for user in user_map.values():
    if not hasattr(user, "isConcurrentContributor"):
        user.isConcurrentContributor = [False]

# === Manual reasoning ===
for c in onto.Commit.instances():
    if len(c.parent) >= 2:
        c.is_a.append(onto.MergeCommit)
    elif len(c.parent) == 0:
        c.is_a.append(onto.InitialCommit)
for b in onto.Branch.instances():
    if not b.mergedInto:
        b.is_a.append(onto.UnmergedBranch)

# === Save ontology ===
onto.save(file="populated.owl", format="rdfxml")
print("✅ Populated ontology saved: populated.owl")
