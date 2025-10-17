# --------------------------------------------------------
# Git-Onto-Logic : SPARQL Query Suite (Full Validation)
# Author: Saayella
# --------------------------------------------------------
from rdflib import Graph, Namespace
from termcolor import colored  # pip install termcolor if needed

# === Load ontology ===
ONTO_PATH = "ontology/git-onto-logic-populated_2.owl"

g = Graph()
g.parse(ONTO_PATH, format="xml")
print(colored(f"✅ Loaded ontology with {len(g)} triples", "green"))

# === Define namespace ===
GIT = Namespace("http://example.org/git-onto-logic#")

# === Helper ===
def run_query(title, query):
    print(colored(f"\n🔍 {title}", "cyan"))
    print(colored("-" * (len(title) + 5), "cyan"))
    results = g.query(query)
    if len(results) == 0:
        print(colored("No results found.", "yellow"))
    else:
        for row in results:
            vals = [str(x).split("#")[-1] for x in row]
            print("  •", ", ".join(vals))

# --------------------------------------------------------
# 20 Queries — Full Coverage Suite
# --------------------------------------------------------
QUERIES = [

# --- Core Structural Tests ---
("Repositories with >5 unmerged branches", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?repo (COUNT(?branch) AS ?unmergedCount)
WHERE {
  ?repo a git:Repository ;
        git:hasBranch ?branch .
  ?branch a git:UnmergedBranch .
}
GROUP BY ?repo
HAVING (COUNT(?branch) > 5)
LIMIT 10
"""),

("Users who contributed to ≥3 repositories (structural)", """
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
LIMIT 10
"""),

("Merge commits (≥2 parents)", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?commit
WHERE { ?commit a git:MergeCommit . }
LIMIT 10
"""),

("Security commits merged into branches", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?commit ?branch
WHERE {
  ?commit a git:SecurityCommit ;
           git:onBranch ?branch .
}
LIMIT 10
"""),

("Initial commits per repository", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?repo ?branch ?commit
WHERE {
  ?repo git:hasBranch ?branch .
  ?branch git:hasCommit ?commit .
  ?commit a git:InitialCommit .
}
ORDER BY ?repo
LIMIT 10
"""),

("Branch merge graph (mergedInto relations)", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?sourceBranch ?targetBranch
WHERE { ?sourceBranch git:mergedInto ?targetBranch . }
LIMIT 10
"""),

("Pull requests that resulted in merges", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?pr ?mergedAt
WHERE {
  ?pr a git:MergedPullRequest ;
      git:mergedAt ?mergedAt .
  FILTER(?mergedAt != "")
}
ORDER BY DESC(?mergedAt)
LIMIT 10
"""),

("Top 5 most active contributors", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?user (COUNT(?commit) AS ?commitCount)
WHERE {
  ?commit a git:Commit ;
           git:authoredBy ?user .
}
GROUP BY ?user
ORDER BY DESC(?commitCount)
LIMIT 10
"""),

("Repositories containing security commits", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT DISTINCT ?repo
WHERE {
  ?repo git:hasBranch ?branch .
  ?branch git:hasCommit ?commit .
  ?commit a git:SecurityCommit .
}
LIMIT 10
"""),

("Users who authored merge commits", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT DISTINCT ?user
WHERE {
  ?commit a git:MergeCommit ;
           git:authoredBy ?user .
}
LIMIT 10
"""),

# --- Data Quality Checks ---
("Commits without an author (data error check)", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?commit
WHERE {
  ?commit a git:Commit .
  FILTER NOT EXISTS { ?commit git:authoredBy ?user . }
}
LIMIT 10
"""),

("Branches with no commits (data validation)", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?branch
WHERE {
  ?branch a git:Branch .
  FILTER NOT EXISTS { ?branch git:hasCommit ?c . }
}
LIMIT 10
"""),

("Average number of commits per branch", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT (AVG(?commitCount) AS ?averageCommits)
WHERE {
  SELECT ?branch (COUNT(?commit) AS ?commitCount)
  WHERE { ?branch git:hasCommit ?commit . }
  GROUP BY ?branch
}
LIMIT 10
"""),

("Top 10 most frequently modified files", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?file (COUNT(?commit) AS ?timesModified)
WHERE {
  ?commit a git:Commit ;
           git:updatesFile ?file .
}
GROUP BY ?file
ORDER BY DESC(?timesModified)
LIMIT 10
"""),

# --- Concurrency Logic (New) ---
("Concurrent contributors", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?user
WHERE { ?user a git:ConcurrentContributor . }
LIMIT 10
"""),

("Concurrent contributors and their repositories", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?user ?repo
WHERE {
  ?user a git:ConcurrentContributor .
  ?commit git:authoredBy ?user ;
          git:onBranch ?branch .
  ?repo git:hasBranch ?branch .
}
LIMIT 10
"""),

("Concurrent vs total contributor count", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT (COUNT(DISTINCT ?userAll) AS ?totalUsers)
       (COUNT(DISTINCT ?userConcurrent) AS ?concurrentUsers)
WHERE {
  {
    SELECT DISTINCT ?userAll WHERE { ?commit git:authoredBy ?userAll . }
  }
  OPTIONAL { ?userConcurrent a git:ConcurrentContributor . }
}
LIMIT 10
"""),

("Concurrent contributors who made security commits", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT DISTINCT ?user
WHERE {
  ?user a git:ConcurrentContributor .
  ?commit git:authoredBy ?user ;
           a git:SecurityCommit .
}
LIMIT 10
"""),

("Most active concurrent contributors (by commit count)", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?user (COUNT(?commit) AS ?commitCount)
WHERE {
  ?user a git:ConcurrentContributor .
  ?commit git:authoredBy ?user .
}
GROUP BY ?user
ORDER BY DESC(?commitCount)
LIMIT 10
"""),

("Concurrent contributors overlapping same branches", """
PREFIX git: <http://example.org/git-onto-logic#>
SELECT ?branch (COUNT(DISTINCT ?user) AS ?concurrentUsers)
WHERE {
  ?user a git:ConcurrentContributor .
  ?commit git:authoredBy ?user ;
          git:onBranch ?branch .
}
GROUP BY ?branch
HAVING (?concurrentUsers >= 3)
LIMIT 10
""")
]

# --------------------------------------------------------
# Run all queries
# --------------------------------------------------------
for title, query in QUERIES:
    run_query(title, query)

print(colored("\n✅ All SPARQL validation queries executed successfully.", "green"))
