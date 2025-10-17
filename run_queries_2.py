# --------------------------------------------------------
# Git-Onto-Logic : Extended Validation SPARQL Suite
# File: run_queries_two.py
# Author: Saayella
# --------------------------------------------------------
from rdflib import Graph, Namespace
from termcolor import colored  # pip install termcolor

# === Load the populated ontology ===
ONTO_PATH = "ontology/git-onto-logic-populated.owl"

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
        return
    for row in results:
        vals = [str(x).split("#")[-1] for x in row if x]
        print("  •", ", ".join(vals))

# === 15 Validation Queries ===
QUERIES = [

    # 1. Repositories and their branches
    ("Repositories and their branches", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?branch
    WHERE { ?repo git:hasBranch ?branch . }
    LIMIT 10
    """),

    # 2. Branches and their commits
    ("Branches and their commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?branch ?commit
    WHERE { ?branch git:hasCommit ?commit . }
    LIMIT 10
    """),

    # 3. Commits and their authors
    ("Commits and their authors", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?user
    WHERE { ?commit git:authoredBy ?user . }
    LIMIT 10
    """),

    # 4. Commits and their parent commits
    ("Commits and their parent commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?parent
    WHERE { ?commit git:parent ?parent . }
    LIMIT 10
    """),

    # 5. Users and their authored commits
    ("Users and their authored commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?user ?commit
    WHERE { ?commit git:authoredBy ?user . }
    LIMIT 10
    """),

    # 6. Commits and updated files
    ("Commits and files they modify", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?file
    WHERE { ?commit git:updatesFile ?file . }
    LIMIT 10
    """),

    # 7. Repositories and their issues
    ("Repositories and their issues", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?issue
    WHERE { ?repo git:hasIssue ?issue . }
    LIMIT 10
    """),

    # 8. Issues and their creators
    ("Issues and their creators", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?issue ?user
    WHERE { ?issue git:openedBy ?user . }
    LIMIT 10
    """),

    # 9. Pull requests and their base/head branches
    ("Pull requests and their base/head branches", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?pr ?head ?base
    WHERE {
      ?pr a git:PullRequest .
      OPTIONAL { ?pr git:hasHeadBranch ?head . }
      OPTIONAL { ?pr git:hasBaseBranch ?base . }
    }
    LIMIT 10
    """),

    # 10. Pull requests that were merged (mergedAt timestamp)
    ("Pull requests with merge timestamps", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?pr ?mergedAt
    WHERE {
      ?pr a git:PullRequest ;
          git:mergedAt ?mergedAt .
      FILTER(?mergedAt != "")
    }
    LIMIT 10
    """),

    # 11. Branches that have been merged into others
    ("Branches merged into others", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?src ?target
    WHERE { ?src git:mergedInto ?target . }
    LIMIT 10
    """),

    # 12. Users who opened both issues and pull requests
    ("Users who opened both issues and pull requests", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT DISTINCT ?user
    WHERE {
      ?issue git:openedBy ?user .
      ?pr git:openedBy ?user .
    }
    LIMIT 10
    """),

    # 13. Commits flagged as SecurityCommit
    ("Commits flagged as SecurityCommit", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?branch
    WHERE {
      ?commit a git:SecurityCommit ;
               git:onBranch ?branch .
    }
    LIMIT 10
    """),

    # 14. Branches marked as UnmergedBranch
    ("Branches marked as UnmergedBranch", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?branch
    WHERE { ?branch a git:UnmergedBranch . }
    LIMIT 10
    """),

    # 15. Combined test — Repo, Branch, Commit, User chain
    ("Full chain: repo → branch → commit → user", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?repo ?branch ?commit ?user
    WHERE {
      ?repo git:hasBranch ?branch .
      ?branch git:hasCommit ?commit .
      OPTIONAL { ?commit git:authoredBy ?user . }
    }
    LIMIT 10
    """),
]

# === Run all queries ===
for title, query in QUERIES:
    run_query(title, query)

print(colored("\n✅ Validation queries executed successfully (15/15).", "green"))
