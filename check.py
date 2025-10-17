from owlready2 import get_ontology
from collections import defaultdict

onto = get_ontology("ontology/git-onto-logic-populated.owl").load()

print("=" * 80)
print(f"ONTOLOGY LOADED: {onto.base_iri}")
print("=" * 80)

# ----------------------------------------------------------------------------
# 1. List all classes
# ----------------------------------------------------------------------------
print("\n🧩 CLASSES FOUND:")
for cls in onto.classes():
    print(f"- {cls.name} ({len(list(cls.instances()))} instances)")

# ----------------------------------------------------------------------------
# 2. List all object/data properties
# ----------------------------------------------------------------------------
print("\n🔗 PROPERTIES:")
for prop in onto.properties():
    domains = [d.name for d in prop.domain]
    ranges = []
    for r in prop.range:
        # Handle datatypes like str, int, etc.
        if hasattr(r, "name"):
            ranges.append(r.name)
        else:
            ranges.append(str(r))
    print(f"- {prop.name}")
    if domains or ranges:
        print(f"   ↳ Domain: {domains or ['(none)']} | Range: {ranges or ['(none)']}")

# ----------------------------------------------------------------------------
# 3. Sample instances for key classes
# ----------------------------------------------------------------------------
def val(prop):
    if isinstance(prop, list):
        return prop[0] if prop else None
    return prop

def sample_instance(cls_name, count=3):
    cls = getattr(onto, cls_name, None)
    if not cls:
        print(f"\n❌ No class named '{cls_name}' found.")
        return
    instances = list(cls.instances())
    if not instances:
        print(f"\n⚠️ No instances found for class '{cls_name}'.")
        return

    print(f"\n\n=== 🔍 SAMPLE: {cls_name} ({len(instances)} total instances) ===")
    for obj in instances[:count]:
        print(f"\n→ Instance: {obj.name}")
        for p in obj.get_properties():
            values = list(p[obj])
            short_values = [v.name if hasattr(v, "name") else v for v in values]
            print(f"   • {p.name}: {short_values[:5]}{' ...' if len(short_values) > 5 else ''}")

# ----------------------------------------------------------------------------
# 4. Run samples for key classes
# ----------------------------------------------------------------------------
for cls_name in ["Repository", "Branch", "Commit", "User", "Issue", "PullRequest"]:
    sample_instance(cls_name)

# ----------------------------------------------------------------------------
# 5. Global property usage summary
# ----------------------------------------------------------------------------
print("\n\n📊 GLOBAL PROPERTY USAGE SUMMARY:")
prop_counts = defaultdict(int)
for cls in onto.classes():
    for inst in cls.instances():
        for p in inst.get_properties():
            prop_counts[p.name] += 1

for prop, count in sorted(prop_counts.items(), key=lambda x: -x[1]):
    print(f"{prop:40s} → {count}")

# ----------------------------------------------------------------------------
# 6. Quick sanity report
# ----------------------------------------------------------------------------
print("\n\n✅ SUMMARY REPORT:")
print(f"Repositories: {len(list(onto.Repository.instances()))}")
print(f"Branches: {len(list(onto.Branch.instances()))}")
print(f"Commits: {len(list(onto.Commit.instances()))}")
print(f"Users: {len(list(onto.User.instances()))}")
print(f"Issues: {len(list(onto.Issue.instances()))}")
print(f"PullRequests: {len(list(onto.PullRequest.instances()))}")
print("\nDone.")