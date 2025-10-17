# --------------------------------------------------------
# Validate Git-Onto-Logic Graph using pySHACL
# --------------------------------------------------------
from pyshacl import validate
from rdflib import Graph

data_graph = Graph().parse("ontology/git-onto-logic-populated.owl", format="xml")
shapes_graph = Graph().parse("ontology/git-onto-logic-shapes.ttl", format="turtle")

results = validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',
    abort_on_first=False,
    allow_infos=True,
    allow_warnings=True
)

conforms, results_graph, results_text = results
print("✅ Validation Result:", conforms)
print(results_text)
