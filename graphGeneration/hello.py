
from PIL import Image
import cv2
import pandas as pd
import numpy as np
import logging
import base64
from github import Github, InputGitTreeElement
import requests
import matplotlib.pyplot as plt
import warnings
import json
from collections import defaultdict
import datetime
import os
import six
import matplotlib.dates as mdates
import sys
import time
from git import Git

def uploadFileToGithub(dmc, repoName, filePath, commitMessage):
    try:
        repo = dmc.get_repo(repoName)
        fileName = filePath.split("/")[-1]
        # fileList = [fileName]
        fileNames = [filePath]
        masterRef = repo.get_git_ref('heads/master')
        masterSha = masterRef.object.sha
        baseTree = repo.get_git_tree(masterSha)
        elementList = list()
        for i, entry in enumerate(fileNames):
            with open(entry) as inputFile:
                data = inputFile.read()
            element = InputGitTreeElement(fileNames[i], '100644', 'blob', data)
            elementList.append(element)
        tree = repo.create_git_tree(elementList, baseTree)
        parent = repo.get_git_commit(masterSha)
        commit = repo.create_git_commit(commitMessage, tree, [parent])
        masterRef.edit(commit.sha)
        print("uploadFileToGithub: ", fileName, " uploaded in repo :", repoName)
        logging.info("uploadFileToGithub: %s uploaded in repo %s", fileName, repoName)
    except Exception as e:
        print("uploadFileToGithub: Exception occurred :", e)
        logging.exception("uploadFileToGithub: Exception occurred : %s", e)

# def restrictedUpload(repoName, branchName, org, filePath, commitMessage):
#     """
#     Upload the file in the given repository and branchName by checking restrictions(hooks and branch protection).
#     :param repoName: Name of the repository
#     :type repoName: string
#     :param branchName: Name of the branch
#     :type branchName: string
#     :param org: object for github organization
#     :type org: github object
#     :param filePath: list of file to be uploaded
#     :type filePath: list
#     :param commitMessage: the message that needs to be committed along with the file
#     :type commitMessage: string
#     :return none
#     """
#     try:
#         # branchProtectJsonObject = org.checkBranchProtection(repoName, branchName)
#         # deletedHook, deletedBranchProtection = org.removeRestrictions(repoName, branchName)
#         # if ((deletedHook is not None and not deletedHook) and (deletedBranchProtection is not None and not deletedBranchProtection)):
#         #     print("restrictedUpload: Unable to remove branch restrictions!")
#         #     logging.info("restrictedUpload: Unable to remove branch restrictions!")
#         # else:
#             org.uploadFile(repoName, branchName, filePath, commitMessage)
#             # org.recastRestrictions(repoName, branchName, branchProtectJsonObject)

#     except Exception as e:
#         print("restrictedUpload: Exception occurred:", e)
#         logging.exception("restrictedUpload: Exception occurred: %s", e)

def initializeOrg(url, accessToken, org):
    """
    Initialize Organisation object
    :param url: github URL
    :type url: str
    :param accessToken: Git accessToken
    :type accessToken: str
    :return dmc: Organisation object
    :type dmc: github org object
    """
    dmc = None
    try:
        g = Github(base_url=url, login_or_token=accessToken)
        dmc = g.get_organization(org)
        logging.info("initializeOrg: Organization: {}".format(dmc))

    except Exception as e:
        print("initializeOrg: Exception occurred: {}".format(e))
        logging.exception("initializeOrg: Exception occurred: {}".format(e))

    return dmc

def main():

    print(os.getcwd())

    if os.path.exists("./graphs/repos/repoBar.png"):
        print("true")

        img = cv2.imread("./graphs/repos/repoBar.png")     
 
# Output Images
        cv2.imshow("img",img)

    # toolsUrl = 'https://github.tools.sap/api/v3'
    # gitToken = "619f4f563ba7135480d8a8ad7a279c0917b8578f"
    # dmc = initializeOrg(toolsUrl, gitToken, "TempOrg")
    # print(dmc)
    
    

    # uploadFileToGithub(dmc,"Test2.O", "graphGeneration/graphs/repos/repoBar.png", "[skip-ci] update file")

    # restrictedUpload("Test2.O", "master", tmp, ["graphs/repos/repoBar.png"], "[skip-ci] update file")
if __name__ == "__main__":
    main()
