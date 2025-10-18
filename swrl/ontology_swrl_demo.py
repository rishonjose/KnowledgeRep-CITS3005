from owlready2 import *
import json
from pathlib import Path
import os

# ============================================================
# Load ontology schema
# ============================================================
onto = get_ontology("outputs/ontology.owl").load()

# ============================================================
# Choose dataset folder automatically
# ============================================================
if Path("truncated_data").exists():
    DATA_DIR = Path("truncated_data")
else:
    DATA_DIR = Path("data")

print(f"📂 Using dataset folder: {DATA_DIR}")

def load_json(filename, n=None):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[:n] if n else data

repos    = load_json("repos.json", 2)
branches = load_json("branches.json", 3)
commits  = load_json("commits.json", 10)
users    = load_json("users.json", 5)
files    = load_json("files.json", 5)
issues   = load_json("issues.json", 3)
prs      = load_json("pulls.json", 3)

repo_map, branch_map, user_map, commit_map = {}, {}, {}, {}

# ============================================================
# Create Individuals
# ============================================================
for u in users:
    user = onto.User(f"user_{u['user_login'].replace('/', '_')}")
    user.userLogin = [u["user_login"]]
    user_map[u["user_login"]] = user

for r in repos:
    repo = onto.Repository(f"repo_{r['repo_id']}")
    repo.repoName = [r.get("repo_name", "Unnamed Repo")]
    repo.repoLanguage = [r.get("repo_language", "")]
    repo_map[r["repo_id"]] = repo

for b in branches:
    repo = repo_map.get(b["repo_id"])
    if not repo:
        continue
    branch = onto.Branch(f"branch_{b['branch_name'].replace('/', '_')}")
    branch.branchName = [b["branch_name"]]
    repo.hasBranch.append(branch)
    branch_map[(b["repo_id"], b["branch_name"])] = branch

for c in commits:
    branch = branch_map.get((c["repo_id"], c["branch_name"]))
    if not branch:
        continue
    commit = onto.Commit(f"commit_{c['commit_sha'].replace('/', '_')}")
    commit.commitSHA = [c["commit_sha"]]
    commit.message = [c.get("commit_message", "")]
    branch.hasCommit.append(commit)
    commit_map[c["commit_sha"]] = commit

    if (auth := c.get("commit_author_login")) and auth in user_map:
        commit.authoredBy.append(user_map[auth])

    for p in c.get("commit_parents", []):
        if p in commit_map:
            commit.parent.append(commit_map[p])

# ============================================================
# Simulated SWRL Reasoning via Python + Safe Rule Placeholders
# ============================================================

# --- SecurityCommit simulation (keyword detection) ---
keywords = ["security", "vulnerability", "auth", "patch", "login"]
for c in onto.Commit.instances():
    msg = (c.message[0] if c.message else "").lower()
    if any(k in msg for k in keywords):
        c.is_a.append(onto.SecurityCommit)

# --- MergeCommit inference via class equivalence / parents ---
for c in onto.Commit.instances():
    if len(c.parent) >= 2:
        c.is_a.append(onto.MergeCommit)

# --- InitialCommit inference ---
for c in onto.Commit.instances():
    if len(c.parent) == 0:
        c.is_a.append(onto.InitialCommit)

# --- UnmergedBranch inference ---
for b in onto.Branch.instances():
    if not b.mergedInto:
        b.is_a.append(onto.UnmergedBranch)

# --- Placeholder SWRL rules (for .owl export) ---
with onto:
    r1 = Imp()
    r1.set_as_rule("Commit(?c), message(?c, ?m) -> SecurityCommit(?c)")
    r2 = Imp()
    r2.set_as_rule("Commit(?c), parent(?c, ?p1), parent(?c, ?p2), differentFrom(?p1, ?p2) -> MergeCommit(?c)")
    r3 = Imp()
    r3.set_as_rule("Commit(?c) -> InitialCommit(?c)")

# ============================================================
# Run actual OWL Reasoner (HermiT)
# ============================================================
print("\n🔍 Running HermiT reasoning on demo dataset...")
sync_reasoner()

# ============================================================
# Display Inferred Results
# ============================================================
print("\n=== 🛡️ SecurityCommits ===")
for c in onto.SecurityCommit.instances():
    print("-", c.name, "|", c.message[0])

print("\n=== 🔀 MergeCommits ===")
for c in onto.MergeCommit.instances():
    print("-", c.name)

print("\n=== 🌱 InitialCommits ===")
for c in onto.InitialCommit.instances():
    print("-", c.name)

print("\n=== 🌿 UnmergedBranches ===")
for b in onto.UnmergedBranch.instances():
    print("-", b.name)

# ============================================================
# Save output ontology (raw + materialized)
# ============================================================
onto.save("ontology_swrl_demo.owl", format="rdfxml")
print("\n💾 Saved: ontology_swrl_demo.owl")

# --- Materialize inferred triples so SPARQL sees them ---
from owlready2 import default_world
default_world.save(file="outputs/ontology_swrl_demo_reasoned.owl", format="rdfxml")
print("💾 Saved reasoned ontology with inferred triples: outputs/ontology_swrl_demo_reasoned.owl")
