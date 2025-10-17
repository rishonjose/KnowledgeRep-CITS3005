from flask import Blueprint, render_template, request
from ontology.ontology_v1 import onto
from rdflib import Graph

bp = Blueprint("routes", __name__)

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

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/repositories")
def repositories():
    repos = [r.hasName[0] for r in onto.Repository.instances() if hasattr(r, "hasName")]
    return render_template("repositories.html", repos=repos)

@bp.route("/repository/<name>")
def view_repository(name):
    branches = []
    for b in onto.Branch.instances():
        if hasattr(b, "belongsTo") and b.belongsTo and b.belongsTo[0].hasName[0].lower() == name.lower():
            branches.append(b.hasName[0])
    return render_template("branches.html", repo=name, branches=branches)

@bp.route("/commits/<branch>")
def commits(branch):
    commits = []
    repo_name = None
    for c in onto.Commit.instances():
        if hasattr(c, "onBranch") and c.onBranch and c.onBranch[0].hasName[0].lower() == branch.lower():
            b = c.onBranch[0]
            if hasattr(b, "belongsTo") and b.belongsTo:
                repo_name = b.belongsTo[0].hasName[0]
            msg = c.message[0] if hasattr(c, "message") else "(no message)"
            author = c.authoredBy[0].hasName[0] if hasattr(c, "authoredBy") and c.authoredBy else "(unknown)"
            label = "Merge" if c in onto.MergeCommit.instances() else "Initial" if c in onto.InitialCommit.instances() else ""
            commits.append({"message": msg, "author": author, "label": label})
    return render_template("commits.html", branch=branch, commits=commits, repo=repo_name)

@bp.route("/authors")
def authors():
    authors = []
    for a in onto.User.instances():
        name = a.hasName[0]
        count = sum(1 for c in onto.Commit.instances() if c.authoredBy and c.authoredBy[0] == a)
        authors.append({"name": name, "count": count})
    return render_template("author.html", authors=authors)

@bp.route("/sparql", methods=["GET", "POST"])
def sparql():
    results = []
    query = ""
    error = None

    if request.method == "POST":
        query = request.form["query"].strip()
        if query:
            try:
                g = Graph()
                g.parse("ontology/git-onto-logic.owl")
                results = [row for row in g.query(query)]
            except Exception as e:
                error = f"SPARQL error: {e.__class__.__name__} – {str(e)}"
        else:
            error = "Query cannot be empty."

    return render_template("sparql.html", query=query, results=results, error=error)

@bp.route("/validate")
def validate():
    warnings = []
    for repo in onto.Repository.instances():
        if not getattr(repo, "hasBranch", None):
            warnings.append(f"Repository '{repo.name}' has no branches.")
    for commit in onto.Commit.instances():
        if not getattr(commit, "authoredBy", None):
            warnings.append(f"Commit '{commit.name}' missing author.")
    return render_template("validate.html", warnings=warnings)
