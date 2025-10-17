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
            # Use readable branchName if it exists
            display_name = val(getattr(b, "branchName", None)) or b.name
            branches.append(display_name)
    print(f"[DEBUG] Repo: {name}, hasBranch: {getattr(repo, 'hasBranch', None)}")
    return render_template("branches.html", repo=name, branches=sorted(branches))


@bp.route("/repository/<path:repo>/branch/<path:branch>")
def view_branch_commits(repo, branch):
    """Display commits belonging to a specific branch of a repository."""
    branch_str = branch.strip().lower()

    # 1) find the repo object by repoName
    repo_obj = next(
        (r for r in onto.Repository.instances()
         if hasattr(r, "repoName") and val(r.repoName).lower() == repo.lower()),
        None
    )
    if not repo_obj:
        return render_template("commits.html", branch=branch, commits=[], repo=repo)

    # 2) find the target branch *inside this repo only*
    target_branch = None
    for b in getattr(repo_obj, "hasBranch", []):
        b_display = val(getattr(b, "branchName", None))
        if (b_display and b_display.lower() == branch_str) or b.name.lower() == branch_str:
            target_branch = b
            break

    if not target_branch:
        # Branch not found under this repo
        return render_template("commits.html", branch=branch, commits=[], repo=repo)

    # 3) gather commits:
    #    - commits directly attached via hasCommit
    #    - commits that reference this branch via onBranch
    #    - keep only commits that are associated with this repo (their onBranch contains a branch in repo_obj.hasBranch)
    linked = set(getattr(target_branch, "hasCommit", []))

    # include commits that reference this branch via onBranch
    for c in onto.Commit.instances():
        if target_branch in getattr(c, "onBranch", []):
            linked.add(c)

    # repo-level filter (commit must be on at least one branch of the current repo)
    repo_branches = set(getattr(repo_obj, "hasBranch", []))
    linked = [c for c in linked if repo_branches.intersection(set(getattr(c, "onBranch", [])))]

    # 4) convert to view-model
    commits = []
    for c in linked:
        msg = val(getattr(c, "message", "(no message)"))
        author = val(getattr(c.authoredBy[0], "userLogin", "(unknown)")) if getattr(c, "authoredBy", None) else "(unknown)"
        label = "Initial" if getattr(c, "isInitial", [False])[0] else ""
        commits.append({
            "message": msg,
            "author": author,
            "label": label,
            "timestamp": val(getattr(c, "commitDate", ""))
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
