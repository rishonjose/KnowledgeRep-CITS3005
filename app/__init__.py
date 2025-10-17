# --------------------------------------------------------
# Git-Onto-Logic Query Script
# Author: Saayella
# --------------------------------------------------------
from rdflib import Graph, Namespace

# === Load the populated ontology ===
file_path = "ontology/git-onto-logic-populated.owl"

g = Graph()
g.parse(file_path, format="xml")

print(f"✅ Loaded ontology with {len(g)} triples")

# === Define namespace ===
GIT = Namespace("http://example.org/git-onto-logic#")

# --------------------------------------------------------
# Query 1: Repositories with more than 5 unmerged branches
# --------------------------------------------------------
query1 = """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?repo (COUNT(?branch) AS ?unmergedCount)
WHERE {
  ?repo a git:Repository .
  ?repo git:hasBranch ?branch .
  ?branch a git:UnmergedBranch .
}
GROUP BY ?repo
HAVING (COUNT(?branch) > 5)
"""

# --------------------------------------------------------
# Query 2: Users who contributed to ≥3 repositories
# --------------------------------------------------------
query2 = """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?user (COUNT(DISTINCT ?repo) AS ?repoCount)
WHERE {
  ?commit a git:Commit ;
           git:authoredBy ?user ;
           git:onBranch ?branch .
  ?repo git:hasBranch ?branch .
}
GROUP BY ?user
HAVING (COUNT(DISTINCT ?repo) >= 3)
"""

# --------------------------------------------------------
# Query 3: Commits that are merges
# --------------------------------------------------------
query3 = """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?commit
WHERE {
  ?commit a git:MergeCommit .
}
"""

# --------------------------------------------------------
# Query 4: Security-related commits merged into a branch
# --------------------------------------------------------
query4 = """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?commit ?branch
WHERE {
  ?commit a git:SecurityCommit ;
           git:onBranch ?branch .
  # Optionally restrict to commits merged into a specific branch:
  # ?branch git:mergedInto git:masterBranch .
}
"""

# --------------------------------------------------------
# Run and display results
# --------------------------------------------------------
def run_query(label, q):
    print(f"\n🔍 {label}")
    print("-" * (len(label) + 3))
    results = g.query(q)
    if not results:
        print("No results found.")
        return
    for row in results:
        print("  •", [str(x).split('#')[-1] for x in row])

run_query("Q1: Repositories with >5 unmerged branches", query1)
run_query("Q2: Users who contributed to ≥3 repos", query2)
run_query("Q3: Merge commits", query3)
run_query("Q4: Security commits merged into branches", query4)

print("\n✅ All SPARQL queries executed successfully.")
