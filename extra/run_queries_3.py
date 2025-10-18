# --------------------------------------------------------
# Git-Onto-Logic : Extended Validation SPARQL Suite (20 Queries)
# File: run_queries_two.py
# Author: Saayella
# --------------------------------------------------------
from rdflib import Graph, Namespace
from termcolor import colored  # pip install termcolor

# === Load populated ontology ===
ONTO_PATH = "populated_knowledge_graph.owl"

g = Graph()
g.parse(ONTO_PATH, format="xml")
print(colored(f"✅ Loaded ontology with {len(g)} triples", "green"))

# === Namespace ===
GIT = Namespace("http://example.org/git-onto-logic#")

# === Helper ===
def run_query(title, query):
    print(colored(f"\n🔍 {title}", "cyan"))
    print(colored("-" * (len(title) + 5), "cyan"))
    results = g.query(query)
    if len(results) == 0:
        print(colored("No results found.", "yellow"))
        return
    for row in results:
        vals = [str(x).split("#")[-1] for x in row if x]
        print("  •", ", ".join(vals))

# === 20 SPARQL Queries ===
QUERIES = [

    # 1–15 (from previous file, unchanged)
    ("Repositories and their branches", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?branch WHERE { ?repo git:hasBranch ?branch . } LIMIT 10
    """),

    ("Branches and their commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?branch ?commit WHERE { ?branch git:hasCommit ?commit . } LIMIT 10
    """),

    ("Commits and their authors", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?user WHERE { ?commit git:authoredBy ?user . } LIMIT 10
    """),

    ("Commits and their parent commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?parent WHERE { ?commit git:parent ?parent . } LIMIT 10
    """),

    ("Users and their authored commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?user ?commit WHERE { ?commit git:authoredBy ?user . } LIMIT 10
    """),

    ("Commits and files they modify", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?file WHERE { ?commit git:updatesFile ?file . } LIMIT 10
    """),

    ("Repositories and their issues", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?issue WHERE { ?repo git:hasIssue ?issue . } LIMIT 10
    """),

    ("Issues and their creators", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?issue ?user WHERE { ?issue git:openedBy ?user . } LIMIT 10
    """),

    ("Pull requests and their base/head branches", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?pr ?head ?base
    WHERE {
      ?pr a git:PullRequest .
      OPTIONAL { ?pr git:hasHeadBranch ?head . }
      OPTIONAL { ?pr git:hasBaseBranch ?base . }
    } LIMIT 10
    """),

    ("Pull requests with merge timestamps", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?pr ?mergedAt
    WHERE {
      ?pr a git:PullRequest ;
          git:mergedAt ?mergedAt .
      FILTER(?mergedAt != "")
    } LIMIT 10
    """),

    ("Branches merged into others", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?src ?target WHERE { ?src git:mergedInto ?target . } LIMIT 10
    """),

    ("Users who opened both issues and pull requests", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT DISTINCT ?user
    WHERE { ?issue git:openedBy ?user . ?pr git:openedBy ?user . }
    LIMIT 10
    """),

    ("Commits flagged as SecurityCommit", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?branch
    WHERE { ?commit a git:SecurityCommit ; git:onBranch ?branch . }
    LIMIT 10
    """),

    ("Branches marked as UnmergedBranch", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?branch WHERE { ?branch a git:UnmergedBranch . } LIMIT 10
    """),

    ("Full chain: repo → branch → commit → user", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?branch ?commit ?user
    WHERE {
      ?repo git:hasBranch ?branch .
      ?branch git:hasCommit ?commit .
      OPTIONAL { ?commit git:authoredBy ?user . }
    } LIMIT 10
    """),

    # --- 5 NEW QUERIES BELOW ---

    # 16. Top 10 most forked repositories
    ("Top 10 most forked repositories", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?forks
    WHERE {
      ?repo a git:Repository ;
            git:repoForks ?forks .
    }
    ORDER BY DESC(?forks)
    LIMIT 10
    """),

    # 17. Branches that are default (isDefault true)
    ("Default branches of repositories", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?branch
    WHERE {
      ?repo git:hasBranch ?branch .
      ?branch git:isDefault true .
    }
    LIMIT 10
    """),

    # 18. Repositories with commits by multiple users
    ("Repositories with multi-user commit history", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo (COUNT(DISTINCT ?user) AS ?userCount)
    WHERE {
      ?repo git:hasBranch ?branch .
      ?branch git:hasCommit ?commit .
      ?commit git:authoredBy ?user .
    }
    GROUP BY ?repo
    HAVING (?userCount > 1)
    LIMIT 10
    """),

    # 19. Files changed in security-related commits
    ("Files modified in security-related commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?file
    WHERE {
      ?commit a git:SecurityCommit ;
               git:updatesFile ?file .
    }
    LIMIT 10
    """),

    # 20. Users who authored both merge and security commits
    ("Users who authored both merge and security commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT DISTINCT ?user
    WHERE {
      ?merge a git:MergeCommit ; git:authoredBy ?user .
      ?sec a git:SecurityCommit ; git:authoredBy ?user .
    }
    LIMIT 10
    """),
]

# === Run all queries ===
for title, query in QUERIES:
    run_query(title, query)

print(colored("\n✅ All 20 validation queries executed successfully.", "green"))
