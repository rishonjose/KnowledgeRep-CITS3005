from owlready2 import *
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery

class OntologyService:
    def __init__(self):
        # Load the populated ontology
        self.onto = get_ontology("outputs/populated.owl").load()
        
        # Convert to RDFlib graph for SPARQL queries
        self.graph = Graph()
        self.graph.parse("outputs/populated.owl", format="xml")
        
        # Define namespaces
        self.ns = Namespace("http://example.org/git-onto-logic#")
        self.graph.bind("", self.ns)  # Bind the default namespace
        
        # Debug: Print graph size
        print(f"DEBUG: Loaded RDF graph with {len(self.graph)} triples")
        
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
        """Find all commits by a specific user, or all commits if no username is provided"""
        query = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?repo ?branch
        WHERE {
            ?user :userLogin ?username .
            ?commit :authoredBy ?user ;
                   :message ?message ;
                   :commitDate ?date ;
                   :onBranch ?branch .
            ?branch :branchName ?branchName ;
                    ^:hasBranch ?repository .
            ?repository :repoName ?repo .
            %s
        }
        ORDER BY DESC(?date)
        LIMIT 50
        """ % (f'FILTER(?username = "{username}")' if username else '')
        
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
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?username ?url
        WHERE {
            ?user a :ConcurrentContributor ;
                  :userLogin ?username ;
                  :userURL ?url .
        }
        LIMIT 50
        """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'username': str(row.username),
                'url': str(row.url)
            })
        return results

    def _get_merge_commits(self, repository):
        """Find all merge commits in a repository, or all merge commits if no repository is provided"""
        query = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?branch
        WHERE {
            ?repository :repoName ?repoName ;
                       :hasBranch ?branch .
            ?branch :hasCommit ?commit .
            ?commit a :MergeCommit ;
                    :message ?message ;
                    :commitDate ?date .
            %s
        }
        ORDER BY DESC(?date)
        LIMIT 50
        """ % (f'FILTER(?repoName = "{repository}")' if repository else '')
        
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
        """Find commits with security/vulnerability messages in a branch, or all security commits if no branch is provided"""
        query = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?commit ?message ?date ?user
        WHERE {
            ?commit a :SecurityCommit ;
                    :message ?message ;
                    :commitDate ?date ;
                    :authoredBy ?user ;
                    :onBranch ?branchObj .
            ?user :userLogin ?userLogin .
            ?branchObj :branchName ?branch .
            %s
        }
        ORDER BY DESC(?date)
        LIMIT 50
        """ % (f'FILTER(?branch = "{branch}")' if branch else '')
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'commit': str(row.commit).split('#')[-1],
                'message': str(row.message),
                'date': str(row.date),
                'user': str(row.user).split('#')[-1]
            })
        return results

    def get_all_repositories(self):
        """Get all repositories in the knowledge graph"""
        query = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?repoName ?description ?url (COUNT(?commit) as ?commitCount)
        WHERE {
            ?repo a :Repository ;
                  :repoName ?repoName ;
                  :hasBranch ?branch .
            ?branch :hasCommit ?commit .
            OPTIONAL { ?repo :description ?description }
            OPTIONAL { ?repo :repoURL ?url }
        }
        GROUP BY ?repoName ?description ?url
        ORDER BY ?repoName
        """
        
        results = []
        for row in self.graph.query(query):
            commit_count = int(row.commitCount) if row.commitCount else 0
            print(f"Debug: Repository {row.repoName} has {commit_count} commits")
            results.append({
                'name': str(row.repoName),
                'description': str(row.description) if row.description else None,
                'url': str(row.url) if row.url else None
            })
        return results

    def get_repository_branches(self, repo_name):
        """Get all branches for a specific repository"""
        query = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?branch ?branchName (COUNT(?commit) as ?commitCount)
        WHERE {
            ?repo a :Repository ;
                  :repoName ?repoName ;
                  :hasBranch ?branch .
            ?branch :branchName ?branchName .
            OPTIONAL {
                ?branch :hasCommit ?commit .
            }
            FILTER(?repoName = "%s")
        }
        GROUP BY ?branch ?branchName
        ORDER BY ?branchName
        """ % repo_name
        
        results = []
        for row in self.graph.query(query):
            commit_count = 0
            if row.commitCount is not None:
                commit_count = int(row.commitCount)
            
            print(f"Debug: Found branch {row.branchName} with {commit_count} commits")
            results.append({
                'name': str(row.branchName),
                'commit_count': commit_count
            })
        return results

    def get_branch_commits(self, repo_name, branch_name):
        """Get all commits for a specific branch in a repository"""
        print(f"\nDEBUG INFORMATION:")
        print(f"Looking for commits in: repo='{repo_name}', branch='{branch_name}'")
        
        # First, find the repository ID
        repo_query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT ?repoId
        WHERE {
            ?repo a git:Repository ;
                  git:repoName "%s" .
            BIND(STRAFTER(STR(?repo), "#repo_") AS ?repoId)
        }
        LIMIT 1
        """ % repo_name
        
        repo_results = list(self.graph.query(repo_query))
        if not repo_results:
            print("DEBUG: Could not find the repository ID")
            return []
            
        repo_id = repo_results[0].repoId
        print(f"DEBUG: Found repository ID: {repo_id}")
        
        # Now construct the branch IRI directly
        sanitized_branch = re.sub(r'[^A-Za-z0-9_]', '_', branch_name).strip('_')
        branch_iri = f"repo_{repo_id}__branch_{sanitized_branch}"
        print(f"DEBUG: Constructed branch IRI: {branch_iri}")
            
    def get_branch_commits(self, repo_name, branch_name):
        """Get all commits for a specific branch in a repository"""
        print(f"\nDEBUG INFORMATION:")
        print(f"Looking for commits in: repo='{repo_name}', branch='{branch_name}'")
        # Step 1: Resolve the exact Branch IRI for this repo + branch name
        resolve_q = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?branch
        WHERE {
            ?repo a :Repository ;
                  :repoName ?rn ;
                  :hasBranch ?branch .
            ?branch :branchName ?bn .
            FILTER(?rn = "%s" && ?bn = "%s")
        }
        LIMIT 1
        """ % (repo_name, branch_name)

        branch_uri = None
        for row in self.graph.query(resolve_q):
            branch_uri = str(row.branch)
            break

        if not branch_uri:
            print("DEBUG: Could not resolve branch IRI from repo+branch name")
            return []

        print(f"DEBUG: Resolved branch IRI: {branch_uri}")

        # Step 2: Fetch commits for that branch (match either via hasCommit or onBranch)
        commit_q = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT DISTINCT ?sha ?message ?date ?author
        WHERE {
            VALUES ?branch { <%s> }
            { ?branch :hasCommit ?commit . }
            UNION
            { ?commit :onBranch ?branch . }
            ?commit :commitSHA ?sha ;
                    :message ?message ;
                    :commitDate ?date .
            OPTIONAL {
                ?commit :authoredBy ?a .
                ?a :userLogin ?author .
            }
        }
        ORDER BY DESC(?date)
        """ % branch_uri

        results = []
        for row in self.graph.query(commit_q):
            results.append({
                'id': str(row.sha),
                'message': str(row.message),
                'date': str(row.date),
                'author': str(row.author) if row.author else "Unknown"
            })

        print(f"DEBUG: Found {len(results)} commits for branch {branch_uri}")
        return results
        
        results = []
        query = """
        PREFIX git: <http://example.org/git-onto-logic#>
        SELECT DISTINCT ?sha ?message ?date ?author
        WHERE {
            ?branch git:hasCommit ?commit .
            ?commit git:commitSHA ?sha ;
                   git:message ?message ;
                   git:commitDate ?date .
            OPTIONAL {
                ?commit git:authoredBy ?author_obj .
                ?author_obj git:userLogin ?author .
            }
            FILTER(STR(?branch) = CONCAT(STR(git:), "%s"))
        }
        ORDER BY DESC(?date)
        """ % branch_iri

        print(f"\nDEBUG: Executing query for branch IRI: {branch_iri}")
        for row in self.graph.query(query):
            print(f"DEBUG: Found commit {row.sha}")
            results.append({
                'id': str(row.sha),
                'message': str(row.message),
                'date': str(row.date),
                'author': str(row.author) if row.author else "Unknown"
            })

        if not results:
            print(f"\nDEBUG: No commits found for branch IRI: {branch_iri}")
            
            # Verify the branch exists
            verify_query = """
            PREFIX git: <http://example.org/git-onto-logic#>
            SELECT ?branch ?branchName (COUNT(?commit) as ?commitCount)
            WHERE {
                ?branch a git:Branch ;
                        git:branchName ?branchName .
                OPTIONAL { ?branch git:hasCommit ?commit }
                FILTER(STR(?branch) = CONCAT(STR(git:), "%s"))
            }
            GROUP BY ?branch ?branchName
            """ % branch_iri
            
            print("\nDEBUG: Verifying branch existence:")
            for row in self.graph.query(verify_query):
                print(f"Branch URI: {row.branch}")
                print(f"Branch name: {row.branchName}")
                print(f"Commit count: {row.commitCount}")

        return results