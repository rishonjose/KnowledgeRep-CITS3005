# --------------------------------------------------------
# Git-Onto-Logic : Final SPARQL Query Runner
# Author: Saayella
# --------------------------------------------------------

from rdflib import Graph, Namespace
from pathlib import Path

ONTO_FILE = Path("ontology/git-onto-logic-populated.owl")

if not ONTO_FILE.exists():
    raise FileNotFoundError(
        "❌ Ontology not found. Run populate_graph_final.py first."
    )

print("✅ Loaded ontology:", ONTO_FILE)

# Load graph
g = Graph()
g.parse(str(ONTO_FILE), format="xml")

EX = Namespace("http://example.org/git-onto-logic#")

# --------------------------------------------------------
# Helper
# --------------------------------------------------------
def run_query(label, q):
    print("\n" + "=" * 75)
    print(f"🔍 {label}")
    print("=" * 75)
    results = list(g.query(q))
    if not results:
        print("(no results)")
    for row in results[:20]:  # limit output
        print(" → ".join(str(x).split("#")[-1] for x in row))
    print("-" * 75)

# --------------------------------------------------------
# CORE QUERIES (from project brief)
# --------------------------------------------------------

Q1 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?repo (COUNT(?branch) AS ?branchCount)
WHERE {
  ?repo a ex:Repository ;
        ex:hasBranch ?branch .
  FILTER NOT EXISTS { ?branch ex:isMain true }
}
GROUP BY ?repo
HAVING(?branchCount > 5)
"""

Q2 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?user (COUNT(DISTINCT ?repo) AS ?repoCount)
WHERE {
  ?user a ex:User .
  ?commit ex:authoredBy ?user .
  ?branch ex:hasCommit ?commit .
  ?repo ex:hasBranch ?branch .
}
GROUP BY ?user
HAVING(?repoCount >= 3)
"""

Q3 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?commit ?msg
WHERE {
  ?commit a ex:MergeCommit ;
           ex:message ?msg .
}
"""

Q4 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?commit ?msg ?branch
WHERE {
  ?commit a ex:Commit ;
           ex:message ?msg ;
           ex:onBranch ?branch .
  FILTER(CONTAINS(LCASE(?msg), "security") || CONTAINS(LCASE(?msg), "vulnerability"))
}
"""

# --------------------------------------------------------
# ADDITIONAL EXPLORATORY QUERIES
# --------------------------------------------------------

Q5 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?repo ?name
WHERE {
  ?repo a ex:Repository ;
        ex:hasName ?name .
}
"""

Q6 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?repo ?branch
WHERE {
  ?repo a ex:Repository ;
        ex:hasBranch ?branch .
}
"""

Q7 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?commit ?author
WHERE {
  ?commit a ex:Commit ;
           ex:authoredBy ?author .
}
LIMIT 20
"""

Q8 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?branch (COUNT(?commit) AS ?numCommits)
WHERE {
  ?branch a ex:Branch ;
           ex:hasCommit ?commit .
}
GROUP BY ?branch
ORDER BY DESC(?numCommits)
"""

Q9 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT ?user (COUNT(?commit) AS ?numCommits)
WHERE {
  ?commit a ex:Commit ;
           ex:authoredBy ?user .
}
GROUP BY ?user
ORDER BY DESC(?numCommits)
LIMIT 10
"""

Q10 = """
PREFIX ex: <http://example.org/git-onto-logic#>
SELECT DISTINCT ?user ?repo
WHERE {
  ?commit a ex:Commit ;
           ex:authoredBy ?user ;
           ex:onBranch ?branch .
  ?repo ex:hasBranch ?branch .
}
ORDER BY ?user
"""

# --------------------------------------------------------
# EXECUTE ALL QUERIES
# --------------------------------------------------------
run_query("1️⃣ Repositories with >5 unmerged branches", Q1)
run_query("2️⃣ Users who contributed to 3+ repositories", Q2)
run_query("3️⃣ All merge commits", Q3)
run_query("4️⃣ Commits mentioning 'security' or 'vulnerability'", Q4)

run_query("5️⃣ All repositories", Q5)
run_query("6️⃣ All branches per repository", Q6)
run_query("7️⃣ Commits and their authors", Q7)
run_query("8️⃣ Commits per branch", Q8)
run_query("9️⃣ Most active users (by commit count)", Q9)
run_query("🔟 Users and repositories they contributed to", Q10)

print("\n✅ All 10 queries executed successfully.")
