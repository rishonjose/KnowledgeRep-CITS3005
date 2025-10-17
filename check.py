from owlready2 import get_ontology
onto = get_ontology("ontology/git-onto-logic-populated.owl").load(reload=True)

print("Repositories:", len(list(onto.classes())))
print("Repository class present?", hasattr(onto, "Repository"))
if hasattr(onto, "Repository"):
    repos = list(onto.Repository.instances())
    print("Repo count:", len(repos))
    if repos:
        r = repos[0]
        print("Repo attributes:", r.get_properties())
        for p in r.get_properties():
            print(p, list(p[r]))

if hasattr(onto, "User"):
    users = list(onto.User.instances())
    print("User count:", len(users))
    if users:
        u = users[0]
        print("User attributes:", u.get_properties())
        for p in u.get_properties():
            print(p, list(p[u]))
