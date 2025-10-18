from pyshacl import validate
from rdflib import Graph
from termcolor import colored

#  File paths 
DATA_FILE = "populated.owl"
SHACL_FILE = "shacl.ttl"

print(colored("Running SHACL Validation...", "cyan"))

# Load RDF and SHACL 
data_graph = Graph().parse(DATA_FILE, format="xml")
shacl_graph = Graph().parse(SHACL_FILE, format="turtle")

# Validate 
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shacl_graph,
    inference="rdfs",
    abort_on_error=False,
    meta_shacl=False,
    debug=False
)

# Print results 
if conforms:
    print(colored("Graph conforms to SHACL shapes!", "green"))
else:
    print(colored("Graph does NOT conform to SHACL shapes!", "red"))

print("\n Validation Report ")
print(results_text)

# Save report 
results_graph.serialize("validation_report.ttl", format="turtle")
print(colored("\n📄 Saved detailed report to validation_report.ttl", "yellow"))
