# validate_ontology.py
from pyshacl import validate
from rdflib import Graph

data_file = "outputs/populated.owl"
shapes_file = "ontology/shapes.ttl"

print(f"🔍 Validating {data_file} with {shapes_file} ...")

data_g = Graph().parse(data_file, format="xml")
shapes_g = Graph().parse(shapes_file, format="turtle")

conforms, report_graph, report_text = validate(
    data_graph=data_g,
    shacl_graph=shapes_g,
    inference='rdfs',
    abort_on_first=False,
    meta_shacl=False,
    debug=False
)

print("\nValidation Report:")
print(report_text)
print(" Conforms:", conforms)

with open("outputs/SHACL_REPORT.txt", "w") as f:
    f.write(report_text)
print("📁 Saved detailed report → outputs/SHACL_REPORT.txt")
