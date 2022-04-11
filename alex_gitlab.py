"""A custom git client
"""

import json
import os
import sys
import urllib.parse
import urllib.request


class Gitz:
    """Performs git tasks utilizing a private token and the Gitlab api."""

    def __init__(self, base_url, project_id, git_token=""):
        self.api_project_url = (
            f"https://{base_url}/api/v4/projects/{project_id}/repository"
        )
        if not git_token:
            self.git_token = os.environ.get("GIT_TOKEN")
        else:
            self.git_token = git_token
        urllib.request.install_opener(self.set_opener())

    def set_opener(self):
        # Set up the headers for use with the rest of the class' objects.
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ("PRIVATE-TOKEN", self.git_token),
            ("Content-Type", "application/json"),
        ]
        return opener

    def list_repo_tree(self):
        """https://docs.gitlab.com/ee/api/repositories.html
        returns list output: Produces a list of files in the repo."""
        output = []
        dict_resp = "go"
        page = 0
        while dict_resp != []:
            page += 1
            try:
                req = urllib.request.Request(
                    f"{self.api_project_url}/tree?page={str(page)}"
                )
                with urllib.request.urlopen(req) as response:
                    if response:
                        if response.getcode() == 200:
                            dict_resp = json.loads(response.read().decode("ASCII"))
                            output = output + dict_resp
            except urllib.error.HTTPError as error:
                print(f"Issue creating new feature branch with error: {error}")
                sys.exit(1)
        return output

    def download_a_file(self, f_path, f_out_path, branch):
        """Downloads a specified file from git repo.

        Args:
            f_path (str): url encoded path to file on repo.
            f_out_path(str): path where output file will be downloaded.
            dafile (str): url encoded path to file

        Returns:
            int: returned status code of replace file api call to git.
        """
        try:
            url = f"{self.api_project_url}/files/{f_path}/raw?ref={branch}"
            win_common_yaml, _ = urllib.request.urlretrieve(url, f_out_path)
            return win_common_yaml
        except urllib.error.URLError as erra:
            print(f"Error: {erra}")
            sys.exit(1)

    def make_new_branch(self, src_branch, new_branch):
        """Make a new branch based on the branch name passed when
        the GetGit object is initially declared.

        Args:
            src_branch (str):  branch ya coming from
            new_branch (str): branch ya going to
        """
        params = {"branch": new_branch, "ref": src_branch}
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(f"{self.api_project_url}/branches", data=data)
        try:
            with urllib.request.urlopen(req) as response:
                if response:
                    if response.getcode() == 200:
                        print(f"{self.feature_branch} has been created.")
        except urllib.error.HTTPError as error:
            print(f"Issue creating new feature branch with error: {error}")
            sys.exit(1)

    def replace_file(self, branch, commit_msg, f_path, f_contents):
        """Replaces the file in the git repo

        Args:
            branch (str): the target branch to replace file on
            commit_msg (str): git commit message,
            f_path (str): url encoded path to fil,
            f_contents (str): the actual contents of the file

        Returns:
            int: returned status code of replace file api call to git.
        """
        api_endpoint = f"{self.api_project_url}/files/{f_path}"
        params = {
            "start_branch": "master",
            "branch": branch,
            "author_email": "email@gmail.com",
            "author_name": "Alex Alequin",
            "content": f_contents,
            "commit_message": commit_msg,
        }
        urllib.request.install_opener(self.set_opener())
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(api_endpoint, data=data, method="PUT")
        try:
            return urllib.request.urlopen(req).getcode()
        except urllib.error.HTTPError as error:
            print(f"issues swapping out the file with error: {error}")
            return sys.exit(1)

    def submit_mr(self, src_branch, apps):
        """submits a merge request from the newly created feature branch

        Args:
            src_branch (str): where ya comin from
            apps (str):  app list for the mr message.

        Returns:
            str: submitted merge request url
        """
        api_endpoint = f"{self.api_project_url.rsplit('/',1)[0]}/merge_requests"
        params = {
            "source_branch": src_branch,
            "target_branch": "main",
            "title": f"Updating gitlab CI jobs to include  the  following apps: {apps}",
        }
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(api_endpoint, data=data, method="POST")
        try:
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as error:
            print(
                f"Issue submitting merge request from feature branch with error: {error}"
            )
            return sys.exit(1)
