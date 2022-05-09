#!/usr/bin/env python

import base64
from github import Github, InputGitTreeElement
from io import StringIO
import json
import logging
# import pandas as pd
import requests
import time
import warnings

warnings.filterwarnings("ignore")
timestr = time.strftime("%Y%m%d-%H%M%S")
fileName = 'logFile-Git-' + timestr + '.log'
logging.basicConfig(filename=fileName, level=logging.INFO)


class Git():
    """
    This is an abstract class built on github client which provides functions to interact with DigitalManufacturing org.
    Attributes:
        url: URL of git
        organization: Name of Github organization
        accessToken: Token to authenticate to github
        connected: Flag to indicate connection status
    """

    def __init__(self, url, accessToken, organization="DigitalManufacturing"):
        """
        Initializes a client object to Github with the provided url
        :param url: Github url
        :param accessToken: Token to authenticate to Github
        : return Git object
        """
        try:
            self.url = url
            self.__accessToken = accessToken
            self.organization = organization
            g = Github(base_url=self.url, login_or_token=self.__accessToken, verify=False)
            self.dmc = g.get_organization(self.organization)
            logging.info("initializeOrg : initializeOrg Organization : {}".format(self.dmc))
            self.connected = True

        except Exception as e:
            self.connected = False
            print("__init__: Encountered exception: ", e)
            logging.exception("__init__: Encountered exception: {}".format(e))
            raise Exception("Exception while initializing  Git object.", e)

    def getOrgMembers(self):
        """
        This method fetches the members of git organization
        :return members: Member list
        """
        members = []
        try:
            members = self.dmc.get_members()
            logging.info("getOrgMembers: Getting Organazation members.")

        except Exception as e:
            print("getOrgMembers: Encountered exception: ", e)
            logging.exception("getOrgMembers: Encountered exception: {}".format(e))
        return members

    def getRepoNamesList(self):
        """
        This method get the list of repo names from github organization
        :return repoList: List of repo names
        """
        repoList = []
        try:
            repoList = [repo.name for repo in self.dmc.get_repos().reversed]
            logging.info("getRepoNames: Fetched list of repo names. Count: {}".format(len(repoList)))

        except Exception as e:
            print("getRepoNames: Encountered exception: ", e)
            logging.exception("getRepoNames: Encountered exception: {}".format(e))
            raise Exception("Exception while fetching Repo names.", e)
        return repoList

    def getRepoList(self):
        """
        This method get the list of repo names from github organization
        :return repoList: List of repo names
        """
        repoList = []
        try:
            repoList = self.dmc.get_repos()
            # repos = [repo for repo in self.dmc.get_repos().reversed if repo.name == repoName]

            # if repos:
            #     repo = repos[0]
            #     logging.info("getRepo: Fetched github team object for repo : {}".format(repoName))
            # else:
            #     logging.info("getRepo: Unable to fetch details of repo : {}".format(repoName))
            #     raise GitError("Unable to fetch details of repo: {}".format(repoName))
            # logging.info("getRepo: Fetched list of repos. Count: {}", len(repoList))

        except Exception as e:
            print("getRepo: Encountered exception: ", e)
            logging.exception("getRepo: Encountered exception: {}".format(e))
            raise Exception("Exception while fetching Repo list.", e)
        return repoList

    def getTeam(self, teamName):
        """
        This method returns the team object from github organization
        :param teamName: Name of github team
        :return team: github team object
        """
        team = None
        try:
            teams = [team for team in self.dmc.get_teams().reversed if team.name == teamName]

            if teams:
                team = teams[0]
                logging.info("getTeam: Fetched github team object for team : {}", teamName)
            else:
                logging.info("getTeam: Unable to fetch details of team : {}", teamName)
                raise GitError("Unable to fetch details of team: {}".format(teamName))

        except Exception as e:
            print("getTeam: Encountered exception: {}".format(e))
            logging.exception("getTeam: Encountered exception: {}".format(e))
            raise Exception("Exception while fetching details of team.", e)

        return team

    def getTeamNames(self):
        """
        This method returns the names of repos under github organization
        :return teamNames: List of team names
        """
        teamNames = []
        try:
            teamNames = [team.name for team in self.dmc.get_teams().reversed]
            logging.info("getTeamNames: Fetched names of repos under git organization.")
        except Exception as e:
            print("getTeamNames: Encountered exception: {}".format(e))
            logging.exception("getTeamNames: Encountered exception: {}".format(e))
            raise Exception("Exception while fetching team names.", e)
        return teamNames

    def getTeamMembers(self, teamName):
        """
        This method returns the list of members of input team
        :param teamName: Name of github team
        :return allMembersDict: Dict of git member object
        """
        members = []
        allMembersDict = {}
        try:
            team = self.getTeam(teamName)
            members = team.get_members()
            allMembersDict = {user.login: user.name for user in members}
            logging.info("getTeamMembers: Fetched members of taem: {}".format(teamName))
        except Exception as e:
            print("getTeamMembers: Encountered exception: {}".format(e))
            logging.exception("getTeamMembers: Encountered exception: {}".format(e))
            raise Exception("Exception while fetching team members.", e)
        return allMembersDict

    def checkBranchExistence(self, repoName, branchName):
        """
        This method checks input branch name exist for repo
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :return flag: True if exists
        """
        flag = False
        try:
            repo = self.dmc.get_repo(repoName)
            branch = repo.get_branch(branchName)
            if branch:
                logging.info("checkBranchExistence: {} branch exists.".format(branchName))
                flag = True

        except Exception as e:
            print("checkBranchExistence: Encountered exception: {}".format(e))
            logging.exception("checkBranchExistence: Encountered exception: {}".format(e))
            raise Exception("Exception while checking existance of branch.", e)
        return flag

    def checkBranchProtection(self, repoName, branchName):
        """
        This method check the branch protection exists for input repo and branch; returns default object if not
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :return data: Branch Protection dict
        """
        branchProtection = False
        try:

            defaultBranchProtection = {
                                        "restrictions": {
                                            "users": [],
                                            "teams": []
                                        },
                                        "required_status_checks": {
                                            "strict": True,
                                            "contexts": []
                                        },
                                        "enforce_admins": None,
                                        "required_pull_request_reviews": {
                                            "dismiss_stale_reviews": True,
                                            "require_code_owner_reviews": True,
                                            "required_approving_review_count": 1,
                                            "dismissal_restrictions": {
                                                "users": [],
                                                "teams": []
                                            }
                                        }
                                    }
            data = defaultBranchProtection
            url = 'https://github.tools.sap/api/v3/repos/DigitalManufacturing/' + repoName + '/branches/' + branchName + '/protection'
            r = requests.get(url=url,
                             headers={
                                 'Accept': 'application/vnd.github.luke-cage-preview+json',
                                 'Authorization': 'Token {0}'.format(self.__accessToken)},
                             verify=False
                             )

            response = json.loads(r.text)
            if r.status_code == 200:
                if 'restrictions' not in response:
                    data['restrictions'] = None
                elif response['restrictions']['teams'] == [] and response['restrictions']['users'] == []:
                    data['restrictions'] = None
                else:
                    teams = []
                    for team in response['restrictions']['teams']:
                        teams.append(team["name"])

                    data['restrictions']['teams'] = teams
                    users = []
                    for user in response['restrictions']['users']:
                        users.append(user["login"])
                    data['restrictions']['users'] = users

                if 'required_status_checks' not in response:
                    data['required_status_checks'] = None
                else:
                    data['required_status_checks']['strict'] = response['required_status_checks']['strict']
                    data['required_status_checks']['contexts'] = response['required_status_checks']['contexts']

                if 'required_pull_request_reviews' in response:

                    data['required_pull_request_reviews']['required_approving_review_count'] = \
                        response['required_pull_request_reviews']['required_approving_review_count']

                    if 'dismissal_restrictions' in response['required_pull_request_reviews']:
                        teams = []
                        for team in response['required_pull_request_reviews']['dismissal_restrictions']['teams']:
                            teams.append(team["name"])
                        data['required_pull_request_reviews']['dismissal_restrictions']['teams'] = teams

                        users = []
                        for user in response['required_pull_request_reviews']['dismissal_restrictions']['users']:
                            users.append(user["login"])
                        data['required_pull_request_reviews']['dismissal_restrictions']['users'] = users

                branchProtection = json.dumps(data)

                logging.info("checkBranchProtection: Branch protection Json output : {}".format(branchProtection))

            elif r.status_code == 404:
                if response["message"] == "Not Found":
                    logging.info(
                        "checkBranchProtection: You are not authorized to get Branch Protection. Access Denied to : {}\n".format(
                            repoName))
                    raise GitError("You are not authorized to get Branch Protection. Access Denied.")
            else:
                logging.info(
                    "checkBranchProtection: Branch Protection is not found for given Repo : {}\n".format(repoName))

        except Exception as e:
            print("checkBranchProtection: Exception occurred : {}".format(e))
            logging.exception("checkBranchProtection: Exception occurred : {}".format(e))
            raise Exception("Exception while checking branch protection details.", e)

        return branchProtection

    def updateBranchProtection(self, repoName, branchName, data):
        """
        This method updates the branch protection for input repo and branch
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :param data: Json Object with the branch protection confriguation
            data = {
                    dismiss_stale_reviews: "dismiss_stale_reviews"
                    dismissal_restrictions: "dismissal_restrictions"
                    require_code_owner_reviews: "require_code_owner_reviews"
                    required_approving_review_count: "required_approving_review_count"
                    }
        :return status: True if success
        """
        status = False
        try:
            jsonData = json.loads(data)

            url = 'https://github.tools.sap/api/v3/repos/DigitalManufacturing/' + repoName + '/branches/' + branchName + '/protection'
            r = requests.put(url=url,
                             headers={
                                 'Accept': 'application/vnd.github.luke-cage-preview+json',
                                 'Authorization': 'Token {0}'.format(self.__accessToken)},
                             json=jsonData,
                             verify=False
                             )

            response = json.loads(r.text)
            if r.status_code == 200:
                logging.info(
                    "updateBranchProtection: Branch Protection updated for repo : {} and branch : {}\n".format(repoName,
                                                                                                               branchName))
                status = True

            else:
                logging.info(
                    "updateBranchProtection: Branch Protection not updated for repo : {} and branch : {}. Error: {}".format(
                        repoName, branchName, response))
                raise GitError("Failed to update Branch Protection.", r.status_code, r.text)

        except Exception as e:
            print("updateBranchProtection: Exception occurred : {}".format(e))
            logging.exception("updateBranchProtection: Exception occurred : {}".format(e))
            raise Exception("Exception while updating branch protection details.", e)

        return status

    def deleteBranchProtection(self, repoName, branchName):
        """
        This method deletes the branch protection for input repo and branch
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :return status: True if success
        """
        response = {}
        try:
            repo = self.dmc.get_repo(repoName)
            branch = repo.get_branch(branchName)
            if branch:
                branch.remove_protection()
                logging.info(
                    "deleteBranchProtection: Removed branch Protection for repo: {} and branch:{}".format(repoName,
                                                                                                          branchName))
            else:
                logging.info(
                    "deleteBranchProtection: couldn't find branch: {} for repo: {}".format(branchName, repoName))
                raise GitError("Could not find branch to delete brach protection.")
        except Exception as e:
            print("deleteBranchProtection: Exception occurred : {}".format(e))
            logging.exception("deleteBranchProtection: Exception occurred : {}".format(e))
            raise Exception("Exception while deleting protection details.", e)
        return response

    def getHooks(self, repoName):
        """
        This method fetches the hook defined for input repo
        :param repoName: Name of github repo
        :return hooks: hook list
        """
        hooks = []
        try:
            url = 'https://github.tools.sap/api/v3/repos/DigitalManufacturing/' + repoName + '/pre-receive-hooks/5'
            r = requests.get(url=url,
                             headers={
                                 'Accept': 'application/vnd.github.eye-scream-preview',
                                 'Authorization': 'Token {0}'.format(self.__accessToken)},
                             verify=False
                             )
            if r.status_code == 200:
                hooks = json.loads(r.text)
            else:
                logging.info("getHooks: Request to get hook of repo -{} failed with status: {}. Response: {}".format(
                    repoName, r.status_code, r.text))
                raise GitError("Failed to update Branch Protection.", r.status_code, r.text)

        except Exception as e:
            print("getHooks: Exception occurred : {}".format(e))
            logging.exception("getHooks: Exception occurred : {}".format(e))
            raise Exception("Exception while fetching hook details.", e)
        return hooks

    def updateHook(self, repoName):
        """
        This method updates the hook for input repoName
        :param repoName: Name of github repo
        :return status: True if success
        """
        status = False
        try:
            url = 'https://github.tools.sap/api/v3/repos/DigitalManufacturing/' + repoName + '/pre-receive-hooks/5'
            r = requests.patch(url=url,
                               headers={
                                   'Accept': 'application/vnd.github.eye-scream-preview',
                                   'Authorization': 'Token {0}'.format(self.__accessToken)},
                               json={
                                   "enforcement": "enabled"
                               },
                               verify=False
                               )
            response = json.loads(r.text)
            if r.status_code == 200:
                status = True
                logging.info("updateHook: Hooks : {} for Repo Name : {}".format(response, repoName))

            else:
                logging.info("updateHook: Hook didn't get updated {}".format(repoName))
                logging.info("updateHook: Hooks : {} for Repo Name : {}".format(response, repoName))
                raise GitError("Failed to update Hook.", r.status_code, r.text)
        except Exception as e:
            print("updateHook: Exception occurred : {}".format(e))
            logging.exception("updateHook: Exception occurred : {}".format(e))
            raise Exception("Exception while updating hook details.", e)
        return status

    def deleteHook(self, repoName):
        """
        This method deletes the hook of input repo
        :param repoName: Name of github repo
        :return response: Response dict
        """
        response = {}
        try:
            url = 'https://github.tools.sap/api/v3/repos/DigitalManufacturing/' + repoName + '/pre-receive-hooks/5'
            r = requests.delete(url=url,
                                headers={
                                    'Accept': 'application/vnd.github.eye-scream-preview',
                                    'Authorization': 'Token {0}'.format(self.__accessToken)},

                                verify=False
                                )

            if r.status_code == 200:
                response = json.loads(r.text)
                logging.info("deleteHook: Hook deleted for the repo :{}".format(repoName))
            elif r.status_code == 422:
                logging.info("deleteHook: Hooks : {} for Repo Name : {}".format(response, repoName))
        except Exception as e:
            print("deleteHook: Exception occurred : {}".format(e))
            logging.exception("deleteHook: Exception occurred : {}".format(e))
            raise Exception("Exception while deleting hook.", e)
        return response

    def checkHooks(self, repoName):
        """
        This method checks hook exists for input repo
        :param repoName: Name of github repo
        :return status: True if exists
        """

        status = False
        try:
            data = self.getHooks(repoName)
            if 'enforcement' in data.keys() and data['enforcement'] == 'enabled':
                logging.info("checkHooks: Hooks are present for repo :{}.\n".format(repoName))
                status = True
            else:
                logging.info("checkHooks: Hooks are not present for repo :{}.\n".format(repoName))
        except Exception as e:
            print("checkHooks: Exception Occurred :{} : {}\n".format(e, repoName))
            logging.exception("checkHooks: Exception Occurred :{} : {}\n".format(e, repoName))
            raise Exception("Exception while checking hook.", e)
        return status

    def recastRestrictions(self, repoName, branchName, branchProtectJsonObject):
        """
        This method updates branch Protection for input branch and update the repo hook
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :param branchProtectJsonObject: Branch Protection object to update
        :return None
        """
        try:

            if branchProtectJsonObject:
                bpStatus = self.updateBranchProtection(repoName, branchName, branchProtectJsonObject)
            hookStatus = self.checkHooks(repoName)
            logging.info("recastRestrictions: Hook Status before recast - {}".format(hookStatus))
            hookUpdateStatus = self.updateHook(repoName)
        except Exception as e:
            print("recastRestrictions: Exception occurred: \n{}".format(e))
            logging.exception("recastRestrictions: Exception Occurred:\n{}".format(e))
            raise Exception("Exception while recastRestrictions.", e)

    def removeRestrictions(self, repoName, branchName):
        """
        This method remove branch Protection for input branch and deletes the repo hook
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :return bpDelResponse: Response of branch protection deletion
        :return deletedHook: Status of Hook deletion
        """
        bpDelResponse = {}
        deletedHook = False
        try:
            branchProtectJsonObject = self.checkBranchProtection(repoName, branchName)
            if branchProtectJsonObject:
                bpDelResponse = self.deleteBranchProtection(repoName, branchName)
                if bpDelResponse:
                    logging.info("removeRestrictions: Deleted branch protection for branch {}".format(branchName))
                    print("removeRestrictions: Deleted branch protection for branch", branchName)
            else:
                logging.info("removeRestrictions: No branch protection to delete for branch {}".format(branchName))
                print("removeRestrictions: No branch protection to delete for branch {} ".format(branchName))

            hookStatus = self.checkHooks(repoName)
            if hookStatus:
                deletedHook = self.deleteHook(repoName)
                if deletedHook:
                    logging.info("removeRestrictions: Deleted hooks for branch {}".format(branchName))
                    print("removeRestrictions: Deleted hooks for branch", branchName)
            else:
                logging.info("removeRestrictions: No hooks to delete for branch {}".format(branchName))
                print("removeRestrictions: No hooks to delete for branch", branchName)
        except Exception as e:
            print("removeRestrictions: Exception Occurred:\n", e)
            logging.exception("removeRestrictions: Exception Occurred : {}".format(e))
            raise Exception("Exception while removeRestrictions.", e)
        return bpDelResponse, deletedHook

    def getFileContents(self, repoName, branchName, fileName):
        """
        This method is used to fetch contents of a input file from input repo
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :param fileName: Name of the file
        :return contents: Contents of the file
        """
        contents = []
        try:
            repo = self.dmc.get_repo(repoName)
            contents = repo.get_contents(fileName, branchName)
            logging.info("getFileContents : Fetched data from file - {}".format(fileName))
        except Exception as e:
            print("getFileContents: Encountered exception: ", e)
            logging.exception("getFileContents: Encountered exception:{}".format(e))
            raise Exception("Exception while fetching file contents.", e)
        return contents

    def getJsonFile(self, repoName, branchName, fileName):
        """
        This method is used to fetch contents of a input json from a input repo
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :param fileName: Name of the file
        :return data: Input Json
        """
        data = {}
        try:
            contents = self.getFileContents(repoName, branchName, fileName)
            file_data = base64.b64decode(contents.content, altchars=None)
            data = json.loads(file_data)
            logging.info("getJsonFile : Fetched data from file - {}".format(fileName))
        except Exception as e:
            print("getJsonFile: Encountered exception: ", e)
            logging.exception("getJsonFile: Encountered exception: {}".format(fileName))
            raise Exception("Exception while fetching Json File.", e)
        return data

#     def getCSVFile(self, repoName, branchName, fileName):
#         """
#         This method is used to fetch contents of a input CSV from a input repo
#         :param repoName: Name of github repo
#         :param branchName: Name of the branch
#         :param fileName: Name of the file
#         :return data: dict of CSV file
#         """
#         data = {}
#         try:
#             contents = self.getFileContents(repoName, branchName, fileName)
#             filedata = base64.b64decode(contents.content, altchars=None).decode("utf-8", "ignore")
#             csvData = StringIO(filedata)
#             df = pd.read_csv(csvData, sep=",")
#             data = df.to_dict('index')
#             logging.info("getCSVFile : Input Dictionary : {}".format(data))
#         except Exception as e:
#             print("getCSVFile : Exception occured : {}".format(e))
#             logging.exception("getCSVFile : Exception occured : {}".format(e))
#             raise Exception("Exception while reading CSV file.", e)
#         return data

    def uploadFile(self, repoName, branchName, fileList, commitMessage):
        """
        This method is used to upload file to github
        :param repoName: Name of github repo
        :param branchName: Name of the branch
        :param fileList: The list of files to be uploaded.
        :param commitMessage: Message after commit
        """
        try:
            repo = self.dmc.get_repo(repoName)
            masterRef = repo.get_git_ref('heads/' + branchName)
            masterSha = masterRef.object.sha
            baseTree = repo.get_git_tree(masterSha)
            elementList = list()
            for filePath in fileList:
                fileName = filePath.split("/")[-1]
                with open(fileName) as inputFile:
                    data = inputFile.read()
                element = InputGitTreeElement(filePath, '100644', 'blob', data)
                elementList.append(element)
            tree = repo.create_git_tree(elementList, baseTree)
            parent = repo.get_git_commit(masterSha)
            commit = repo.create_git_commit(commitMessage, tree, [parent])
            masterRef.edit(commit.sha)
            logging.info("uploadFile: Files uploaded to Github")

        except Exception as e:
            print("uploadFile: Exception occurred :", e)
            logging.exception("uploadFile: Exception occurred : {}".format(e))
            raise Exception("Exception while uploading files to Git.", e)


class GitError(Exception):
    def __init__(self, message=None, http_status=None, http_message=None):
        self.message = message
        self.http_message = http_message
        self.http_status = http_status

    def __str__(self):
        return repr(f'Error while invoking jira endpoint. {self.message}. Received HTTP '
                    f'status code: {self.http_status} with response {self.http_message}')