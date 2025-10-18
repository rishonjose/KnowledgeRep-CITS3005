from owlready2 import *
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
import re

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
    
    def _escape_sparql_string(self, value: str) -> str:
        """Escape a Python string for safe inclusion as a SPARQL string literal.
        Escapes backslashes and double quotes; leaves other characters intact.
        """
        if value is None:
            return ""
        return value.replace("\\", "\\\\").replace('"', '\\"')
        
    def _resolve_repo_iri(self, repo_input: str):
        """Resolve a repository IRI from user input robustly.
        Tries in order: exact (case-insensitive), ownerless suffix match, then contains.
        Returns (repo_iri, matched_name) or (None, None).
        """
        esc = self._escape_sparql_string(repo_input)
        # 1) Exact (case-insensitive)
        q1 = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?repo ?rn
        WHERE {
            ?repo a :Repository ;
                  :repoName ?rn .
            FILTER(LCASE(?rn) = LCASE("%s"))
        }
        LIMIT 1
        """ % esc

        for row in self.graph.query(q1):
            return str(row.repo), str(row.rn)

        # 2) Ownerless suffix match: .../repo_input (case-insensitive)
        # Only attempts if input doesn't look like owner/repo
        if "/" not in repo_input:
            # Use STRENDS with CONCAT to avoid regex and special escaping problems
            q2 = """
            PREFIX : <http://example.org/git-onto-logic#>
            SELECT ?repo ?rn
            WHERE {
              ?repo a :Repository ;
                    :repoName ?rn .
              FILTER(STRENDS(LCASE(?rn), LCASE(CONCAT("/", "%s"))))
            }
            LIMIT 1
            """ % esc
            for row in self.graph.query(q2):
                return str(row.repo), str(row.rn)

        # 3) Contains match (case-insensitive) - fallback
        q3 = """
        PREFIX : <http://example.org/git-onto-logic#>
        SELECT ?repo ?rn
        WHERE {
          ?repo a :Repository ;
                :repoName ?rn .
          FILTER(CONTAINS(LCASE(?rn), LCASE("%s")))
        }
        LIMIT 1
        """ % esc
        for row in self.graph.query(q3):
            return str(row.repo), str(row.rn)

        return None, None

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
        results = []
        if repository:
            # Step 1: Resolve the repository IRI from input using robust matching
            repo_iri, matched = self._resolve_repo_iri(repository)
            if not repo_iri:
                print(f"DEBUG: _get_merge_commits - repository not found for input '{repository}'")
                return []
            else:
                print(f"DEBUG: _get_merge_commits - resolved '{repository}' -> '{matched}' as {repo_iri}")

            # Step 2: Query merge commits for that repository via its branches
            commit_q = """
            PREFIX : <http://example.org/git-onto-logic#>
            SELECT ?commit ?message ?date ?branch
            WHERE {
              VALUES ?repo { <%s> }
              ?repo :hasBranch ?branch .
              ?branch :hasCommit ?commit .
              ?commit a :MergeCommit ;
                      :message ?message ;
                      :commitDate ?date .
            }
            ORDER BY DESC(?date)
            LIMIT 50
            """ % repo_iri

            for row in self.graph.query(commit_q):
                results.append({
                    'commit': str(row.commit).split('#')[-1],
                    'message': str(row.message),
                    'date': str(row.date),
                    'branch': str(row.branch).split('#')[-1]
                })
            return results
        else:
            # No repository filter: return top merge commits globally
            query = """
            PREFIX : <http://example.org/git-onto-logic#>
            SELECT ?commit ?message ?date ?branch
            WHERE {
                ?repo a :Repository ;
                      :hasBranch ?branch .
                ?branch :hasCommit ?commit .
                ?commit a :MergeCommit ;
                        :message ?message ;
                        :commitDate ?date .
            }
            ORDER BY DESC(?date)
            LIMIT 50
            """

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