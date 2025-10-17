from flask import Blueprint, render_template, request
from owlready2 import get_ontology
from rdflib import Graph
import os

bp = Blueprint("routes", __name__)

# --------------------------------------------------------------
# Load the populated ontology once at startup
# --------------------------------------------------------------
ONTOLOGY_PATH = os.path.join(os.path.dirname(__file__), "../ontology/git-onto-logic-populated.owl")
ONTOLOGY_PATH = os.path.abspath(ONTOLOGY_PATH)

# Load ontology directly from local file
onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

# Helper function to safely extract property values
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
    repos = [val(r.hasName) for r in onto.Repository.instances() if hasattr(r, "hasName")]
    return render_template("repositories.html", repos=repos)


@bp.route("/repository/<name>")
def view_repository(name):
    """Display branches belonging to a selected repository."""
    repo = next(
        (r for r in onto.Repository.instances()
         if hasattr(r, "hasName") and val(r.hasName).lower() == name.lower()),
        None
    )
    branches = [val(b.hasName) for b in getattr(repo, "hasBranch", [])] if repo else []
    return render_template("branches.html", repo=name, branches=branches)


@bp.route("/commits/<branch>")
def commits(branch):
    """Show commits associated with a given branch, with inferred labels."""
    commits = []
    repo_name = None

    for b in onto.Branch.instances():
        if hasattr(b, "hasName") and val(b.hasName).lower() == branch.lower():
            # If ontology has repository linkage, extract it
            if hasattr(b, "belongsTo") and b.belongsTo:
                repo_name = val(b.belongsTo[0].hasName)

            for c in getattr(b, "hasCommit", []):
                msg = val(getattr(c, "message", "(no message)"))
                author = val(c.authoredBy[0].hasName) if hasattr(c, "authoredBy") and c.authoredBy else "(unknown)"
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

    return render_template("commits.html", branch=branch, commits=commits, repo=repo_name)


@bp.route("/authors")
def authors():
    """List all authors and their commit counts."""
    authors = []
    for a in onto.User.instances():
        name = val(getattr(a, "hasName", "(unknown)"))
        count = sum(
            1 for c in onto.Commit.instances()
            if hasattr(c, "authoredBy") and c.authoredBy and c.authoredBy[0] == a
        )
        authors.append({"name": name, "count": count})
    return render_template("author.html", authors=authors)


@bp.route("/issues")
def issues():
    """List all issues and their metadata."""
    issues = []
    for i in onto.Issue.instances():
        issues.append({
            "name": val(getattr(i, "hasName", "(unnamed)")),
            "status": val(getattr(i, "status", "unknown")),
            "opened_by": val(i.openedBy[0].hasName) if hasattr(i, "openedBy") and i.openedBy else "(unknown)",
            "assigned_to": val(i.assignedTo[0].hasName) if hasattr(i, "assignedTo") and i.assignedTo else "(unassigned)"
        })
    return render_template("issues.html", issues=issues)


@bp.route("/pulls")
def pulls():
    """List all pull requests and their metadata."""
    pulls = []
    for p in onto.PullRequest.instances():
        pulls.append({
            "name": val(getattr(p, "hasName", "(unnamed)")),
            "status": val(getattr(p, "status", "unknown")),
            "opened_by": val(p.openedBy[0].hasName) if hasattr(p, "openedBy") and p.openedBy else "(unknown)",
            "merged_by": val(p.mergedBy[0].hasName) if hasattr(p, "mergedBy") and p.mergedBy else "(none)"
        })
    return render_template("pulls.html", pulls=pulls)


@bp.route("/sparql", methods=["GET", "POST"])
def sparql():
    """Run SPARQL queries directly on the already-loaded ontology."""
    results, query, error = [], "", None
    if request.method == "POST":
        query = request.form["query"].strip()
        if query:
            try:
                # Reuse loaded ontology’s graph (no need to rebuild)
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
        if not getattr(repo, "hasBranch", None):
            warnings.append(f"Repository '{val(repo.hasName)}' has no branches.")
    for commit in onto.Commit.instances():
        if not getattr(commit, "authoredBy", None):
            warnings.append(f"Commit '{val(commit.hasName)}' missing author.")
    return render_template("validate.html", warnings=warnings)
