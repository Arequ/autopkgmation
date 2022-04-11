#!/Library/AutoPkg/Python3/Python.framework/Versions/3.7/bin/python3
"""Create an updated gitlab-ci yml file to create unique jobs that are all nested within a stage.
This allows us visiblity of which recipe ran and its status. Each job has a single log file 
for each app run.
"""
import datetime
import re

from ruamel.yaml import YAML

from alex_gitlab import Gitz

def main():
    # initialize custom git client.
    g = Gitz("code.gitlab.company.com", "123456")
    # Scans glob of files on specified repo.
    recipes = [
        re.findall("^(\S+)\.munki", obj["name"])[0].lower()
        for obj in g.list_repo_tree()
        if "munki.recipe" in obj["name"]
    ]
    # Get the latest gitlab-ci file from source.
    g.download_a_file(r"%2Egitlab-ci%2Eyaml", "./gitlab-ci.yaml", "main")
    # Open that yaml file and construct a more-friendly python dict.
    with open("./.gitlab-ci.yml", "r") as afile:
        dicto = YAML(typ="safe").load(afile)
    # create existing job list so we don't process those
    existing_jobs = [job for job in list(dicto.keys())[1:]]
    # Getting the difference  between whats in the  yml
    #  and what is new from the list tree api call.
    new_jobs = list(set(recipes) - set(existing_jobs))
    # Construct a new dictionary for each app that doesnt
    # already exist to make a new job per app.
    for job in new_jobs:
        dicto[job] = {
            "stage": "autopkg",
            "rules": [{"if": f"$RECIPE_NAME =~ /{job}/"}],
            "tags": ["alexs_macbook"],
            "script": [
                f"/usr/local/bin/autopkg run $(grep -o {job} <<< ${{RECIPE_NAME}}).munki"
            ],
        }
    # Don't need to write it locally...
    # with open(".gitlab-ci.yml", "w+") as fileout:
    #    yml = YAML()
    #    yml.indent(mapping=2, sequence=4, offset=2)
    #    yml.dump(dicto, fileout)
    now_time = datetime.datetime.now().strftime("%s")
    yml = YAML()
    yml.indent(mapping=2, sequency=4, offset=2)
    g.replace_file(
        branch=f"{now_time}-new-autopkg-recipes",
        commit_msg=f"Added the following recipes: {' '.join(new_jobs)}.",
        f_path=r"%2Egitlab-ci%2Eyaml",
        f_contents=yml.dump(dicto),
    )

if __name__ == "__main__":
    main()
