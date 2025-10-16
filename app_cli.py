# app_cli.py
from ontology.ontology_v1 import onto
from rdflib import Graph

# Load ontology
onto.load(file="ontology/git-onto-logic.owl")

# ------------------------------------------------------------------
# Temporary test data (for local run until ontology is populated)
# ------------------------------------------------------------------
from datetime import datetime

with onto:
    # --- Repository ---
    test_repo = onto.Repository("repo_test")
    test_repo.hasName = ["Guild Volunteering"]

    # --- Branches ---
    branch_main = onto.Branch("branch_main")
    branch_main.hasName = ["main"]
    branch_dev = onto.Branch("branch_dev")
    branch_dev.hasName = ["dev"]

    # Link branches to repository
    test_repo.hasBranch = [branch_main, branch_dev]
    branch_main.belongsTo = [test_repo]
    branch_dev.belongsTo = [test_repo]

    # --- Users ---
    user_alice = onto.User("alice_user")
    user_alice.hasName = ["Alice"]
    user_bob = onto.User("bob_user")
    user_bob.hasName = ["Bob"]

    # --- Files ---
    file1 = onto.File("file_models")
    file1.hasName = ["models.py"]
    file2 = onto.File("file_views")
    file2.hasName = ["views.py"]
    test_repo.containsFile = [file1, file2]

    # --- Commits ---
    c1 = onto.Commit("commit_001")
    c1.hasName = ["Initial Commit"]
    c1.message = ["Added project structure"]
    c1.timestamp = [datetime(2023, 1, 1, 10, 0, 0)]
    c1.authoredBy = [user_alice]
    c1.updatesFile = [file1, file2]
    c1.onBranch = [branch_main]

    c2 = onto.Commit("commit_002")
    c2.hasName = ["Feature Add"]
    c2.message = ["Implemented login feature"]
    c2.timestamp = [datetime(2023, 1, 5, 12, 30, 0)]
    c2.authoredBy = [user_bob]
    c2.parent = [c1]
    c2.onBranch = [branch_dev]

    c3 = onto.Commit("commit_003")
    c3.hasName = ["Merge Feature"]
    c3.message = ["Merged dev into main"]
    c3.timestamp = [datetime(2023, 1, 6, 9, 45, 0)]
    c3.authoredBy = [user_alice]
    c3.parent = [c1, c2]   # Two parents → merge commit
    c3.onBranch = [branch_main]

    # Link initial commit to branch
    branch_main.initialCommit = [c1]
    branch_dev.initialCommit = [c1]


# -------------------------------------------------------
# Basic functions
# -------------------------------------------------------

def list_repositories():
    """List all repositories in ontology."""
    print("\n=== Repositories ===")
    for repo in onto.Repository.instances():
        if hasattr(repo, "hasName") and repo.hasName:
            print(f"- {repo.hasName[0]}")
    print("--------------------")

def commits_by_author(author_name):
    """List commits authored by a specific user."""
    print(f"\n=== Commits by {author_name} ===")
    found = False
    for commit in onto.Commit.instances():
        if hasattr(commit, "authoredBy") and commit.authoredBy:
            author = commit.authoredBy[0]
            if hasattr(author, "hasName") and author.hasName and author.hasName[0].lower() == author_name.lower():
                print(f"- {commit.message[0] if hasattr(commit, 'message') else '(no message)'}")
                found = True
    if not found:
        print("No commits found for that author.")
    print("--------------------")

def find_merge_commits():
    """Identify merge commits (commits with >1 parent)."""
    print("\n=== Merge Commits ===")
    found = False
    for commit in onto.Commit.instances():
        if hasattr(commit, "parent") and len(commit.parent) > 1:
            print(f"- {commit.name}")
            found = True
    if not found:
        print("No merge commits detected.")
    print("--------------------")

# -------------------------------------------------------
# Extended functionality
# -------------------------------------------------------

def list_branches(repo_name):
    """List branches for a specific repository."""
    print(f"\n=== Branches in {repo_name} ===")
    found = False
    for branch in onto.Branch.instances():
        if hasattr(branch, "belongsTo") and branch.belongsTo:
            repo = branch.belongsTo[0]
            if hasattr(repo, "hasName") and repo.hasName and repo.hasName[0].lower() == repo_name.lower():
                print(f"- {branch.hasName[0] if hasattr(branch, 'hasName') else branch.name}")
                found = True
    if not found:
        print("No branches found or repository name invalid.")
    print("--------------------")

def show_inferred_classes():
    """Display ontology-inferred classes."""
    print("\n=== Inferred Classes ===")
    print("\n-- MergeCommits --")
    for commit in onto.MergeCommit.instances():
        print(f"- {commit.name}")
    print("\n-- InitialCommits --")
    for commit in onto.InitialCommit.instances():
        print(f"- {commit.name}")
    print("--------------------")

def search_commit_keyword(keyword):
    """Search commit messages containing a given keyword."""
    print(f"\n=== Searching for '{keyword}' in commit messages ===")
    found = False
    for commit in onto.Commit.instances():
        if hasattr(commit, "message") and commit.message and keyword.lower() in commit.message[0].lower():
            print(f"- {commit.message[0]}")
            found = True
    if not found:
        print("No commits contain that keyword.")
    print("--------------------")

def validate_ontology():
    """Identify ontology inconsistencies (missing data)."""
    print("\n=== Ontology Validation ===")
    for repo in onto.Repository.instances():
        if not getattr(repo, "hasBranch", None):
            print(f"Warning: Repository '{repo.name}' has no branches.")
    for commit in onto.Commit.instances():
        if not getattr(commit, "authoredBy", None):
            print(f"Warning: Commit '{commit.name}' has no author.")
    print("Validation complete.")
    print("--------------------")

def run_sparql_query():
    """Run custom SPARQL queries directly."""
    print("\n=== SPARQL Query Interface ===")
    g = Graph()
    g.parse("ontology/git-onto-logic.owl")
    query = input("Enter SPARQL query:\n> ")
    try:
        results = g.query(query)
        for row in results:
            print(row)
    except Exception as e:
        print(f"Error executing query: {e}")
    print("--------------------")

# -------------------------------------------------------
# CLI Main Menu
# -------------------------------------------------------

def main():
    print("Welcome to Git-Onto-Logic CLI")
    while True:
        print("\nCommands:")
        print("1 - List Repositories")
        print("2 - List Branches in a Repository")
        print("3 - Find Merge Commits")
        print("4 - Show Inferred Classes")
        print("5 - Search Commits by Keyword")
        print("6 - Query Commits by Author")
        print("7 - Validate Ontology")
        print("8 - Run SPARQL Query")
        print("9 - Exit")

        choice = input("> ").strip()

        if choice == "1":
            list_repositories()
        elif choice == "2":
            repo = input("Enter repository name: ")
            list_branches(repo)
        elif choice == "3":
            find_merge_commits()
        elif choice == "4":
            show_inferred_classes()
        elif choice == "5":
            keyword = input("Enter keyword: ")
            search_commit_keyword(keyword)
        elif choice == "6":
            author = input("Enter author name: ")
            commits_by_author(author)
        elif choice == "7":
            validate_ontology()
        elif choice == "8":
            run_sparql_query()
        elif choice == "9":
            print("Exiting Git-Onto-Logic CLI.")
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
