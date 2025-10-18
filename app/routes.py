from flask import render_template, request, jsonify
from app import app
from app.ontology_service import OntologyService
from urllib.parse import unquote
import os
from rdflib import Graph
from pyshacl import validate

ontology_service = OntologyService()

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/browse/repos')
def browse_repos():
    """Display all repositories"""
    repos = ontology_service.get_all_repositories()
    return render_template('browse_repos.html', repos=repos)

@app.route('/browse/repo/<path:repo_name>/branches')
def browse_branches(repo_name):
    """Display all branches for a repository"""
    repo_name = unquote(repo_name)
    branches = ontology_service.get_repository_branches(repo_name)
    return render_template('browse_branches.html', branches=branches, repo_name=repo_name)

@app.route('/browse/repo/<path:repo_name>/branch/<path:branch_name>/commits')
def browse_commits(repo_name, branch_name):
    """Display all commits for a branch"""
    repo_name = unquote(repo_name)
    branch_name = unquote(branch_name)
    commits = ontology_service.get_branch_commits(repo_name, branch_name)
    return render_template('browse_commits.html', commits=commits, repo_name=repo_name, branch_name=branch_name)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search interface route"""
    if request.method == 'POST':
        query_type = request.form.get('query_type')
        parameters = {
            'user': request.form.get('user', ''),
            'repository': request.form.get('repository', ''),
            'branch': request.form.get('branch', ''),
            'keyword': request.form.get('keyword', '')
        }
        
        results = ontology_service.execute_query(query_type, parameters)
        return render_template('results.html', results=results, request=request)
    
    return render_template('search.html')

@app.route('/validate', methods=['GET'])
def validate_graph():
    """Run SHACL validation and display the results."""
    try:
        # Determine project root from this file location (app/routes.py -> project root)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # Paths relative to project root
        data_file = os.path.join(project_root, 'outputs', 'populated.owl')
        shapes_file = os.path.join(project_root, 'ontology', 'shapes.ttl')
        report_file = os.path.join(project_root, 'outputs', 'SHACL_REPORT.txt')

        # Load graphs
        data_g = Graph().parse(data_file, format='xml')
        shapes_g = Graph().parse(shapes_file, format='turtle')

        # Run validation
        conforms, report_graph, report_text = validate(
            data_graph=data_g,
            shacl_graph=shapes_g,
            inference='rdfs',
            abort_on_first=False,
            meta_shacl=False,
            debug=False
        )

        # Persist the report to disk to match CLI behavior
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w') as f:
            f.write(report_text)

        return render_template(
            'validation_results.html',
            conforms=conforms,
            report_text=report_text,
            data_file_display=os.path.relpath(data_file, project_root),
            shapes_file_display=os.path.relpath(shapes_file, project_root),
            report_file_display=os.path.relpath(report_file, project_root),
        )
    except Exception as e:
        return render_template(
            'validation_results.html',
            conforms=None,
            report_text=str(e),
            data_file_display='outputs/populated.owl',
            shapes_file_display='ontology/shapes.ttl',
            report_file_display='outputs/SHACL_REPORT.txt',
        ), 500

@app.route('/sparql', methods=['GET', 'POST'])
def run_sparql():
    """Render a page to run custom SPARQL queries and display results."""
    query_text = None
    result = None
    error = None

    if request.method == 'POST':
        query_text = (request.form.get('query') or '').strip()
        if not query_text:
            error = 'Please enter a SPARQL query.'
        else:
            try:
                result = ontology_service.run_custom_sparql(query_text)
            except Exception as e:
                error = str(e)

    # Provide a handy sample for initial load
    sample_query = """
PREFIX : <http://example.org/git-onto-logic#>
SELECT ?repoName ?branchName ?sha
WHERE {
  ?repo a :Repository ;
        :repoName ?repoName ;
        :hasBranch ?branch .
  ?branch :branchName ?branchName ;
          :hasCommit ?commit .
  ?commit :commitSHA ?sha .
}
LIMIT 10
""".strip()

    if not query_text:
        query_text = sample_query

    return render_template(
        'run_sparql.html',
        query_text=query_text,
        result=result,
        error=error,
    )