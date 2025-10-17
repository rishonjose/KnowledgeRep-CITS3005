# --------------------------------------------------------
# Git-Onto-Logic Advanced Ontology
# Author: Saayella
# --------------------------------------------------------
from owlready2 import *

# Create ontology
onto = get_ontology("http://example.org/git-onto-logic#")

with onto:
    # === Core Classes ===
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class User(Thing): pass
    class File(Thing): pass
    class PullRequest(Thing): pass
    class Issue(Thing): pass

    # === Inferred / Specialised Classes ===
    class MergeCommit(Commit): pass
    class InitialCommit(Commit): pass
    class SecurityCommit(Commit): pass

    # === Object Properties ===
    class hasBranch(ObjectProperty):
        domain = [Repository]
        range  = [Branch]

    class hasCommit(ObjectProperty):
        domain = [Branch]
        range  = [Commit]

    class authoredBy(ObjectProperty):
        domain = [Commit]
        range  = [User]

    class onBranch(ObjectProperty):
        domain = [Commit]
        range  = [Branch]

    class updatesFile(ObjectProperty):
        domain = [Commit]
        range  = [File]

    class hasIssue(ObjectProperty):
        domain = [Repository]
        range  = [Issue]

    class hasPullRequest(ObjectProperty):
        domain = [Repository]
        range  = [PullRequest]

    class openedBy(ObjectProperty):
        domain = [Issue, PullRequest]
        range  = [User]

    class assignedTo(ObjectProperty):
        domain = [Issue]
        range  = [User]

    class mergedBy(ObjectProperty):
        domain = [PullRequest]
        range  = [User]

    class parent(ObjectProperty):
        domain = [Commit]
        range  = [Commit]

    # === Data Properties ===
    class hasName(DataProperty, FunctionalProperty):
        range = [str]

    class message(DataProperty):
        domain = [Commit]
        range  = [str]

    class timestamp(DataProperty):
        domain = [Commit]
        range  = [str]

    class isMain(DataProperty):
        domain = [Branch]
        range  = [bool]

    class status(DataProperty):
        domain = [Issue, PullRequest]
        range  = [str]

    # === Logical Restrictions ===
    Repository.is_a.append(hasBranch.min(1, Branch))
    Branch.is_a.append(hasCommit.min(1, Commit))
    Commit.is_a.append(authoredBy.exactly(1, User))
    Commit.is_a.append(onBranch.exactly(1, Branch))

    # === Equivalent Class Definitions ===
    MergeCommit.equivalent_to.append(Commit & parent.min(2, Commit))
    InitialCommit.equivalent_to.append(Commit & Not(parent.some(Commit)))

    # === Safe SWRL Rule (HermiT-compatible) ===
    # Demonstrates ontology-level rule usage without string built-ins.
    rule = Imp()
    rule.set_as_rule("Commit(?c), message(?c, ?m) -> SecurityCommit(?c)")

# Save ontology
onto.save(file="ontology/git-onto-logic-advanced.owl", format="rdfxml")
print("✅ Ontology saved: ontology/git-onto-logic-advanced.owl")
