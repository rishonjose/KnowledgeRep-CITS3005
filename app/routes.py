from flask import render_template, request, jsonify
from app import app
from app.ontology_service import OntologyService

ontology_service = OntologyService()

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

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
        return render_template('results.html', results=results)
    
    return render_template('search.html')