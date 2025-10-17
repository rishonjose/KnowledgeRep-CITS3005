# --------------------------------------------------------
# Populate Git-Onto-Logic Ontology with Real Dataset
# Author: Saayella
# --------------------------------------------------------

from owlready2 import *
import json, datetime
from pathlib import Path

# Load ontology (ensure same filename as exported)
onto = get_ontology("ontology/git-onto-logic-final.owl").load()

# Data folder path
DATA_DIR = Path("data")

def parse_date(date_str):
    """Convert ISO timestamps (from GitHub) into datetime objects."""
    try:
        return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.datetime.now()

def load_json(name):
    """Load JSON file from /data directory."""
    with open(DATA_DIR / name, "r") as f:
        return json.load(f)

# --------------------------------------------------------
# Load all JSON files
# --------------------------------------------------------
repos_data = load_json("repos.json")
branches_data = load_json("branches.json")
commits_data = load_json("commits.json")
files_data = load_json("files.json")
users_data = load_json("users.json")

print(f"✅ Loaded dataset: {len(repos_data)} repos, {len(branches_data)} branches, "
      f"{len(commits_data)} commits, {len(files_data)} files, {len(users_data)} users")

# --------------------------------------------------------
# Create Individuals
# --------------------------------------------------------
users, repos, branches, commits, files = {}, {}, {}, {}, {}

# --- Users ---
for u in users_data:
    user = onto.User(u["user_login"])
    user.hasName = [u["user_login"]]
    users[u["user_login"]] = user

# --- Repositories ---
for r in repos_data:
    repo = onto.Repository(r["repo_name"].replace("/", "_"))
    repo.hasName = [r["repo_name"]]
    repos[r["repo_id"]] = repo

# --- Branches ---
for b in branches_data:
    key = (b["repo_id"], b["branch_name"])
    repo = repos.get(b["repo_id"])
    branch = onto.Branch(f"{b['branch_name']}_{b['repo_id']}")
    branch.hasName = [b["branch_name"]]
    branch.isMain = [b.get("is_default", False)]
    branches[key] = branch
    if repo: repo.hasBranch.append(branch)

# --- Commits ---
for c in commits_data:
    repo_id = c["repo_id"]
    branch_name = c["branch_name"]
    key = (repo_id, branch_name)
    branch = branches.get(key)
    author = users.get(c["commit_author_login"])
    
    commit = onto.Commit(c["commit_sha"])
    commit.hasName = [c["commit_sha"]]
    commit.hasId = [c["commit_sha"]]
    commit.message = [c["commit_message"]]
    commit.timestamp = [parse_date(c["commit_date"])]
    
    if branch: commit.onBranch = [branch]
    if author: commit.authoredBy = [author]
    if branch: branch.hasCommit.append(commit)
    commits[c["commit_sha"]] = commit

# Add parent relationships (after all commits created)
for c in commits_data:
    commit = commits.get(c["commit_sha"])
    for parent_sha in c.get("commit_parents", []):
        parent_commit = commits.get(parent_sha)
        if parent_commit: commit.parent.append(parent_commit)

# --- Files ---
for f in files_data:
    repo_id = f["repo_id"]
    commit_sha = f["commit_sha"]
    filename = f["file_name"]

    file_obj = files.get(filename)
    if not file_obj:
        file_obj = onto.File(filename.replace("/", "_"))
        file_obj.hasName = [filename]
        files[filename] = file_obj
        repo = repos.get(repo_id)
        if repo: repo.containsFile.append(file_obj)

    commit = commits.get(commit_sha)
    if commit:
        commit.updatesFile.append(file_obj)
        author = commit.authoredBy[0] if commit.authoredBy else None
        if author: file_obj.modifiedBy = [author]
        file_obj.modificationTime = [commit.timestamp[0]]

# --------------------------------------------------------
# Run Reasoning
# --------------------------------------------------------
print("🧠 Running OWL reasoner (HermiT)...")
sync_reasoner()
print("✅ Reasoning complete!")

# --------------------------------------------------------
# Export populated ontology
# --------------------------------------------------------
output_path = "ontology/git-onto-logic-populated.owl"
onto.save(file=output_path, format="rdfxml")
print(f"🎉 Populated ontology saved to {output_path}")
