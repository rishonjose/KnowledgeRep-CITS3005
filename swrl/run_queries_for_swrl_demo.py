from rdflib import Graph, Namespace

# Load the reasoned ontology
g = Graph()
g.parse("outputs/ontology_swrl_demo_reasoned.owl")


git = Namespace("http://example.org/git-onto-logic#")

print("✅ Ontology loaded with", len(g), "triples\n")

# ------------------------------------------------------------
# 1️⃣  Find all SecurityCommits and their messages
# ------------------------------------------------------------
q1 = """
SELECT ?commit ?msg WHERE {
    ?commit a git:SecurityCommit ;
            git:message ?msg .
}
"""

print("=== 🛡️ SecurityCommits (inferred) ===")
for commit, msg in g.query(q1, initNs={'git': git}):
    print(f"{commit.split('#')[-1]} | {msg[:100]}")

# ------------------------------------------------------------
# 2️⃣  Find all InitialCommits
# ------------------------------------------------------------
q2 = """
SELECT ?commit WHERE {
    ?commit a git:InitialCommit .
}
"""

print("\n=== 🌱 InitialCommits ===")
for (c,) in g.query(q2, initNs={'git': git}):
    print(c.split('#')[-1])

# ------------------------------------------------------------
# 3️⃣  Find all UnmergedBranches
# ------------------------------------------------------------
q3 = """
SELECT ?branch WHERE {
    ?branch a git:UnmergedBranch .
}
"""

print("\n=== 🌿 UnmergedBranches ===")
for (b,) in g.query(q3, initNs={'git': git}):
    print(b.split('#')[-1])

# ------------------------------------------------------------
# 4️⃣  Find all commits authored by each user
# ------------------------------------------------------------
q4 = """
SELECT ?user ?commit WHERE {
    ?commit git:authoredBy ?user .
}
"""

print("\n=== 👩‍💻 Commits per User ===")
for user, commit in g.query(q4, initNs={'git': git}):
    print(f"{user.split('#')[-1]} -> {commit.split('#')[-1]}")

# ------------------------------------------------------------
# 5️⃣  Advanced: security commits merged into a branch (logic example)
#     Show commits with "security" keyword that belong to a given branch.
# ------------------------------------------------------------
branch_name = "master"  # or any branch name existing in your dataset
q5 = f"""
SELECT ?commit ?msg WHERE {{
    ?commit a git:SecurityCommit ;
            git:message ?msg ;
            git:onBranch ?branch .
    ?branch git:branchName "{branch_name}" .
}}
"""

print(f"\n=== 🧩 SecurityCommits on branch '{branch_name}' ===")
for commit, msg in g.query(q5, initNs={'git': git}):
    print(f"{commit.split('#')[-1]} | {msg[:100]}")

# ------------------------------------------------------------
# 6️⃣  (Optional) Users who authored at least one SecurityCommit
# ------------------------------------------------------------
q6 = """
SELECT DISTINCT ?user WHERE {
    ?commit a git:SecurityCommit ;
            git:authoredBy ?user .
}
"""

print("\n=== 🔐 Users who authored SecurityCommits ===")
for (user,) in g.query(q6, initNs={'git': git}):
    print(user.split('#')[-1])
