# --------------------------------------------------------
# Populate Git-Onto-Logic (Advanced) Ontology with Dataset
# Author: Saayella
# --------------------------------------------------------
import json
from pathlib import Path
from owlready2 import *

# --------------------------------------------------------
# Paths
# --------------------------------------------------------
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
ONTO_FILE = ROOT / "ontology" / "git-onto-logic-advanced.owl"
OUTPUT_FILE = ROOT / "ontology" / "git-onto-logic-populated.owl"

# --------------------------------------------------------
# Helpers
# --------------------------------------------------------
def load_json(name):
    p = DATA_DIR / name
    if not p.exists():
        print(f"⚠️  Missing {p}, skipping.")
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------------------------------------
# Load Ontology
# --------------------------------------------------------
if not ONTO_FILE.exists():
    raise FileNotFoundError("❌ Ontology file missing. Run git_onto_logic_advanced.py first.")

onto = get_ontology(ONTO_FILE.as_uri()).load()
print(f"✅ Loaded base ontology: {ONTO_FILE}")

Repository   = onto.Repository
Branch       = onto.Branch
Commit       = onto.Commit
File         = onto.File
User         = onto.User
Issue        = onto.Issue
PullRequest  = onto.PullRequest

# --------------------------------------------------------
# Load Dataset
# --------------------------------------------------------
repos_data   = load_json("repos.json")
branches_data= load_json("branches.json")
commits_data = load_json("commits.json")
files_data   = load_json("files.json")
issues_data  = load_json("issues.json")
prs_data     = load_json("pull_requests.json")
users_data   = load_json("users.json")

print(
    f"📦 Dataset sizes → repos: {len(repos_data)}, branches: {len(branches_data)}, "
    f"commits: {len(commits_data)}, files: {len(files_data)}, "
    f"issues: {len(issues_data)}, PRs: {len(prs_data)}, users: {len(users_data)}"
)

# --------------------------------------------------------
# Create Individuals
# --------------------------------------------------------
users, repos, branches, commits, files, issues, pulls = {}, {}, {}, {}, {}, {}, {}

# --- Users ---
for u in users_data:
    login = u.get("user_login")
    if not login or login in users:
        continue
    user_ind = User(login)
    user_ind.hasName = login
    users[login] = user_ind

# --- Repositories ---
for r in repos_data:
    rid = r["repo_id"]
    repolabel = r.get("repo_name", f"repo_{rid}").replace("/", "_")
    repo_ind = Repository(repolabel)
    repo_ind.hasName = r.get("repo_name", repolabel)
    repos[rid] = repo_ind

# --- Branches ---
for b in branches_data:
    rid = b["repo_id"]
    bname = b["branch_name"]
    key = (rid, bname)
    branch_ind = Branch(f"{bname}_{rid}")
    branch_ind.hasName = bname
    branch_ind.isMain = [bool(b.get("is_default", False))]
    branches[key] = branch_ind
    if rid in repos:
        repos[rid].hasBranch.append(branch_ind)

# --- Commits ---
for c in commits_data:
    sha = c["commit_sha"]
    rid = c["repo_id"]
    bname = c["branch_name"]
    author_login = c.get("commit_author_login")

    commit_ind = commits.get(sha) or Commit(sha)
    commits[sha] = commit_ind
    commit_ind.hasName = sha
    commit_ind.message = [c.get("commit_message", "")]
    commit_ind.timestamp = [c.get("commit_date", "")]

    if author_login and author_login in users:
        commit_ind.authoredBy = [users[author_login]]

    branch_key = (rid, bname)
    br = branches.get(branch_key)
    if br:
        commit_ind.onBranch = [br]
        br.hasCommit.append(commit_ind)

# --- Parent Relationships ---
for c in commits_data:
    sha = c["commit_sha"]
    child = commits.get(sha)
    if not child:
        continue
    for psha in c.get("commit_parents", []):
        parent_commit = commits.get(psha)
        if not parent_commit:
            parent_commit = Commit(psha)
            parent_commit.hasName = psha
            commits[psha] = parent_commit
        child.parent.append(parent_commit)

# --- Files ---
for f in files_data:
    sha = f["commit_sha"]
    fname = f["file_name"]
    file_ind = files.get(fname)
    if not file_ind:
        file_ind = File(fname.replace("/", "_"))
        file_ind.hasName = fname
        files[fname] = file_ind
    commit_ind = commits.get(sha)
    if commit_ind:
        commit_ind.updatesFile.append(file_ind)

# --- Issues ---
for it in issues_data:
    rid = it["repo_id"]
    iid = it.get("issue_id") or it.get("issue_number")
    title = it.get("title", f"Issue_{iid}")
    state = it.get("state", "")
    opener = it.get("user_login")

    issue_ind = Issue(f"issue_{iid}")
    issue_ind.hasName = title
    issue_ind.status = [state]
    issues[iid] = issue_ind

    repo_ind = repos.get(rid)
    if repo_ind:
        repo_ind.hasIssue.append(issue_ind)
    if opener and opener in users:
        issue_ind.openedBy = [users[opener]]

# --- Pull Requests ---
for pr in prs_data:
    rid = pr["repo_id"]
    prid = pr.get("pr_id") or pr.get("number")
    title = pr.get("title", f"PR_{prid}")
    state = pr.get("state", "")
    opener = pr.get("user_login")
    merged_at = pr.get("merged_at")

    pr_ind = PullRequest(f"pr_{prid}")
    pr_ind.hasName = title
    pr_ind.status = [state]
    pulls[prid] = pr_ind

    repo_ind = repos.get(rid)
    if repo_ind:
        repo_ind.hasPullRequest.append(pr_ind)

    if opener and opener in users:
        pr_ind.openedBy = [users[opener]]
    if merged_at and opener in users:
        pr_ind.mergedBy = [users[opener]]

# --------------------------------------------------------
# Simulate SWRL-like reasoning in Python
# --------------------------------------------------------
security_commits = []
for c in Commit.instances():
    for msg in getattr(c, "message", []):
        if isinstance(msg, str) and ("security" in msg.lower() or "vulnerability" in msg.lower()):
            c.is_a.append(onto.SecurityCommit)
            security_commits.append(c)

if security_commits:
    print(f"🧩 Identified {len(security_commits)} SecurityCommit(s) via keyword rule.")
else:
    print("ℹ️  No commits matched 'security' or 'vulnerability' keywords.")

# --------------------------------------------------------
# Run Reasoner (HermiT)
# --------------------------------------------------------
print("🧠 Running OWL reasoner (HermiT)...")
sync_reasoner()
print("✅ Reasoning complete!")

# --------------------------------------------------------
# Summary
# --------------------------------------------------------
merge_commits = list(onto.MergeCommit.instances())
init_commits  = list(onto.InitialCommit.instances())
security_commits = list(onto.SecurityCommit.instances())

print(f"📊 MergeCommits inferred: {len(merge_commits)}")
print(f"📊 InitialCommits inferred: {len(init_commits)}")
print(f"📊 SecurityCommits inferred (rule or SWRL): {len(security_commits)}")

# --------------------------------------------------------
# Save populated ontology
# --------------------------------------------------------
onto.save(file=str(OUTPUT_FILE), format="rdfxml")
print(f"🎉 Populated ontology saved to {OUTPUT_FILE}")
