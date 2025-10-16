from flask import Flask, render_template, request
from ontology.ontology_v1 import onto
from rdflib import Graph

app = Flask(__name__)

# Load ontology once
onto.load(file="ontology/git-onto-logic.owl")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/repositories')
def list_repositories():
    repos = []
    for repo in onto.Repository.instances():
        if hasattr(repo, "hasName") and repo.hasName:
            repos.append(repo.hasName[0])
    return render_template('repositories.html', repos=repos)

@app.route('/commits')
def commits_by_author():
    author_name = request.args.get('author', '').lower()
    commits = []
    for commit in onto.Commit.instances():
        if hasattr(commit, "authoredBy") and commit.authoredBy:
            author = commit.authoredBy[0]
            if hasattr(author, "hasName") and author.hasName and author.hasName[0].lower() == author_name:
                commits.append(commit.message[0])
    return render_template('commits.html', author=author_name, commits=commits)

@app.route('/search')
def search_commit_keyword():
    keyword = request.args.get('keyword', '').lower()
    matches = []
    for commit in onto.Commit.instances():
        if hasattr(commit, "message") and commit.message and keyword in commit.message[0].lower():
            matches.append(commit.message[0])
    return render_template('search.html', keyword=keyword, results=matches)

if __name__ == '__main__':
    app.run(debug=True)
