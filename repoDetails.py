import requests
import json
from github import Github, InputGitTreeElement
import warnings
import datetime
from tqdm import tqdm
import time
import logging
import sys
import os
from pypipes import Git

warnings.filterwarnings("ignore")
timestr = time.strftime("%Y%m%d-%H%M%S")
logFile = 'logfile-prAnalysis' + timestr + '.log'
logging.basicConfig(filename=logFile, level=logging.DEBUG)


def getPrJSON(repoName, endCursor, token):
    """
    fetching details of PR JSON  
    :param repoName: name of repo 
    :type repoName: string
    :param endCursor: cursor end
    :type endCursor: string
    :param token: gitHub token
    :type token: string
    :return data: json response
    :type data: json obj 
    """
    data = ""
    try:
        query = """{{
            rateLimit{{
                remaining
            }}
            organization(login: "DigitalManufacturing") {{
                repository(name: "{}"){{
                pullRequests(first:50, after: {}){{
                    nodes{{
                    id
                    number
                    title
                    state
                    closed
                    author{{
                        ... on User{{
                        name
                        login
                        }}
                    }}
                    mergedBy{{
                        ... on User{{
                        name
                        login
                        }}
                    }}
                    reviewRequests(first:100){{
                        nodes{{
                        requestedReviewer{{
                            ... on User{{
                            name
                            login
                            }}
                        }}
                        }}
                    }}
                    createdAt
                    closedAt
                    updatedAt
                    mergedAt
                    changedFiles
                    deletions
                    additions
                    commits{{
                        totalCount
                    }}
                    comments{{
                        totalCount
                    }}
                    }}
                    pageInfo{{
                    endCursor
                    hasNextPage
                    }}
                }}
                }}
            }}
            }}"""
        url = 'https://github.tools.sap/api/graphql'
        endCursor = '"' + endCursor + '"' if endCursor else "null"
        response = requests.post(url,
                                 json={'query': query.format(
                                     repoName, endCursor)},
                                 headers={
                                     "Authorization": "token " + token
                                 },
                                 verify=False)
        data = response.json()
    except Exception as e:
        print("getPrJSON: Exception occured: ", e)
        logging.exception("getPrJSON: Exception occured: {}".format(e))

    return data


def getPrReviewJSON(repoName, prNumber, endCursor, token):
    """
    fetching details of PR review threads  
    :param repoName: name of repo 
    :type repoName: string
    :param prNumber: pr number
    :type prNumber: string
    :param endCursor: cursor end
    :type endCursor: string
    :param token: gitHub token
    :type token: string
    :return data: json response
    :type data: json obj 
    """
    data = ""
    try:
        query = """{{
            rateLimit{{
                remaining
            }}
        organization(login: "DigitalManufacturing") {{
            repository(name: "{}") {{
            pullRequest(number: {}) {{
                reviewThreads(first: 100, after: {}) {{
                nodes {{
                    isResolved
                    comments(first: 100, after: null) {{
                    totalCount
                    nodes {{
                        author {{
                        ... on User {{
                            name
                            login
                        }}
                        }}
                        body
                        path
                        pullRequestReview {{
                        state
                        }}
                        createdAt
                    }}
                    }}
                }}
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                }}
            }}
            }}
        }}
        }}"""
        url = 'https://github.tools.sap/api/graphql'
        endCursor = '"' + endCursor + '"' if endCursor else "null"
        response = requests.post(url,
                                 json={'query': query.format(repoName, prNumber, endCursor)},
                                 headers={
                                     "Authorization": "token " + token
                                 },
                                 verify=False)
        data = response.json()
    except Exception as e:
        print("getPrReviewJSON: Exception occurred: ", e)
        logging.exception("getPrReviewJSON: Exception occurred: {}".format(e))

    return data


def findingTimeBwReviews(firstReviewDate, lastReviewDate, pr):
    """
    Calculate pre-review time and post-review time
    :param firstReviewDate: datetime when the first review comment was made
    :type firstReviewDate: datetime
    :param lastReviewDate: datetime when the last review comment was made
    :type lastReviewDate: datetime
    :param pr: Contains all the information about a single pr
    :type pr: dict
    :returns preReviewTime, postReviewTime: tuple of preReviewTime, postReviewTime
    :type preReviewTime, postReviewTime: tuple
    """
    try:
        preReviewTime = postReviewTime = None
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        if firstReviewDate:
            preReviewTime = firstReviewDate - \
                datetime.datetime.strptime(pr["opened_at"], datetime_format)
            preReviewTime = str(round(
                preReviewTime.total_seconds()/60, 2)) + " Min"
        if pr["closed_at"] and lastReviewDate:
            postReviewTime = datetime.datetime.strptime(
                pr["closed_at"], datetime_format) - lastReviewDate
            postReviewTime = str(round(
                postReviewTime.total_seconds()/60, 2)) + " Min"
    except Exception as e:
        print("findingTimeBwReviews: Exception occurred: ", e)
        logging.exception("findingTimeBwReviews: Exception occurred: {}".format(e))

    return preReviewTime, postReviewTime


def getPrCmntsJSON(repoName, prNumber, endCursor, token):
    """
    fetching details of PR JSON by firing a query 
    :param repoName: name of repo 
    :type repoName: str
    :param prNumber: pr number
    :type prNumber: str
    :param endCursor: cursor end
    :type endCursor: str
    :param token: gitHub token
    :type token: str
    :return data: json response
    :type data: json obj 
    """    
    data = ""
    try:
        query = """{{
            rateLimit {{
                remaining
            }}
            organization(login: "DigitalManufacturing") {{
                repository(name: "{}") {{
                pullRequest(number: {}) {{
                    comments(first: 100, after: {}) {{
                    nodes {{
                        author {{
                        ... on User {{
                            name
                            login
                        }}
                        }}
                        body
                        createdAt
                    }}
                    pageInfo {{
                        endCursor
                        hasNextPage
                    }}
                    }}
                }}
                }}
            }}
            }}"""
        url = 'https://github.tools.sap/api/graphql'
        endCursor = '"' + endCursor + '"' if endCursor else "null"
        response = requests.post(url,
                                 json={'query': query.format(repoName, prNumber, endCursor)},
                                 headers={
                                     "Authorization": "token " + token
                                 },
                                 verify=False)
        data = response.json()
    except Exception as e:
        print("getPrCmntsJSON: Exception occurred: {}".format(e))
        logging.exception("getPrCmntsJSON: Exception occurred: {}".format(e))

    return data


def convertToDatetime(date):
    """
    Convert JSON Datetime to python datetime object
    :param date: JSON Datetime
    :type date: string
    :return datetime: python datetime object
    :type datetime: datetime
    """   
    try:
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        if date:
            return datetime.datetime.strptime(
                date, datetime_format)
        return None

    except Exception as e:
        print("convertToDatetime: Exception occured: {}".format(e))
        logging.exception("convertToDatetime: Exception occured: {}".format(e))


def convertToFile(dictionary, fileName):
    """
    writing dictionaries into json file
    :param dictionary: dictionary containing data
    :type dictionary: dict
    :param fileName: name of the json file
    :type fileName: string
    :return none
    """   
    try:
        with open(fileName, 'w') as jsonFile:	
            json.dump(dictionary, jsonFile, indent=4)
        logging.info("convertToFile: Json file generated: {}".format(fileName))
        print("convertToFile: Json file generated: ", fileName)

    except Exception as e:
        print("convertToFile: Exception occurred: ", e)
        logging.exception("convertToFile: Exception occurred: {}".format(e))


def getPrRvwJSON(gitToken, prDetails, exceptionList):
    """
    fetching details of PRs reviews of every repo 
    :param gitToken: github access token
    :type gitToken: string
    :param repoList: list of repos
    :type repoList: list
    :param exceptionList: list of exceptions
    :type exceptionList: list
    :return prDetails
    :type prDetails: dict
    :return exceptionList: list of exceptions
    :type exceptionList: list
    """   
    exceptionCount = 0
    igt = 0
    try:
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        logging.info("\ngetPrRvwJSON: Fetching PR Reviews")
        print("\ngetPrRvwJSON: Fetching PR Reviews")

        # iterating over repos to fetch PR reviews
        for repoName in prDetails:
            try:
                for pr in tqdm(prDetails[repoName], desc="fetching PR rvws for repoName: {}".format(repoName)):
                    rvw_thrds, reviewers, firstReviewDate, lastReviewDate = [], set(), None, None
                    endCursor, hasNextPage = None, True
                    try:
                        while (hasNextPage):
                            # getting PRs reviews JSON data
                            try:
                                data = getPrReviewJSON(repoName, prDetails[repoName][pr]["PR_number"], endCursor, gitToken[igt])
                                if data == "":
                                    print("getPrRvwJSON: retrieving pr data is unsuccessful for repo {}".format(repoName))
                                    logging.info("getPrRvwJSON: retrieving pr data is unsuccessful for repo {}".format(repoName))
                                    hasNextPage = False
                                else:
                                    if data["data"]["rateLimit"]["remaining"] < 100:
                                        logging.info("getPrRvwJSON: Token limit < 100 - pausing the updating for 1 min")
                                        time.sleep(60)
                                        logging.info("getPrRvwJSON: Updation started - token changed to new one")
                                        igt = (igt + 1) % len(gitToken)
                                        print("getPrRvwJSON: access token changed")
                                        logging.info("getPrRvwJSON: accessToken Changed")

                                    if data["data"]["organization"]["repository"] is not None:
                                        data = data["data"]["organization"]["repository"]["pullRequest"]["reviewThreads"]
                                        endCursor = data["pageInfo"]["endCursor"]
                                        hasNextPage = data["pageInfo"]["hasNextPage"]
                                        for rvw_thrd in data["nodes"]:
                                            first_thrd_cmt = last_thrd_cmt = None
                                            # Populating Review Thread object(JSON)
                                            rvw_thrd_object = {
                                                "is_resolved": rvw_thrd["isResolved"],
                                                "comments": [],
                                                "thread_duration": None,
                                            }
                                            # Adding comments count to total_review_comments
                                            prDetails[repoName][pr]["total_review_comments"] += rvw_thrd["comments"]["totalCount"]
                                            for comment in rvw_thrd["comments"]["nodes"]:
                                                # Populating the comment object structure(JSON)
                                                comment_obj = {
                                                    "user": comment["author"],
                                                    "for_file": comment["path"],
                                                    "body": comment["body"],
                                                    "state": comment["pullRequestReview"]["state"],
                                                    "posted_at": comment["createdAt"]
                                                }
                                                if comment_obj["user"] and comment_obj["user"] != prDetails[repoName][pr][
                                                    "user"] and comment_obj["user"] not in prDetails[repoName][pr]["reviewers"]:
                                                    prDetails[repoName][pr]["reviewers"].append(comment_obj["user"])

                                                # Finding when was the first and last comment made in the thread
                                                first_thrd_cmt = min(
                                                    convertToDatetime(comment_obj["posted_at"]),
                                                    first_thrd_cmt) if first_thrd_cmt else convertToDatetime(
                                                    comment_obj["posted_at"])
                                                last_thrd_cmt = max(
                                                    convertToDatetime(comment_obj["posted_at"]),
                                                    last_thrd_cmt) if last_thrd_cmt else convertToDatetime(
                                                    comment_obj["posted_at"])
                                                # Finding when was the first and last comment made for all the PR
                                                firstReviewDate = min(
                                                    convertToDatetime(comment_obj["posted_at"]),
                                                    firstReviewDate) if firstReviewDate else convertToDatetime(
                                                    comment_obj["posted_at"])
                                                lastReviewDate = max(
                                                    convertToDatetime(comment_obj["posted_at"]),
                                                    lastReviewDate) if lastReviewDate else convertToDatetime(
                                                    comment_obj["posted_at"])
                                                rvw_thrd_object["comments"].append(comment_obj)

                                            # Calculating thread duration
                                            if first_thrd_cmt and last_thrd_cmt:
                                                diff = last_thrd_cmt - first_thrd_cmt
                                                rvw_thrd_object["thread_duration"] = str(
                                                    round(diff.total_seconds() / 60, 2)) + " Min"
                                            # Adding thread object to the all threads list
                                            rvw_thrds.append(rvw_thrd_object)
                                    else:
                                        hasNextPage = False

                            except Exception as e:
                                logging.exception("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception".format(e))
                                print("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception".format(e))
                                print("PR number: {} and repoName: {}".format(pr, repoName))
                                exceptionList.append("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception PR number: {} and repoName: {}\n".format(e, pr, repoName))
                                exceptionCount += 1
                                continue

                        # Making changes to local file PR object
                        prDetails[repoName][pr]["review_threads"] = rvw_thrds
                        preReviewTime, postReviewTime = findingTimeBwReviews(
                            firstReviewDate, lastReviewDate, prDetails[repoName][pr])
                        prDetails[repoName][pr]["pre_review_time"] = preReviewTime
                        prDetails[repoName][pr]["post_review_time"] = postReviewTime
                        if firstReviewDate and lastReviewDate:
                            dur = round(
                                (lastReviewDate - firstReviewDate).total_seconds() / 60, 2)
                            if dur:
                                prDetails[repoName][pr]["inspection_rate"] = str(
                                    round((prDetails[repoName][pr]["changes"]["added"] + prDetails[repoName][pr]["changes"][
                                        "deleted"]) / dur, 2)) + " loc/min"
                            prDetails[repoName][pr]["inspection_time"] = str(
                                round((lastReviewDate - firstReviewDate).total_seconds() / 60, 2)) + " Min"
                    except Exception as e:
                        logging.exception("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception".format(e))
                        print("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception".format(e))
                        print("PR number: {} and repoName: {}".format(pr, repoName))
                        exceptionList.append("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception PR number: {} and repoName: {}\n".format(e, pr, repoName))
                        exceptionCount += 1
                        continue

            except Exception as e:
                print("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception in repo: {}".format(e, repoName))
                logging.exception("getPrRvwJSON: Exception occurred: {} getting pr reviews ended with exception in repo: {}".format(e, repoName))
                exceptionCount += 1
                continue

        logging.info("getPrRvwJSON: fetching Reviews Script completed successfully")
        print("getPrRvwJSON: fetching Reviews Script completed successfully")

    except Exception as e:
        print("getPrRvwJSON: Exception occurred: ", e)
        logging.exception("getPrRvwJSON: Exception occurred: {}".format(e))
    logging.info("getPrRvwJSON: Exception count: {}\n".format(exceptionCount))
    print("getPrRvwJSON: Exception count: {}\n".format(exceptionCount))

    return prDetails, exceptionList


def getPrCmnts(gitToken, prDetails, exceptionList):
    """
    fetching details of PRs comments of every repo 
    :param gitToken: github access token
    :type gitToken: string
    :param repoList: list of repos
    :type repoList: list
    :param exceptionList: list of exceptions
    :type exceptionList: list
    :return prDetails
    :type: dict
    :return exceptionList: list of exceptions
    :type exceptionList: list
    """    
    exceptionCount = 0
    igt = 0
    try:
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        logging.info("\ngetPrCmnts: Fetching PR Comments")
        print("\ngetPrCmnts: Fetching PR Comments")

        # iterating over repos and PRs to fetch general comments
        for repoName in prDetails:
            try:
                for pr in tqdm(prDetails[repoName], desc="fetching PR cmnts of repo: {}".format(repoName)):
                    endCursor, hasNextPage = None, True
                    while (hasNextPage):
                        # getting PRs comments JSON data
                        try:
                            data = getPrCmntsJSON(repoName, prDetails[repoName][pr]["PR_number"], endCursor, gitToken[igt])
                            if data == "":
                                print("getPrCmnts: retrieving pr data is unsuccessful for repo {}".format(repoName))
                                logging.info("getPrCmnts: retrieving pr data is unsuccessful for repo {}".format(repoName))
                                hasNextPage = False
                            else:
                                if data["data"]["rateLimit"]["remaining"] < 100:
                                    logging.info("getPrCmnts: Token limit < 100 - pausing the updating for 1 min")
                                    time.sleep(60)
                                    logging.info("getPrCmnts: Updation started - token changed to new one")
                                    igt = (igt + 1) % len(gitToken)
                                    print("getPrCmnts: access token changed" + igt)
                                    logging.info("getPrCmnts: access token changed" + igt)

                                if data["data"]["organization"]["repository"] is not None:
                                    data = data["data"]["organization"]["repository"]["pullRequest"]["comments"]
                                    endCursor = data["pageInfo"]["endCursor"]
                                    hasNextPage = data["pageInfo"]["hasNextPage"]
                                    # iterating over nodes in json data
                                    for comment in data["nodes"]:
                                        # populating general comments data
                                        prDetails[repoName][pr]["general_comments"].append({
                                            "user": comment["author"],
                                            "body": comment["body"],
                                            "posted_at": comment["createdAt"]
                                        })
                                else:
                                    hasNextPage = False

                        except Exception as e:
                            logging.exception("getPrCmnts: Exception occurred: {} getting pr comments ended with exception".format(e))
                            print("getPrCmnts: Exception occurred: {} getting pr comments ended with exception".format(e))
                            print("PR number: {} and repoName: {}".format(pr, repoName))
                            exceptionList.append("getPrCmnts: Exception occurred: {} getting pr comments ended with exception PR number: {} and repoName: {}\n".format(e, pr, repoName))
                            exceptionCount += 1
                            continue

            except Exception as e:
                logging.exception("getPrCmnts: Exception occurred: {} fetching pr comments ended with exception in repo: {}".format(e,repoName))
                print("getPrCmnts: Exception occurred: {} fetching pr comments ended with exception in repo: {}".format(e,repoName))
                exceptionCount += 1
                continue

        logging.info("getPrCmnts: Comments script completed successfully")
        print("getPrCmnts: Comments script completed successfully")
        
    except Exception as e:
        print("getPrCmnts: Exception occurred: {}".format(e))
        logging.exception("getPrCmnts: Exception occurred: {}".format(e))
    logging.info("getPrCmnts: Exception count: {}".format(exceptionCount))
    print("getPrCmnts: Exception count: {}".format(exceptionCount))

    return prDetails, exceptionList


def prDetails(gitToken, repoList, startDate, endDate):
    """
    fetching details of PRs of every repo and writing it into json file
    :param gitToken: github access token
    :type gitToken: string
    :param repoList: list of repos
    :type repoList: list
    :param startDate: start date
    :type startDate: string
    :param endDate: end date
    :type endDate: string 
    :return repoPrDict: dictionary of repos and pr's
    :type repoPrDict: dict
    """    
    exceptionList = []
    exceptionCount = 0
    repoPrDict = {}
    igt = 0
    try:
        logging.info("prDetails: Fetching PR Details")
        print("prDetails: Fetching PR Details")
        startDate = convertToDatetime(startDate)
        endDate = convertToDatetime(endDate)

        # iterating each repo for getting PRs
        for repoName in tqdm(repoList, total= len(repoList), desc="prDetails"):
            consolidatedJSON = {}
            prCount = 0
            endCursor, hasNextPage = None, True
            try:
                while (hasNextPage):
                    try:
                        # getting PRs JSON data using api call
                        data =  getPrJSON(repoName, endCursor, gitToken[igt])
                        if data == "":
                            print("prDetails: retrieving pr data is unsuccessful for repo {}".format(repoName))
                            logging.info("prDetails: retrieving pr data is unsuccessful for repo {}".format(repoName))
                            hasNextPage = False
                        else:
                            if data["data"]["rateLimit"]["remaining"] < 100:
                                logging.info("prDetails: Token limit < 100 - pausing the updating for 1 min")
                                time.sleep(60)
                                logging.info("prDetails: Updation started - token changed to new one")
                                igt = (igt + 1) % len(gitToken)
                                print("prDetails: access token changed" + igt)
                                logging.info("prDetails: access token changed" + igt)

                            if data["data"]["organization"]["repository"] is not None:
                                data = data["data"]["organization"]["repository"]["pullRequests"]
                                endCursor = data["pageInfo"]["endCursor"]
                                hasNextPage = data["pageInfo"]["hasNextPage"]

                                # iterating over nodes in json data
                                for pr in data["nodes"]: 
                                    try:
                                        prDetails = ""
                                        closedAt = convertToDatetime(pr["closedAt"])
                                        openedAt = convertToDatetime(pr["createdAt"])
                                        merged_at = convertToDatetime(pr["mergedAt"])
                                        updated_at = convertToDatetime(pr["updatedAt"])
                                        reviewDuration = reviewRate = None

                                        if startDate <= openedAt:
                                                if closedAt:
                                                    dur = round((closedAt - openedAt).total_seconds() / 60, 2)
                                                    if dur:
                                                        reviewRate = str(round((pr["additions"] + pr["deletions"]) / dur, 2)) + " loc/min"
                                                    reviewDuration = str(dur) + " Min"

                                                # populating prDetails obj with PR detail values
                                                prDetails = {
                                                    "PR_number": pr["number"],
                                                    "title": pr["title"],
                                                    "id": pr["id"],
                                                    "status": pr["state"],
                                                    "is_closed": pr["closed"],
                                                    "user": pr["author"],
                                                    "changes": {
                                                        "added": pr["additions"],
                                                        "deleted": pr["deletions"],
                                                        "changed_file": pr["changedFiles"]
                                                    },
                                                    "opened_at": pr["createdAt"],
                                                    "closed_at": pr["closedAt"],
                                                    "merged_at": pr["mergedAt"],
                                                    "updated_at": pr["updatedAt"],
                                                    "preReviewTime": None,
                                                    "post_review_time": None,
                                                    "review_duration": reviewDuration,
                                                    "review_rate": reviewRate,
                                                    "inspection_time": None,
                                                    "inspection_rate": None,
                                                    "review_threads": [],
                                                    "total_review_comments": 0,
                                                    "general_comments": [],
                                                    "total_general_comments": pr["comments"]["totalCount"],
                                                    "total_commits": pr["commits"]["totalCount"],
                                                    "reviewers": [req_rvw["requestedReviewer"] for req_rvw in
                                                                pr["reviewRequests"]["nodes"]],
                                                    "resolver": pr["author"],
                                                    "approver": pr["mergedBy"],
                                                }
                                                # contains all the PRs of a repo
                                        
                                        if prDetails != "" :
                                            consolidatedJSON[f"PR{pr['number']}"] = prDetails  
                                            prCount = prCount + 1
                                            
                                    except Exception as e:
                                        print("prDetails: Exception occurred: {} getting prDetails ended with exception".format(e))
                                        print("PR number: {} and repoName: {}".format(pr, repoName))
                                        exceptionList.append("prDetails: Exception occurred: {} getting prDetails ended with exception PR number: {} and repoName: {}\n".format(e, pr, repoName))
                                        logging.exception("prDetails: Exception occurred: {} getting prDetails ended with exception".format(e))
                            else:
                                hasNextPage = False
                            
                    except Exception as e:
                        print("prDetails: Exception occurred: {} getting prDetails ended with exception".format(e))
                        logging.exception("prDetails: Exception occurred: {} getting prDetails ended with exception".format(e))

                # contains all the PRs mapped to repo
                repoPrDict[repoName] = consolidatedJSON  
                print("\nrepoName: {} with total no. of prs: {}\n".format(repoName, prCount))
                
            except Exception as e:
                print("prDetails: Exception occurred: {} getting prDetails ended with exception in repo: {}".format(e, repoName))
                logging.exception("prDetails: Exception occurred: {} getting prDetails ended with exception in repo: {}".format(e, repoName))

        # getting PR comments	
        repoPrDict, exceptionList = getPrCmnts(gitToken, repoPrDict, exceptionList)

        # getting PR reviews	
        repoPrDict, exceptionList = getPrRvwJSON(gitToken, repoPrDict, exceptionList)        

        #writing exceptionList in txt file if any
        if exceptionList:
            f = open("exceptionalSummary.txt", "a+")        
            for excp in exceptionList:
                f.write(excp)
            f.close()

        logging.info("prDetails: Fetching PR Details process updated successfully")
        print("prDetails: Fetching PR Details process updated successfully")

    except Exception as e:
        print("prDetails: Exception occurred: {}".format(e))
        logging.exception("prDetails: Exception occurred: {}".format(e))

    logging.info("prDetails: Exception count: {}".format(exceptionCount))
    print("prDetails: Exception count: {}".format(exceptionCount))

    return repoPrDict


def restrictedUpload(repoName, branchName, org, filePath, commitMessage):
    """
    Upload the file in the given repository and branchName by checking restrictions(hooks and branch protection).
    :param repoName: Name of the repository
    :type repoName: string
    :param branchName: Name of the branch
    :type branchName: string
    :param org: object for github organization
    :type org: github object
    :param filePath: list of file to be uploaded
    :type filePath: list
    :param commitMessage: the message that needs to be committed along with the file
    :type commitMessage: string
    :return none
    """
    try:
        branchProtectJsonObject = org.checkBranchProtection(repoName, branchName)
        deletedHook, deletedBranchProtection = org.removeRestrictions(repoName, branchName)
        if ((deletedHook is not None and not deletedHook) and (deletedBranchProtection is not None and not deletedBranchProtection)):
            print("restrictedUpload: Unable to remove branch restrictions!")
            logging.info("restrictedUpload: Unable to remove branch restrictions!")
        else:
            org.uploadFile(repoName, branchName, filePath, commitMessage)
            org.recastRestrictions(repoName, branchName, branchProtectJsonObject)

    except Exception as e:
        print("restrictedUpload: Exception occurred:", e)
        logging.exception("restrictedUpload: Exception occurred: %s", e)


def main():
    try:
        start = time.time()
        logging.info("main : Start time = %.3f seconds", start)

        #format of startDate - endDate are : yyyy-mm-dd 
        startDate = os.getenv("START_DATE")
        endDate = os.getenv("END_DATE")
        startDate = startDate + "T0:0:0Z"
        endDate = endDate +  "T0:0:0Z"
        
        url = "https://github.tools.sap/api/v3"                                 
        token = os.getenv("GIT_TOKEN")
        gitToken = list(token.split(","))

        #Initialize git organization
        dmc = Git(url, gitToken[0])
        if not dmc.connected:
            print("Unable to authenticate with Github Tools org 'DigitalManufacturing'")
            logging.info("Unable to authenticate with Github Tools org 'DigitalManufacturing'")
            sys.exit(1)

        
        #getting list of repos
#         repoList = dmc.getRepoNamesList()
        repoList = ["dmc-devops-reports"]
        if not repoList:
            print("Unable to Fetch repoList from org 'DigitalManufacturing'")
            logging.info("Unable to Fetch repoList from org 'DigitalManufacturing'")
            sys.exit(1)
            
        # for getting pr json dict         
        repoPr = prDetails(gitToken, repoList, startDate, endDate)
        
        # Generating and uploading JSON file to GitHub.  
        convertToFile(repoPr, "repoPrDetails.json")

        #uploading to github
#         restrictedUpload("dmc-pr-insights", "master", dmc, ["repoDataGeneration/repoPrDetails.json"], "[skip-ci] update repoPrDetails.json file")

    except Exception as e:
        logging.exception("main: Exception occurred: {}".format(e))
        print("main: Exception occurred: {}".format(e))
        sys.exit(1) 
    
    finally:
        end = time.time()
        logging.info("main: End time = %.3f seconds", end)
        print("main: Total Execution Time in seconds = ", (end - start))
        logging.info("main: Total execution time = %.3f seconds", (end - start))


if __name__ == "__main__":
    main()
