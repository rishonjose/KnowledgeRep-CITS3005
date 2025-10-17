# --------------------------------------------------------
# Git-Onto-Logic Ontology v1 (property-method style)
# --------------------------------------------------------
from owlready2 import *
import datetime  # for datetime.datetime

onto = get_ontology("http://example.org/git-onto-logic#")

with onto:
    # --- CLASSES ---
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class File(Thing): pass
    class User(Thing): pass
    class Activity(Thing): pass   # base for actions

    # --- OBJECT PROPERTIES ---
    class hasBranch(ObjectProperty):
        domain = [Repository]
        range  = [Branch]

    class containsFile(ObjectProperty):
        domain = [Repository]
        range  = [File]

    class initialCommit(ObjectProperty):
        domain = [Branch]
        range  = [Commit]

    class onBranch(ObjectProperty):
        domain = [Commit]
        range  = [Branch]

    class authoredBy(ObjectProperty):
        domain = [Commit]
        range  = [User]

    class updatesFile(ObjectProperty):
        domain = [Commit]
        range  = [File]

    class parent(ObjectProperty):
        domain = [Commit]
        range  = [Commit]

    # --- DATA PROPERTIES ---
    class hasName(DataProperty):
        domain = [Repository, Branch, File, User]
        range  = [str]
        characteristics = [FunctionalProperty]

    class message(DataProperty):
        domain = [Commit]
        range  = [str]

    class timestamp(DataProperty):
        domain = [Activity, Commit]
        range  = [datetime.datetime]  # maps to xsd:dateTime

    # --- RESTRICTIONS (use property methods) ---
    Repository.is_a.append(hasBranch.min(1, Branch))                 # ≥1 branch
    Branch.is_a.append(initialCommit.exactly(1, Commit))             # exactly 1 initial commit
    Commit.is_a.append(authoredBy.exactly(1, User))                  # exactly 1 author
    Commit.is_a.append(onBranch.exactly(1, Branch))                  # exactly 1 branch
    Commit.is_a.append(timestamp.exactly(1, datetime.datetime))      # exactly 1 timestamp
    Commit.is_a.append(updatesFile.min(1, File))                     # updates ≥1 file

    # --- INFERRED CLASSES (reasoner will classify) ---
    class InitialCommit(Commit):
        # zero parents → use max(0, ...)
        equivalent_to = [Commit & parent.max(0, Commit)]

    class MergeCommit(Commit):
        # ≥2 parents
        equivalent_to = [Commit & parent.min(2, Commit)]

    # --- DISJOINTNESS ---
    AllDisjoint([InitialCommit, MergeCommit])

# --- EXPORT ---
if __name__ == "__main__":
    out = "ontology/git-onto-logic.owl"
    onto.save(file=out, format="rdfxml")
    print(f"✅ Exported ontology to {out}")
