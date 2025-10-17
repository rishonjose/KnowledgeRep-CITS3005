# --------------------------------------------------------
# Git-Onto-Logic (Final Clean Version)
# --------------------------------------------------------
from owlready2 import *
import datetime

onto = get_ontology("http://example.org/git-onto-logic#")

with onto:
    # ----------------------------------------------------
    # 🧱 CORE CLASSES
    # ----------------------------------------------------
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class File(Thing): pass
    class User(Thing): pass
    class Activity(Thing): pass

    # ----------------------------------------------------
    # ⚙️ OPTIONAL EXTENSIONS
    # ----------------------------------------------------
    class PullRequest(Thing): pass
    class Issue(Thing): pass

    # ----------------------------------------------------
    # 🔗 OBJECT PROPERTIES
    # ----------------------------------------------------
    # Repository structure
    class hasBranch(ObjectProperty):
        domain = [Repository]
        range  = [Branch]

    class containsFile(ObjectProperty):
        domain = [Repository]
        range  = [File]

    # Branch → Commit
    class hasCommit(ObjectProperty):
        domain = [Branch]
        range  = [Commit]

    class initialCommit(ObjectProperty):
        domain = [Branch]
        range  = [Commit]

    # Commit relations
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

    # PullRequest relations (optional)
    class hasSourceBranch(ObjectProperty):
        domain = [PullRequest]
        range  = [Branch]
        characteristics = [FunctionalProperty]

    class hasTargetBranch(ObjectProperty):
        domain = [PullRequest]
        range  = [Branch]
        characteristics = [FunctionalProperty]

    class createsMergeCommit(ObjectProperty):
        domain = [PullRequest]
        range  = [Commit]

    class openedBy(ObjectProperty):
        domain = [PullRequest, Issue]
        range  = [User]

    class resolvedBy(ObjectProperty):
        domain = [Issue]
        range  = [PullRequest, Commit]

    # ----------------------------------------------------
    # 🔤 DATA PROPERTIES
    # ----------------------------------------------------
    class hasName(DataProperty):
        domain = [Repository, Branch, File, User, PullRequest]
        range = [str]
        characteristics = [FunctionalProperty]

    class message(DataProperty):
        domain = [Commit]
        range = [str]

    class timestamp(DataProperty):
        domain = [Activity, Commit]
        range = [datetime.datetime]

    class isMain(DataProperty):
        domain = [Branch]
        range = [bool]

    class hasStatus(DataProperty):
        domain = [PullRequest, Issue]
        range = [str]

    # ----------------------------------------------------
    # 🧮 LOGICAL RESTRICTIONS
    # ----------------------------------------------------
    Repository.is_a.append(hasBranch.min(1, Branch))
    Branch.is_a.append(initialCommit.exactly(1, Commit))
    Commit.is_a.append(authoredBy.exactly(1, User))
    Commit.is_a.append(onBranch.exactly(1, Branch))
    Commit.is_a.append(updatesFile.min(1, File))
    Commit.is_a.append(timestamp.exactly(1, datetime.datetime))

    # ----------------------------------------------------
    # 🧠 INFERRED CLASSES
    # ----------------------------------------------------
    class InitialCommit(Commit):
        equivalent_to = [Commit & parent.max(0, Commit)]

    class MergeCommit(Commit):
        equivalent_to = [Commit & parent.min(2, Commit)]

    class SecurityCommit(Commit):
        equivalent_to = [Commit & message.value("security")]

    AllDisjoint([InitialCommit, MergeCommit])

# --------------------------------------------------------
# EXPORT
# --------------------------------------------------------
if __name__ == "__main__":
    onto.save(file="ontology/git-onto-logic-final.owl", format="rdfxml")
    print("✅ Exported: git-onto-logic-final.owl")
