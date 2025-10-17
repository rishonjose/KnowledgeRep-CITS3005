from flask import Blueprint, render_template, request
from owlready2 import get_ontology
import os

bp = Blueprint("routes", __name__)

# --------------------------------------------------------------
# Load the populated ontology once at startup
# --------------------------------------------------------------
ONTOLOGY_PATH = os.path.join(os.path.dirname(__file__), "../ontology/git-onto-logic-populated.owl")
ONTOLOGY_PATH = os.path.abspath(ONTOLOGY_PATH)
onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

def val(prop):
    """Return a consistent single value whether the property is a list or a scalar."""
    if isinstance(prop, list):
        return prop[0] if prop else None
    return prop


# --------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------

@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/repositories")
def repositories():
    """Display all repositories in the ontology."""
    repos = sorted([
        val(getattr(r, "repoName", None))
        for r in onto.Repository.instances()
        if hasattr(r, "repoName")
    ])
    return render_template("repositories.html", repos=repos)


@bp.route("/repository/<path:name>")
def view_repository(name):
    """Display branches belonging to a selected repository."""
    repo = next(
        (r for r in onto.Repository.instances()
         if hasattr(r, "repoName") and val(r.repoName).lower() == name.lower()),
        None
    )
    branches = []
    if repo:
        for b in getattr(repo, "hasBranch", []):
            branch_name = val(getattr(b, "hasName", None)) or b.name
            branches.append(branch_name)
    print(f"[DEBUG] Repo: {name}, hasBranch: {getattr(repo, 'hasBranch', None)}")
    return render_template("branches.html", repo=name, branches=sorted(branches))


@bp.route("/repository/<path:repo>/branch/<branch>")
def view_branch_commits(repo, branch):
    """Display commits belonging to a specific branch of a repository."""
    commits = []
    for b in onto.Branch.instances():
        if hasattr(b, "hasName") and val(b.hasName).lower() == branch.lower():
            for c in getattr(b, "hasCommit", []):
                msg = val(getattr(c, "message", "(no message)"))
                author = val(getattr(c.authoredBy[0], "userLogin", "(unknown)")) if getattr(c, "authoredBy", None) else "(unknown)"
                label = (
                    "Merge" if c in onto.MergeCommit.instances()
                    else "Initial" if c in onto.InitialCommit.instances()
                    else "Security" if c in onto.SecurityCommit.instances()
                    else ""
                )
                commits.append({
                    "message": msg,
                    "author": author,
                    "label": label,
                    "timestamp": val(getattr(c, "timestamp", ""))
                })
    commits.sort(key=lambda x: x["timestamp"], reverse=True)
    return render_template("commits.html", branch=branch, commits=commits, repo=repo)


@bp.route("/authors")
def authors():
    """List all authors and their commit counts."""
    authors = []
    for a in onto.User.instances():
        name = val(getattr(a, "userLogin", "(unknown)"))
        count = sum(
            1 for c in onto.Commit.instances()
            if getattr(c, "authoredBy", None) and c.authoredBy[0] == a
        )
        authors.append({"name": name, "count": count})
    return render_template("author.html", authors=sorted(authors, key=lambda x: x["name"]))


@bp.route("/sparql", methods=["GET", "POST"])
def sparql():
    """Run SPARQL queries directly on the already-loaded ontology."""
    results, query, error = [], "", None
    if request.method == "POST":
        query = request.form["query"].strip()
        if query:
            try:
                g = onto.world.as_rdflib_graph()
                results = [row for row in g.query(query)]
            except Exception as e:
                error = f"SPARQL error: {e.__class__.__name__} – {str(e)}"
        else:
            error = "Query cannot be empty."
    return render_template("sparql.html", query=query, results=results, error=error)


@bp.route("/validate")
def validate():
    """Perform simple consistency checks on ontology instances."""
    warnings = []
    for repo in onto.Repository.instances():
        if not getattr(repo, "hasBranch", []):
            warnings.append(f"Repository '{val(repo.repoName)}' has no branches.")
    for commit in onto.Commit.instances():
        if not getattr(commit, "authoredBy", []):
            warnings.append(f"Commit '{val(getattr(commit, 'message', '(unnamed)'))}' missing author.")
    return render_template("validate.html", warnings=warnings)
