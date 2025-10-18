from owlready2 import *
import json
from pathlib import Path
from owlready2 import default_world

onto_path = Path("outputs/ontology.owl").resolve()
onto = get_ontology(onto_path.as_uri()).load()

# Dataset folder automatically

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

repo_map, branch_map, user_map, commit_map = {}, {}, {}, {}


# Individuals

with onto:
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

        commit_iri = f"commit_{c['commit_sha'].replace('/', '_')}"
        commit = commit_map.get(c["commit_sha"])
        if not commit:
            commit = onto.Commit(commit_iri)
            commit_map[c["commit_sha"]] = commit

        commit.commitSHA = [c["commit_sha"]]
        commit.message = [c.get("commit_message", "")]
        branch.hasCommit.append(commit)

        # Authors
        if (auth := c.get("commit_author_login")) and auth in user_map:
            commit.authoredBy.append(user_map[auth])

    # === Second pass: link parents (ensure all exist) ===
    for c in commits:
        this_commit = commit_map.get(c["commit_sha"])
        for psha in c.get("commit_parents", []):
            if psha not in commit_map:
                parent_commit = onto.Commit(f"commit_{psha.replace('/', '_')}")
                commit_map[psha] = parent_commit
            else:
                parent_commit = commit_map[psha]
            this_commit.parent.append(parent_commit)


#  SWRL Rule (executed by HermiT)

with onto:
    rule_real_1 = Imp()
    rule_real_1.set_as_rule("""
        Commit(?c), parent(?c, ?p1), parent(?c, ?p2), differentFrom(?p1, ?p2)
        -> MergeCommit(?c)
    """)

sync_reasoner()

# Display Inferred Results

print("\n=== 🔀 MergeCommits (via SWRL) ===")
for c in onto.MergeCommit.instances():
    print("-", c.name)

# Save
onto.save("outputs/ontology_swrl_demo.owl", format="rdfxml")
default_world.save(file="outputs/ontology_swrl_demo_reasoned.owl", format="rdfxml")
print("\nSaved: outputs/ontology_swrl_demo_reasoned.owl")
print("SWRL reasoning demo completed successfully!")
