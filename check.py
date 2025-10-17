from owlready2 import *

onto = get_ontology("ontology/git-onto-logic-populated.owl").load()

merged_count = 0
for b in onto.Branch.instances():
    if b.mergedInto:
        merged_count += 1
        print(f"{b.name} → {b.mergedInto[0].name}")

print(f"\nTotal mergedInto relations: {merged_count}")
