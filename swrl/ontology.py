from owlready2 import *
from pathlib import Path

# ============================================================
# Setup
# ============================================================
OUTPUTS = Path("outputs")
OUTPUTS.mkdir(exist_ok=True)

onto = get_ontology("http://example.org/git-onto-logic#")

# ============================================================
# Define Classes
# ============================================================
with onto:
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class User(Thing): pass
    class File(Thing): pass

    class InitialCommit(Commit): pass
    class MergeCommit(Commit): pass
    class UnmergedBranch(Branch): pass

# ============================================================
# Object Properties
# ============================================================
with onto:
    class hasBranch(ObjectProperty):
        domain = [Repository]
        range  = [Branch]

    class hasCommit(ObjectProperty):
        domain = [Branch]
        range  = [Commit]

    class onBranch(ObjectProperty):
        domain = [Commit]
        range  = [Branch]

    class authoredBy(ObjectProperty):
        domain = [Commit]
        range  = [User]

    class parent(ObjectProperty):
        domain = [Commit]
        range  = [Commit]

    class mergedInto(ObjectProperty):
        domain = [Branch]
        range  = [Branch]

# ============================================================
# Data Properties
# ============================================================
with onto:
    class repoName(DataProperty): domain = [Repository]; range = [str]
    class repoLanguage(DataProperty): domain = [Repository]; range = [str]
    class branchName(DataProperty): domain = [Branch]; range = [str]
    class commitSHA(DataProperty): domain = [Commit]; range = [str]
    class message(DataProperty): domain = [Commit]; range = [str]
    class userLogin(DataProperty): domain = [User]; range = [str]
    class fileName(DataProperty): domain = [File]; range = [str]

# ============================================================
# Logical Restrictions
# ============================================================
with onto:
    Repository.is_a.append(hasBranch.min(1, Branch))
    Branch.is_a.append(hasCommit.min(1, Commit))
    Commit.is_a.append(authoredBy.min(1, User))
    Commit.is_a.append(onBranch.exactly(1, Branch))

# ============================================================
# Equivalent Class Definitions
# ============================================================
with onto:
    # Equivalent class definitions (HermiT will use these)
    MergeCommit.equivalent_to.append(Commit & parent.min(2, Commit))
    InitialCommit.equivalent_to.append(Commit & ~parent.some(Commit))
    UnmergedBranch.equivalent_to.append(Branch & ~mergedInto.some(Branch))

# ============================================================
# Valid SWRL Rules (syntactically safe)
# ============================================================
with onto:
    # SWRL rules cannot use 'not' directly in Owlready2.
    # These are documentation placeholders — still valid OWL syntax.
    r1 = Imp()
    r1.set_as_rule("""
        Commit(?c), parent(?c, ?p) -> MergeCommit(?c)
    """)

    r2 = Imp()
    r2.set_as_rule("""
        Branch(?b), mergedInto(?b, ?m) -> Branch(?b)
    """)
# --- Test commit for SWRL demonstration ---
with onto:
    p1 = onto.Commit("demo_parent1")
    p2 = onto.Commit("demo_parent2")
    m  = onto.Commit("demo_merge")
    m.parent.append(p1)
    m.parent.append(p2)

# ============================================================
# Save Ontology
# ============================================================
onto.save(file=str(OUTPUTS / "ontology.owl"), format="rdfxml")
print("💾 Ontology successfully saved at: outputs/ontology.owl")

# ============================================================
# Quick verification
# ============================================================
print("\n🔍 Ontology structure verification:")
print(f"Classes: {len(list(onto.classes()))}")
print(f"Object properties: {len(list(onto.object_properties()))}")
print(f"Data properties: {len(list(onto.data_properties()))}")
print("✅ ontology.owl is ready for reasoning demo.")
