from owlready2 import *
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery

class OntologyService:
    def __init__(self):
        # Load the populated ontology
        self.onto = get_ontology("outputs/populated.owl").load()
        
        # Convert to RDFlib graph for SPARQL queries
        self.graph = Graph()
        self.graph.parse("outputs/populated.owl")
        
        # Define namespaces
        self.ns = Namespace("http://example.org/git-onto-logic#")
        
    def execute_query(self, query_type, parameters):
        """Execute different types of SPARQL queries based on the query type"""
        if query_type == "user_commits":
            return self._get_user_commits(parameters['user'])
        elif query_type == "concurrent_contributors":
            return self._get_concurrent_contributors()
        elif query_type == "merge_commits":
            return self._get_merge_commits(parameters['repository'])
        elif query_type == "security_commits":
            return self._get_security_commits(parameters['branch'])
        return []
    
    def _get_user_commits(self, username):
        """Find all commits by a specific user"""
        query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?repo ?branch
        WHERE {
            ?user git:userLogin ?username .
            ?commit git:authoredBy ?user ;
                   git:message ?message ;
                   git:commitDate ?date ;
                   git:onBranch ?branch .
            ?branch git:branchName ?branchName ;
                    ^git:hasBranch ?repository .
            ?repository git:repoName ?repo .
            FILTER(?username = "%s")
        }
        ORDER BY DESC(?date)
        """ % username
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'commit': str(row.commit).split('#')[-1],
                'message': str(row.message),
                'date': str(row.date),
                'repository': str(row.repo),
                'branch': str(row.branch).split('#')[-1]
            })
        return results

    def _get_concurrent_contributors(self):
        """Find users who have made concurrent contributions to three or more repositories"""
        query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT ?username ?url
        WHERE {
            ?user a git:ConcurrentContributor ;
                  git:userLogin ?username ;
                  git:userURL ?url .
        }
        """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'username': str(row.username),
                'url': str(row.url)
            })
        return results

    def _get_merge_commits(self, repository):
        """Find all merge commits in a repository"""
        query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?branch
        WHERE {
            ?repository git:repoName ?repoName ;
                       git:hasBranch ?branch .
            ?branch git:hasCommit ?commit .
            ?commit a git:MergeCommit ;
                    git:message ?message ;
                    git:commitDate ?date .
            FILTER(?repoName = "%s")
        }
        ORDER BY DESC(?date)
        """ % repository
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'commit': str(row.commit).split('#')[-1],
                'message': str(row.message),
                'date': str(row.date),
                'branch': str(row.branch).split('#')[-1]
            })
        return results

    def _get_security_commits(self, branch):
        """Find commits with security/vulnerability messages in a branch"""
        query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?user
        WHERE {
            ?commit a git:SecurityCommit ;
                    git:message ?message ;
                    git:commitDate ?date ;
                    git:authoredBy ?user ;
                    git:onBranch ?branchObj .
            ?user git:userLogin ?userLogin .
            ?branchObj git:branchName ?branch .
            FILTER(?branch = "%s")
        }
        ORDER BY DESC(?date)
        """ % branch
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'commit': str(row.commit).split('#')[-1],
                'message': str(row.message),
                'date': str(row.date),
                'user': str(row.user).split('#')[-1]
            })
        return results