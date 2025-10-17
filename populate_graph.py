# --------------------------------------------------------
# Git-Onto-Logic Ontology Population Script (Redesigned)
# Author: Saayella
# --------------------------------------------------------
import json
from pathlib import Path
from owlready2 import *
from datetime import datetime

# === Load ontology schema ===
onto = get_ontology("ontology/git-onto-logic-redesigned.owl").load()

# === Dataset folder path ===
DATA_DIR = Path("data")

# === Helper: load JSON ===
def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === Load all dataset files ===
repos = load_json("repos.json")
branches = load_json("branches.json")
commits = load_json("commits.json")
users = load_json("users.json")
files = load_json("files.json")
issues = load_json("issues.json")
prs = load_json("pulls.json")

# === Cache dictionaries for lookups ===
repo_map = {}
branch_map = {}
user_map = {}
commit_map = {}

# === Create individuals for repositories ===
for r in repos:
    repo = onto.Repository(f"repo_{r['repo_id']}")
    repo.repoName = [r["repo_name"]]
    repo.repoLanguage = [r.get("repo_language", "Unknown")]
    repo.repoStars = [r.get("repo_stars", 0)]
    repo.repoForks = [r.get("repo_forks", 0)]
    repo_map[r["repo_id"]] = repo

# === Create users ===
for u in users:
    user = onto.User(f"user_{u['user_login']}")
    user.userLogin = [u["user_login"]]
    user.userURL = [u.get("user_url", "")]
    user_map[u["user_login"]] = user

# === Create branches and link to repos ===
for b in branches:
    repo_id = b["repo_id"]
    repo = repo_map.get(repo_id)
    if not repo: 
        continue
    branch_iri = f"repo_{repo_id}__branch_{b['branch_name']}"
    branch = onto.Branch(branch_iri)
    branch.branchName = [b["branch_name"]]
    branch.isDefault = [bool(b.get("is_default", False))]
    branch_map[(repo_id, b["branch_name"])] = branch
    repo.hasBranch.append(branch)

# === Create commits and link ===
for c in commits:
    repo_id = c["repo_id"]
    branch_key = (repo_id, c["branch_name"])
    branch = branch_map.get(branch_key)
    if not branch:
        continue

    commit_iri = f"{c['commit_sha']}"
    commit = onto.Commit(commit_iri)
    commit.commitSHA = [c["commit_sha"]]
    commit.message = [c.get("commit_message", "")]
    commit.commitDate = [c.get("commit_date", "")]
    commit.isInitial = [bool(c.get("is_initial", False))]

    branch.hasCommit.append(commit)
    commit.onBranch.append(branch)

    # Author + committer
    author_login = c.get("commit_author_login")
    committer_login = c.get("commit_committer_login")

    if author_login and author_login in user_map:
        commit.authoredBy.append(user_map[author_login])
    if committer_login and committer_login in user_map:
        commit.committedBy.append(user_map[committer_login])

    # Parent commits (if known)
    parents = c.get("commit_parents", [])
    for psha in parents:
        if psha not in commit_map:  # may appear later
            parent_commit = onto.Commit(psha)
            commit_map[psha] = parent_commit
        commit.parent.append(commit_map[psha])

    commit_map[c["commit_sha"]] = commit

    # Flag security-related commits (via Python keyword scan)
    msg = c.get("commit_message", "").lower()
    if any(k in msg for k in ["security", "vulnerability"]):
        commit.is_a.append(onto.SecurityCommit)

# === Create files and link ===
for fobj in files:
    commit_sha = fobj["commit_sha"]
    if commit_sha not in commit_map:
        continue
    commit = commit_map[commit_sha]
    file_ind = onto.File(f"{commit_sha}__{fobj['file_name'].replace('/', '_')}")
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
    issue.title = [iobj["title"]]
    issue.state = [iobj["state"]]
    repo.hasIssue.append(issue)
    user_login = iobj.get("user_login")
    if user_login and user_login in user_map:
        issue.openedBy.append(user_map[user_login])

# === Create pull requests ===
for pobj in prs:
    repo = repo_map.get(pobj["repo_id"])
    if not repo:
        continue
    pr = onto.PullRequest(f"pr_{pobj['pr_id']}")
    pr.title = [pobj["title"]]
    pr.state = [pobj["state"]]
    pr.mergedAt = [pobj.get("merged_at") or ""]

    repo.hasPullRequest.append(pr)

    user_login = pobj.get("user_login")
    if user_login and user_login in user_map:
        pr.openedBy.append(user_map[user_login])

    base_branch = branch_map.get((pobj["repo_id"], pobj["base_branch"]))
    head_branch = branch_map.get((pobj["repo_id"], pobj["head_branch"]))

    if base_branch:
        pr.hasBaseBranch.append(base_branch)
    if head_branch:
        pr.hasHeadBranch.append(head_branch)
        # If merged, add mergedInto relation
        if pobj.get("merged_at"):
            head_branch.mergedInto.append(base_branch)

# === Save populated ontology ===
onto.save(file="ontology/git-onto-logic-populated.owl", format="rdfxml")
print("✅ Populated ontology saved: ontology/git-onto-logic-populated.owl")
