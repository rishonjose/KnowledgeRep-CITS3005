from flask import render_template, request, jsonify
from app import app
from app.ontology_service import OntologyService
from urllib.parse import unquote

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