# app_cli.py
from ontology.ontology_v1 import onto
from rdflib import Graph

onto.load(file="ontology/git-onto-logic.owl")

with onto:
    test_repo = onto.Repository("repo_test")
    test_repo.hasName = ["Guild Volunteering"]

def list_repositories():
    for repo in onto.Repository.instances():
        print(f"{repo.hasName[0]}")

def commits_by_author(author_name):
    for commit in onto.Commit.instances():
        if commit.authoredBy and commit.authoredBy[0].hasName[0].lower() == author_name.lower():
            print(commit.message[0])

def find_merge_commits():
    for commit in onto.Commit.instances():
        if len(commit.parent) > 1:
            print(f"Merge commit: {commit.hasName[0]}")

def main():
    print("Welcome to Git-Onto-Logic CLI")
    while True:
        print("\nCommands:")
        print("1 - List Repositories")
        print("2 - Find Merge Commits")
        print("3 - Query Commits by Author")
        print("4 - Exit")

        choice = input("> ")

        if choice == "1":
            list_repositories()
        elif choice == "2":
            find_merge_commits()
        elif choice == "3":
            author = input("Enter author name: ")
            commits_by_author(author)
        elif choice == "4":
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
