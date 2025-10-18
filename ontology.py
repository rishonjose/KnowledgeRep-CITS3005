from owlready2 import *

onto = get_ontology("http://example.org/git-onto-logic#")

with onto:
    # Core Classes 
    class Repository(Thing): pass
    class Branch(Thing): pass
    class Commit(Thing): pass
    class User(Thing): pass
    class File(Thing): pass
    class PullRequest(Thing): pass
    class Issue(Thing): pass

    # Inferred Classes
    class MergeCommit(Commit): pass
    class InitialCommit(Commit): pass
    class SecurityCommit(Commit): pass
    class UnmergedBranch(Branch): pass
    class MergedPullRequest(PullRequest): pass

    # Object Properties
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

    class committedBy(ObjectProperty):
        domain = [Commit]
        range  = [User]

    class parent(ObjectProperty):
        domain = [Commit]
        range  = [Commit]

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

    class mergedInto(ObjectProperty):
        domain = [Branch]
        range  = [Branch]

    class hasBaseBranch(ObjectProperty):
        domain = [PullRequest]
        range  = [Branch]

    class hasHeadBranch(ObjectProperty):
        domain = [PullRequest]
        range  = [Branch]

    class assignedTo(ObjectProperty):
        domain = [Issue]
        range  = [User]

    # Data Properties 
    class repoName(DataProperty): domain = [Repository]; range = [str]
    class repoLanguage(DataProperty): domain = [Repository]; range = [str]
    class repoStars(DataProperty): domain = [Repository]; range = [int]
    class repoForks(DataProperty): domain = [Repository]; range = [int]

    class branchName(DataProperty): domain = [Branch]; range = [str]
    class isDefault(DataProperty): domain = [Branch]; range = [bool]

    class commitSHA(DataProperty): domain = [Commit]; range = [str]
    class message(DataProperty): domain = [Commit]; range = [str]
    class commitDate(DataProperty): domain = [Commit]; range = [str]
    class isInitial(DataProperty): domain = [Commit]; range = [bool]

    class fileName(DataProperty): domain = [File]; range = [str]
    class fileStatus(DataProperty): domain = [File]; range = [str]
    class fileChanges(DataProperty): domain = [File]; range = [int]

    class title(DataProperty): domain = [Issue, PullRequest]; range = [str]
    class state(DataProperty): domain = [Issue, PullRequest]; range = [str]
    class mergedAt(DataProperty): domain = [PullRequest]; range = [str]

    class userLogin(DataProperty): domain = [User]; range = [str]
    class userURL(DataProperty): domain = [User]; range = [str]
    class isConcurrentContributor(DataProperty): domain = [User]; range = [bool]

    # Logical Restrictions 
    Repository.is_a.append(hasBranch.min(1, Branch))
    Branch.is_a.append(hasCommit.min(1, Commit))
    Commit.is_a.append(authoredBy.min(1, User))
    Commit.is_a.append(onBranch.exactly(1, Branch))

    # Equivalent Class Definitions 
    MergeCommit.equivalent_to.append(Commit & parent.min(2, Commit))
    InitialCommit.equivalent_to.append(Commit & ~parent.some(Commit))
    UnmergedBranch.equivalent_to.append(Branch & ~mergedInto.some(Branch))
    MergedPullRequest.equivalent_to.append(PullRequest & state.value("closed") & mergedAt.some(str))

    # SWRL Placeholder (Documentation only) 
    rule = Imp()
    rule.set_as_rule("""
        Commit(?c), message(?c, ?m) -> SecurityCommit(?c)
    """)

    class ConcurrentContributor(User): pass
    ConcurrentContributor.equivalent_to.append(
        User & onto.isConcurrentContributor.value(True)
    )

onto.save(file="ontology.owl", format="rdfxml")
print("Ontology saved: ontology.owl")
