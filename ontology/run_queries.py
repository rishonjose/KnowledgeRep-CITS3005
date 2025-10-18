from rdflib import Graph, Namespace
from termcolor import colored  

ONTO_PATH = "outputs/populated.owl"

g = Graph()
g.parse(ONTO_PATH, format="xml")
print(colored(f"Loaded ontology with {len(g)} triples", "green"))

# Namespace
GIT = Namespace("http://example.org/git-onto-logic#")

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


QUERIES = [

    # 1. Repositories with >5 unmerged branches
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

    # 2. Users who contributed to ≥3 repositories (structural)
    ("Users who contributed to ≥3 repositories", """
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

    # 3. Users with concurrent contributions to ≥3 repositories (true overlap)
    ("Users with concurrent contributions to ≥3 repositories", """
    PREFIX git: <http://example.org/git-onto-logic#>

SELECT ?user (COUNT(DISTINCT ?repo) AS ?repoCount)
WHERE {
  ?user a git:ConcurrentContributor .
  ?commit a git:Commit ;
           git:authoredBy ?user ;
           git:onBranch ?branch .
  ?repo git:hasBranch ?branch .
}
GROUP BY ?user
HAVING (COUNT(DISTINCT ?repo) >= 3)
ORDER BY DESC(?repoCount)
LIMIT 10

    """),

    # 4. Merge commits (≥2 parents)
    ("Merge commits (≥2 parents)", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit
    WHERE { ?commit a git:MergeCommit . }
    LIMIT 10
    """),

    # 5. Security commits merged into branches
    ("Security commits merged into branches", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit ?branch
    WHERE {
      ?commit a git:SecurityCommit ;
               git:onBranch ?branch .
    }
    LIMIT 10
    """),

    # 6. Initial commits per repository
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

    # 7. Branch merge graph
    ("Branch merge graph (mergedInto relations)", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?sourceBranch ?targetBranch
    WHERE { ?sourceBranch git:mergedInto ?targetBranch . }
    LIMIT 10
    """),

    

    # 9. Top 5 most active contributors
    ("Top 5 most active contributors", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?user (COUNT(?commit) AS ?commitCount)
    WHERE {
      ?commit a git:Commit ;
               git:authoredBy ?user .
    }
    GROUP BY ?user
    ORDER BY DESC(?commitCount)
    LIMIT 5
    """),

    # 10. Repositories containing security commits
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

    # 11. Users who authored merge commits
    ("Users who authored merge commits", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT DISTINCT ?user
    WHERE {
      ?commit a git:MergeCommit ;
               git:authoredBy ?user .
    }
    LIMIT 10
    """),

    # 12. Average number of commits per branch
    ("Average number of commits per branch", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT (AVG(?commitCount) AS ?averageCommits)
    WHERE {
      SELECT ?branch (COUNT(?commit) AS ?commitCount)
      WHERE {
        ?branch a git:Branch .
        ?branch git:hasCommit ?commit .
      }
      GROUP BY ?branch
    }
    LIMIT 10
    """),

    # 13. Top 10 most frequently modified files
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

    # 14. Commits without an author
    ("Commits without an author (data error check)", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?commit
    WHERE {
      ?commit a git:Commit .
      FILTER NOT EXISTS { ?commit git:authoredBy ?user . }
    }
    LIMIT 10
    """),

    # 15. Branches with no commits
    ("Branches with no commits (data error check)", """
    PREFIX git: <http://example.org/git-onto-logic#>
    SELECT ?branch
    WHERE {
      ?branch a git:Branch .
      FILTER NOT EXISTS { ?branch git:hasCommit ?c . }
    }
    LIMIT 10
    """),
]

for title, query in QUERIES:
    run_query(title, query)

print(colored("\n All SPARQL queries executed successfully.", "green"))
