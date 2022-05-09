
import pandas as pd
import numpy as np
import logging
import base64
from github import Github
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


warnings.filterwarnings("ignore")
timestr = time.strftime("%Y%m%d-%H%M%S")
logFile = 'logfile-prAnalysisReport' + timestr + '.log'
logging.basicConfig(filename=logFile, level=logging.DEBUG)

def convertToDatetime(date):
    """
    Convert JSON Datetime to python datetime object
    :param date: JSON Datetime
    :type date: str
    :return datetime: python datetime object
    :type datetime: datetime
    """
    dateTimeVal = None
    try:
        datetimeFormat = "%Y-%m-%dT%H:%M:%SZ"
        if date:
            dateTimeVal = datetime.datetime.strptime(
                date, datetimeFormat)          

    except Exception as e:
        print("convertToDatetime: Exception: {}".format(e))
        logging.exception("convertToDatetime: Exception: {}".format(e))

    return dateTimeVal

def repoCount(teamRepoDict, allData):
    """
    Retrieves count of repos and owners and returns the repo dict mapped with team names
    :param teamRepoDict: Name of the Team mapped with repos
    :type teamRepoDict: dict
    :param allData: default dictionary that contains all the required data
    :type allData: dict
    :return allData: default dictionary that contains all the required data
    :type allData: dict
    :return repoDict: Dictionary containing all the repositories
    :type repoDict: dict
    """
    repoDict = {}
    try:
        for teamName in teamRepoDict:
            repos = set()
            owners = set()
            for repoOwner in teamRepoDict[teamName]:
                if repoOwner == "validRepoList":
                    for repo in teamRepoDict[teamName][repoOwner]:
                        repos.add(repo)
                if repoOwner == "codeOwnersList":
                    for owner in teamRepoDict[teamName][repoOwner]:
                        owners.add(owner)

            allData[f"{teamName}"]["repos"] = len(repos)
            allData[f"{teamName}"]["owners"] = len(owners)
            repoDict[teamName] = repos

    except Exception as e:
        print("repoCount: Exception occurred: {}".format(e))
        logging.exception("repoCount: Exception occurred: {}".format(e))

    return allData, repoDict


def prInfo(allData, repoDict, token):
    """
    To fetch all the PR information from github 
    :param org: object of github DigitalManufacturing
    :type org: github object
    :param allData: default dictionary that contains all the required data
    :type allData: dict
    :param repoDict: Dictionary containing all the repositories and codeOwners mapped to team names
    :type repoDict: dict
    :return allData: default dictionary that contains all the required data
    :type allData: dict
    """
    
    try:
        fileSha = getFileSha(token, "dmc-pr-insights", "repoDataGeneration", "repoPrDetails.json")
        prDict = parseJsonFile(token, "dmc-pr-insights", fileSha)
               
        for teamName in repoDict:
                for teamRepo in repoDict[teamName]:
                    for repo in prDict:
                        if repo == teamRepo:
                            for pr in prDict[repo]:
                                try:
                                    createdAt = (prDict[repo][pr]["opened_at"])
                                    closedAt = (prDict[repo][pr]["closed_at"])
                                    updatedAt = (prDict[repo][pr]["updated_at"])
                                    mergedAt = (prDict[repo][pr]["merged_at"])

                                    if mergedAt:
                                        if prDict[repo][pr]["approver"]:
                                            if prDict[repo][pr]["approver"]["name"] is None:
                                                prDict[repo][pr]["approver"]["name"] = prDict[repo][pr]["approver"]["login"]
                                            allData[teamName]["approvers"][prDict[repo][pr]["approver"]["name"]] += 1
                                    
                                    if createdAt:
                                        allData[teamName]["deletions"] += prDict[repo][pr]["changes"]["deleted"]
                                        allData[teamName]["additions"] += prDict[repo][pr]["changes"]["added"]
                                        if prDict[repo][pr]["user"]:
                                            if prDict[repo][pr]["user"]["name"] is None:
                                                prDict[repo][pr]["user"]["name"] = prDict[repo][pr]["user"]["login"]
                                            allData[teamName]["openers"][prDict[repo][pr]["user"]["name"]]["open_count"] += 1
                                            allData[teamName]["openers"][prDict[repo][pr]["user"]["name"]]["LOC_count"] += \
                                                                                    prDict[repo][pr]["changes"]["added"] + prDict[repo][pr]["changes"]["deleted"]
                                        allData[teamName]["opened_pr"] += 1
                                        allData[teamName]["open_dates"].append(createdAt)
                                        til = prDict[repo][pr]["title"].strip().split("-")
                                        if len(til) >= 2 and til[0].upper() == "DIGMANEXE" and til[1].isnumeric():
                                            allData[teamName]["follow_name_conv"] += 1
                                        else:
                                            allData[teamName]["not_follow_name_conv"] += 1

                                    if closedAt: 
                                        
                                        integrationTime = float(prDict[repo][pr]["review_duration"].split()[0])
                                        if integrationTime < 10:
                                            allData[teamName]["integration_time"]["opt1"] += 1
                                        elif integrationTime < 360:
                                            allData[teamName]["integration_time"]["opt2"] += 1
                                        elif integrationTime < 1440:
                                            allData[teamName]["integration_time"]["opt3"] += 1
                                        elif integrationTime < 10080:
                                            allData[teamName]["integration_time"]["opt4"] += 1
                                        elif integrationTime < 302400:
                                            allData[teamName]["integration_time"]["opt5"] += 1
                                        elif integrationTime < 1814400:
                                            allData[teamName]["integration_time"]["opt6"] += 1
                                        elif integrationTime < 3628800:
                                            allData[teamName]["integration_time"]["opt7"] += 1
                                        else:
                                            allData[teamName]["integration_time"]["opt8"] += 1
                                        allData[teamName]["post_review_time"].append(prDict[repo][pr]["post_review_time"])
                                        allData[teamName]["close_pr_status"].append(prDict[repo][pr]["status"])
                                        allData[teamName]["close_repo_name"].append(repo)
                                        allData[teamName]["close_pr_number"].append(prDict[repo][pr]["PR_number"])
                                        allData[teamName]["closed_pr"] += 1
                                        allData[teamName]["close_dates"].append(closedAt)
                                        allData[teamName]["inspection_rate"].append(prDict[repo][pr]["inspection_rate"])
                                        allData[teamName]["inspection_time"].append(prDict[repo][pr]["inspection_time"])
                                        allData[teamName]["pre_review_time"].append(prDict[repo][pr]["preReviewTime"])
                                        allData[teamName]["update_repo_name"].append(repo)
                                        allData[teamName]["update_pr_number"].append(prDict[repo][pr]["PR_number"])
                                        allData[teamName]["update_pr_status"].append(prDict[repo][pr]["status"])
                                        allData[teamName]["update_dates"].append(updatedAt)

                                        if prDict[repo][pr]["review_threads"]:
                                            allData[teamName]["pr_that_has_rvw_thrd"] += 1
                                        for rvwThrd in prDict[repo][pr]["review_threads"]:
                                            if rvwThrd["is_resolved"]:
                                                allData[teamName]["review_threads_resolved"] += 1
                                            else: 
                                                allData[teamName]["review_threads_unresolved"] += 1

                                        til = prDict[repo][pr]["title"].strip().split("-")
                                        if len(til) >= 2 and til[0].upper() == "DIGMANEXE" and til[1].isnumeric():
                                            allData[teamName]["follow_name_conv"] += 1
                                        else:
                                            allData[teamName]["not_follow_name_conv"] += 1
                
                                    if updatedAt :
                                        if prDict[repo][pr]["status"] == "CLOSED":
                                            allData[teamName]["abandoned"] += 1

                                    for rvwThrd in prDict[repo][pr]["review_threads"]:
                                            for i,rvw in enumerate(rvwThrd["comments"]):
                                                postedAt = (rvw["posted_at"])
                                                if i == 0 and postedAt:
                                                    allData[teamName]["review_threads"] += 1

                                                if rvw["user"] != prDict[repo][pr]["user"] and postedAt:
                                                    if rvw["user"]["name"] is None:
                                                        rvw["user"]["name"] = rvw["user"]["login"]
                                                    allData[teamName]["reviewers"][rvw["user"]["name"]] += 1
                                                    allData[teamName]["review_comments"] += 1

                                except Exception as e:
                                    print("prInfo: Exception occurred: {} for repo: {} pr: {}".format(e, repo, pr))
                                    logging.exception("prInfo: Exception occurred: {} for repo: {} pr: {}".format(e, repo, pr))

    except Exception as e:
        print("prInfo: Exception occurred: {}".format(e))
        logging.exception("prInfo: Exception occurred: {}".format(e))

    return allData


def filterOut(allData, lisProperty, teamNames):
    newDict = None
    try:
        newDict = defaultdict(lambda: {})
        for teamName in teamNames:
            for props in lisProperty:
                newDict[teamName][props] = allData[teamName][props]

    except Exception as e:
        logging.exception("filterOut: Exception occurred: {}".format(e))
        print("filterOut: Exception occurred: {}".format(e))

    return newDict

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

def getDataFrame(data, teamNames):
    """
    Creates the DataFrame
    :param data: Teams repo pr Data
    :type data: dict
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :return df: Pandas DataFrame
    :type df: str
    """
    df = None
    try:
        teamWiseCompare = filterOut(data, ["repos", "owners", "opened_pr", "closed_pr", "review_threads",
                                              "review_threads_resolved", "review_threads_unresolved", "deletions",
                                              "additions",
                                              "abandoned", "pr_that_has_rvw_thrd", "review_comments"], teamNames)
        df = pd.DataFrame(teamWiseCompare).T
        df.insert(0, "teamName", df.index)
        print(df)

    except Exception as e:
        logging.exception("getDataFrame: Exception occurred: {}".format(e))
        print("getDataFrame: Exception occurred: {}".format(e))

    return df


def repoBarGraph(df, tmp):
    """
    Creates a  bar graph to obtain the total count of repos per team
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(13, 8))
        ax.bar(x=df.index, height=df.repos)
        ax.set(title="Total Repos per Team", ylabel="No. of Repositories", xlabel="Team Names")
        rects = ax.patches

        for rect, label in zip(rects, df.repos):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height + 0.1, label,
                    ha='center', va='bottom')
        if not os.path.exists("./graphs/repos"):
            os.mkdir("./graphs/repos")
        fig.savefig("./graphs/repos/repoBar.png")

        restrictedUpload("Test2.O", "master", tmp, ["graphs/repos/repoBar.png"], "[skip-ci] update file")

    except Exception as e:
        logging.exception("repoBarGraph: Exception occurred: {}".format(e))
        print("repoBarGraph: Exception occurred: {}".format(e))


def repoPieChart(teamNames, df):
    """
    Creates a pie chart to obtain the total count of repos per team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        explode = [0 for i in range(len(teamNames))]
        explode[1] = 0.1
        ax.pie(df.repos, labels=df.index,shadow=True, startangle=90, autopct='%1.1f%%', explode=explode)
        if not os.path.exists("./graphs/repos"):
            os.mkdir("./graphs/repos")
        fig.savefig("./graphs/repos/pieChart.png")

    except Exception as e:
        logging.exception("repoPieChart: Exception occurred: {}".format(e))
        print("repoPieChart: Exception occurred: {}".format(e))


def ownerBarGraph(df):
    """
    Creates a bar graph to obtain the total count of owners per Team
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(13, 8))
        ax.bar(x=df.index, height=df.owners)
        ax.set(title="Owners per Team", ylabel="Owners Count", xlabel="Team Names")
        rects = ax.patches

        for rect, label in zip(rects, df.owners):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height + 0.1, label,
                    ha='center', va='bottom')
        if not os.path.exists("./graphs/owners"):
            os.mkdir("./graphs/owners")
        fig.savefig("./graphs/owners/barGraph.png")

    except Exception as e:
        logging.exception("ownerBarGraph: Exception occurred: {}".format(e))
        print("ownerBarGraph: Exception occurred: {}".format(e))


def ownerPieChart(teamNames, df):
    """
    Creates a pie chart to obtain the total count of owners per team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        explode = [0 for i in range(len(teamNames))]
        explode[5] = 0.1
        ax.pie(df.owners, labels=df.index,shadow=True, startangle=90, autopct='%1.1f%%', explode=explode)
        if not os.path.exists("./graphs/owners"):
            os.mkdir("./graphs/owners")
        fig.savefig("./graphs/owners/pieChart.png")

    except Exception as e:
        logging.exception("ownerPieChart: Exception occurred: {}".format(e))
        print("ownerPieChart: Exception occurred: {}".format(e))


def locBarGraph(df):
    """
    Creates a bar graph to obtain the total count of line of code modified
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.barh(df.index, df.additions)
        ax.barh(df.index, df.deletions, left=df.additions)
        ax.set(title="Line of Code(LOC) Modified Vs Team", xlabel="LOC Modified", ylabel="Teams")
        ax.invert_yaxis()
        ax.legend(('Additions', 'Deletions'))

        for i, label1, label2 in zip(range(len(df.additions)), df.additions, df.deletions):
            ax.text(label1+label2+1, i+.20, f"a-{label1}/d-{label2}", color="#678d58", fontweight="bold")
        if not os.path.exists("./graphs/LOC"):
            os.mkdir("./graphs/LOC")
        fig.savefig("./graphs/LOC/barGraph.png")

    except Exception as e:
        logging.exception("locBarGraph: Exception occurred: {}".format(e))
        print("locBarGraph: Exception occurred: {}".format(e))


def rvwThrdResolvedBarGraph(df):
    """
    Creates a bar graph to obtain the total count of review threads that were resolved and unresolved
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.barh(df.index, df.review_threads_resolved)
        ax.barh(df.index, df.review_threads_unresolved, left=df.review_threads_resolved)
        ax.set(title="Review Threads Vs Team", xlabel="Thread Count", ylabel="Teams")
        ax.invert_yaxis()
        ax.legend(('Thread Resolved in given Time Range', 'Thread Unresolved in given Time Range'))

        for i, label1, label2 in zip(range(len(df.review_threads_resolved)), df.review_threads_resolved, df.review_threads_unresolved):
            ax.text(label1+label2+1, i+.20, f"r-{label1}/ur-{label2}", color="#678d58", fontweight="bold")
        if not os.path.exists("./graphs/rvwThrdresolved"):
            os.mkdir("./graphs/rvwThrdresolved")
        fig.savefig("./graphs/rvwThrdresolved/barGraph.png")

    except Exception as e:
        logging.exception("rvwThrdResolvedBarGraph: Exception occurred: {}".format(e))
        print("rvwThrdResolvedBarGraph: Exception occurred: {}".format(e))


def prsBarGraph(df):
    """
    Creates a bar graph to obtain the total count of PRs that were opened and closed
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.barh(df.index, df.opened_pr)
        ax.barh(df.index, df.closed_pr, left=df.opened_pr)
        ax.set(title="Open/Closed PRs Vs Team", xlabel="PR Count", ylabel="Teams")
        ax.invert_yaxis()
        ax.legend(('Open PR', 'Closed PR'))

        for i, label1, label2 in zip(range(len(df.opened_pr)), df.opened_pr, df.closed_pr):
            ax.text(label1+label2+1, i+.20, f"o-{label1}/c-{label2}", color="#678d58", fontweight="bold")
        if not os.path.exists("./graphs/prs"):
            os.mkdir("./graphs/prs")
        fig.savefig("./graphs/prs/barGraph.png")

    except Exception as e:
        logging.exception("prsBarGraph: Exception occurred: {}".format(e))
        print("prsBarGraph: Exception occurred: {}".format(e))


def abndndPrBarGraph(df):
    """
    Creates a bar graph to obtain the total count of abandoned PRs
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        # the label locations
        x = np.arange(len(df.index))  
        # the width of the bars
        width = 0.35  
        fig, ax = plt.subplots(figsize=(13,8))
        rects1 = ax.bar(x - width/2, df.closed_pr, width, label='Closed PR')
        rects2 = ax.bar(x + width/2, df.abandoned, width, label='Abandoned PR')
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('PR Count')
        ax.set_title('Closed PR/Abandoned PR Vs Team')
        ax.set_xlabel("Teams")
        ax.set_xticks(x)
        ax.set_xticklabels(df.index)
        ax.legend()
        autolabel(ax, rects1)
        autolabel(ax, rects2)
        fig.tight_layout()
        if not os.path.exists("./graphs/abandonedPr"):
            os.mkdir("./graphs/abandonedPr")
        fig.savefig("./graphs/abandonedPr/barGraph.png")

    except Exception as e:
        logging.exception("abndndPrBarGraph: Exception occurred: {}".format(e))
        print("abndndPrBarGraph: Exception occurred: {}".format(e))


def rvwThrdBarGraph(df):
    """
    Creates a bar graph to obtain the total count of PRs that are having review threads
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        # the label locations
        x = np.arange(len(df.index))  
        # the width of the bars
        width = 0.35  
        fig, ax = plt.subplots(figsize=(13,8))
        rects1 = ax.bar(x - width/2, df.closed_pr, width, label='PRs that was closed in given time range')
        rects2 = ax.bar(x + width/2, df.pr_that_has_rvw_thrd, width, label='PRs having review thrd')
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Count')
        ax.set_title('Total PRs having review thread  Vs Team')
        ax.set_xlabel("Teams")
        ax.set_xticks(x)
        ax.set_xticklabels(df.index)
        ax.legend()
        autolabel(ax, rects1)
        autolabel(ax, rects2)
        fig.tight_layout()
        if not os.path.exists("./graphs/rvwThrd"):
            os.mkdir("./graphs/rvwThrd")
        fig.savefig("./graphs/rvwThrd/barGraph.png")

    except Exception as e:
        logging.exception("rvwThrdBarGraph: Exception occurred: {}".format(e))
        print("rvwThrdBarGraph: Exception occurred: {}".format(e))


def rvwCmntsBarGraph(df):
    """
    Creates a bar graph to obtain the total count of PRs that are having Review Comments
    :param df: Pandas DataFrame
    :type df: str
    :return none
    """
    try:
        # the label locations
        x = np.arange(len(df.index)) 
        # the width of the bars
        width = 0.35 
        fig, ax = plt.subplots(figsize=(13,8))
        rects1 = ax.bar(x - width/2, df.review_comments, width, label='Review Comments')
        rects2 = ax.bar(x + width/2, df.review_threads, width, label='Review Threads')
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Count')
        ax.set_title('Review Comments/Review Threads Vs Team')
        ax.set_xticks(x)
        ax.set_xticklabels(df.index)
        ax.legend()
        autolabel(ax, rects1)
        autolabel(ax, rects2)
        fig.tight_layout()
        if not os.path.exists("./graphs/rvwComments"):
            os.mkdir("./graphs/rvwComments")
        fig.savefig("./graphs/rvwComments/barGraph.png")

    except Exception as e:
        logging.exception("rvwCmntsBarGraph: Exception occurred: {}".format(e))
        print("rvwCmntsBarGraph: Exception occurred: {}".format(e))


def openersGraph(teamNames, df, data):
    """
    Creates a bar graph to obtain the total count of openers per Team
    :param teamNames: Name of the Team with repos
    :type teamNames: dict
    :param df: Pandas DataFrame
    :type df: str
    :param data: Teams repo pr Data
    :type data: dict
    :param fileList: 
    :type fileList: list
    :return none
    """
    try:
        plt.style.use('ggplot')
        for teamName in teamNames:
            df = pd.DataFrame(data[teamName]["openers"]).T
            fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(20, 16), sharey=True)
            if not df.empty:
                y = np.arange(len(df.index))
                df.sort_values(by="open_count", inplace=True)
                rects1 = ax1.barh(y, df["open_count"], label="Pull Requests Count")
                rects2 = ax2.barh(y, round(df["LOC_count"] / 1000, 2), label="LOC Modified", color='y')
                ax1.set_yticks(y)
                ax1.set_yticklabels(df.index, fontweight="bold", fontsize="12")
                ax1.legend()
                ax2.legend()
                for rect in rects1:
                    width = rect.get_width()
                    ax1.annotate(str(width),
                                 xy=(width, rect.get_y() + rect.get_height() / 2),
                                 xytext=(3, 0),
                                 textcoords="offset points",
                                 fontweight="bold",
                                 fontsize="11",
                                 ha="left", va="center")
                for rect in rects2:
                    width = rect.get_width()
                    ax2.annotate(str(width) + " K",
                            xy=(width, rect.get_y()+rect.get_height()/2),
                            xytext=(3, 0),
                            textcoords="offset points",
                            fontweight="bold",
                            fontsize="11",
                            ha="left", va="center")
            if not os.path.exists("./graphs/openers"):
                os.mkdir("./graphs/openers")
            fig.savefig(f"./graphs/openers/{teamName}.png")
        plt.close("all")

    except Exception as e:
        logging.exception("openersGraph: Exception occurred: {}".format(e))
        print("openersGraph: Exception occurred: {}".format(e))
    

def reviewersGraph(teamNames, data):
    """
    Creates a bar graph to obtain the total count of reviewers per Team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("seaborn-whitegrid")
        for teamName in teamNames:
            df = pd.DataFrame({"count": data[teamName]["reviewers"]})
            fig, ax = plt.subplots(figsize=(20, 13))
            df.sort_values(by="count", inplace=True)
            rects = ax.barh(df.index, df["count"])
            ax.set_yticklabels(df.index, fontweight="bold", fontsize="13")

            for rect in rects:
                width = rect.get_width()
                ax.annotate(str(width),
                        xy=(width, rect.get_y()+rect.get_height()/2),
                        xytext=(3, 0),
                        textcoords="offset points",
                        fontsize="11",
                        ha="left", va="center")
            if not os.path.exists("./graphs/reviewers"):
                os.mkdir("./graphs/reviewers")
            fig.savefig(f"./graphs/reviewers/{teamName}.png")
        plt.close("all")

    except Exception as e:
        logging.exception("reviewersGraph: Exception occurred: {}".format(e))
        print("reviewersGraph: Exception occurred: {}".format(e))


def integrationTimeGraph(teamNames, data):
    """
    Creates a bar graph to obtain the total count of Integration time
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("seaborn-dark-palette")
        for teamName in teamNames:
            df = pd.DataFrame({"count": data[teamName]["integration_time"]})
            fig, ax = plt.subplots(figsize=(20, 13.5))
            df.index = ["< 10 Min",
                        ">= 10 Min and < 6 Hour",
                        ">= 6 Hour and < 1 Day",
                        ">= 1 Day and < 1 Week",
                        ">= 1 Week and < 1 Month",
                        ">= 1 Month and < 6 Month",
                        ">= 6 Month and < 1 Year",
                        ">= 1 Year"]
            rects = ax.barh(df.index, df["count"])
            ax.set_yticklabels(df.index, fontweight="bold", fontsize="13")
            ax.invert_yaxis()
            for rect in rects:
                width = rect.get_width()
                ax.annotate(str(width),
                            xy=(width, rect.get_y() + rect.get_height() / 2),
                            xytext=(3, 0),
                            fontweight="bold",
                            fontsize="11",
                            textcoords="offset points",
                            ha='left', va='center')
            if not os.path.exists("./graphs/integrationTime"):
                os.mkdir("./graphs/integrationTime")
            fig.savefig(f"./graphs/integrationTime/{teamName}.png")
        plt.close("all")

    except Exception as e:
        logging.exception("integrationTimeGraph: Exception occurred: {}".format(e))
        print("integrationTimeGraph: Exception occurred: {}".format(e))


def approvers(teamNames, data):
    """
    Creates a graph to obtain the total count of approvers per Team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        for teamName in teamNames:
            df = pd.DataFrame({"approve_counts": data[teamName]["approvers"]})
            fig, ax = plt.subplots(figsize=(20, 14))
            df.sort_values(by="approve_counts", inplace=True)
            rects = ax.barh(df.index, df["approve_counts"])
            ax.set(title="Approves Count", xlabel="Count")
            ax.set_yticklabels(df.index, fontweight="bold", fontsize="12")

            for rect in rects:
                width = rect.get_width()
                ax.annotate("{}".format(width),
                            xy=(width, rect.get_y() + rect.get_height() / 2),
                            xytext=(3, 0),
                            textcoords="offset points",
                            fontweight="bold",
                            fontsize="11",
                            ha='left', va='center')
            if not os.path.exists("./graphs/approvers"):
                os.mkdir("./graphs/approvers")
            fig.savefig(f"./graphs/approvers/{teamName}.png")
        plt.close("all")

    except Exception as e:
        logging.exception("approvers: Exception occurred: {}".format(e))
        print("approvers: Exception occurred: {}".format(e))


def inspectionRateGraph(teamNames, data):
    """
    Creates a graph to obtain the total count of inspection rate
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("ggplot")
        teamList = []
        for teamName in teamNames:
            df = pd.DataFrame({"Repo Name": data[teamName]["update_repo_name"],
                               "PR Number": data[teamName]["update_pr_number"],
                               "Inspection Rate(LOC/Min)": data[teamName]["inspection_rate"],
                               "Inspection Time(Min)": data[teamName]["inspection_time"]
                               },
                              index=data[teamName]["update_dates"])
            df = df.dropna(axis=0)
            df["Inspection Rate(LOC/Min)"] = df["Inspection Rate(LOC/Min)"].apply(lambda x: float(x.split()[0]))
            df["Inspection Time(Min)"] = df["Inspection Time(Min)"].apply(lambda x: float(x.split()[0]))
            teamList.append({
                "Team Name": teamName,
                "Repo Count": len(set(df["Repo Name"])),
                "PR Count": len(df["PR Number"]),
                "Avg. Inspection Time(Min)": round(np.mean(df["Inspection Time(Min)"]), 2),
                "Avg. Inspection Rate(LOC/Min)": round(np.mean(df["Inspection Rate(LOC/Min)"]), 2)
            })
        df = pd.DataFrame(teamList)
        df.fillna(0.00, inplace=True)
        if not os.path.exists("./graphs/inspectionRate"):
            os.mkdir("./graphs/inspectionRate")
        renderMplTable(df, header_columns=0, col_width=5.0, file_path='/graphs/inspectionRate/overview.png')

        fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(15, 10), sharey=True)
        df.sort_values("Avg. Inspection Time(Min)", inplace=True)
        rects1 = ax1.barh(df["Team Name"], df["Avg. Inspection Time(Min)"], label="Avg. Inspection Time(Min)")
        rects2 = ax2.barh(df["Team Name"], df["Avg. Inspection Rate(LOC/Min)"], color="y",
                          label="Avg. Inspection Rate(LOC/Min")
        ax1.legend()
        ax2.legend()
        ax1.set_yticklabels(df["Team Name"], fontweight="bold")
        for rect in rects1:
            width = rect.get_width()
            ax1.annotate(str(width),
                         xy=(width, rect.get_y() + rect.get_height() / 2),
                         xytext=(3, 0),
                         textcoords="offset points",
                         fontweight="bold",
                         fontsize="11",
                         ha="left", va="center")

        for rect in rects2:
            width = rect.get_width()
            ax2.annotate(str(width),
                    xy=(width, rect.get_y()+rect.get_height()/2),
                    xytext=(3, 0),
                    textcoords="offset points",
                    fontweight="bold",
                    fontsize="11",
                    ha="left", va="center")
        # These Repo count and PR count are considered in calculating avg. Inspection time (these are not the total count of the PR or Repo)
        fig.savefig("./graphs/inspectionRate/overview.png")

    except Exception as e:
        logging.exception("inspectionRateGraph: Exception occurred: {}".format(e))
        print("inspectionRateGraph: Exception occurred: {}".format(e))


def preIntegrationTimeGraph(teamNames, data):
    """
    Creates a graph to obtain the total count of preIntegration time per Team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        teamList = []
        for teamName in teamNames:
            df = pd.DataFrame({"Repo Name": data[teamName]["close_repo_name"],
                               "PR Number": data[teamName]["close_pr_number"],
                               "PR Status": data[teamName]["close_pr_status"],
                               "Pre-Integration Time(Min)": data[teamName]["post_review_time"]
                               },
                              index=data[teamName]["close_dates"])
            df = df.dropna(axis=0)
            df["Pre-Integration Time(Min)"] = df["Pre-Integration Time(Min)"].apply(lambda x: float(x.split()[0]))
            df = df[df["PR Status"] == "MERGED"]
            avg_pre_time = np.mean(df[df["Pre-Integration Time(Min)"] >= 0]["Pre-Integration Time(Min)"])
            teamList.append({
                "Team Name": teamName,
                "Repo Count": len(set(df["Repo Name"])),
                "PR Count": len(df["PR Number"]),
                "Avg. Pre-Integration Time(Min)": round(avg_pre_time, 2)
            })

        df = pd.DataFrame(teamList)
        df.fillna(0.0, inplace=True)
        if not os.path.exists("./graphs/preIntegrationTime"):
            os.mkdir("./graphs/preIntegrationTime")
        renderMplTable(df, header_columns=0, col_width=5.0, file_path='/graphs/preIntegrationTime/overview.png')
        fig, ax = plt.subplots(figsize=(17,10))
        rects = ax.bar(df["Team Name"], df["Avg. Pre-Integration Time(Min)"])
        ax.set_ylabel("Minutes")
        autolabel(ax, rects)
        fig.savefig("./graphs/preIntegrationTime/overview.png")

    except Exception as e:
        logging.exception("preIntgrationTimeGraph: Exception occurred: {}".format(e))
        print("preIntgrationTimeGraph: Exception occurred: {}".format(e))


def openCountGraph(teamNames, data):
    """
    Creates a graph to obtain the total count of open counts
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use('ggplot')
        teamPltData = []
        for teamName in teamNames:
            df = pd.DataFrame(data[teamName]["openers"]).T
            teamPltData.append({
                "Team Name": teamName,
                "Avg. pull requests made by user": round(np.mean(df["open_count"]), 2) if not df.empty else 0,
                "Avg. LOC modified by user": round(np.mean(df["LOC_count"]), 2) if not df.empty else 0
            })
        df = pd.DataFrame(teamPltData)
        fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(17, 10), sharey=True)
        df.sort_values(by="Avg. pull requests made by user", inplace=True)
        rects1 = ax1.barh(df["Team Name"], df["Avg. pull requests made by user"],
                          label="Avg. pull requests made by user")
        rects2 = ax2.barh(df["Team Name"], df["Avg. LOC modified by user"], label="Avg. LOC modified by user",
                          color='y')
        ax1.legend(bbox_to_anchor=(1.1, 1.05))
        ax2.legend(bbox_to_anchor=(1.1, 1.05))
        ax1.set_yticklabels(df["Team Name"], fontweight="bold")
        for rect in rects1:
            width = rect.get_width()
            ax1.annotate(str(width),
                    xy=(width, rect.get_y()+rect.get_height()/2),
                    xytext=(3, 0),
                    textcoords="offset points",
                    fontweight="bold",
                    fontsize="11",
                    ha="left", va="center")

        for rect in rects2:
            width = rect.get_width()
            ax2.annotate(str(width),
                    xy=(width, rect.get_y()+rect.get_height()/2),
                    xytext=(3, 0),
                    textcoords="offset points",
                    fontweight="bold",
                    fontsize="11",
                    ha="left", va="center")
        if not os.path.exists("./graphGeneration/graphs/overview"):
            os.mkdir("./graphs/overview")
        fig.savefig("./graphs/overview/openCount.png")

    except Exception as e:
        logging.exception("openCountGraph: Exception occurred: {}".format(e))
        print("openCountGraph: Exception occurred: {}".format(e))


def ovrvwIntegrationTime(teamNames, data):
    """
    Creates a graph to obtain the total count of reviewers per Team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("seaborn-whitegrid")
        fig, axes = plt.subplots(nrows=6, ncols=3, figsize=(15, 19), sharey=True, sharex=True)
        legendEle = []
        for teamName, ax in zip(teamNames, np.array(axes).flatten()):
            df = pd.DataFrame({"count": data[teamName]["integration_time"]})
            df.index = ["< 10 Min",
                        ">= 10 Min and < 6 Hour",
                        ">= 6 Hour and < 1 Day",
                        ">= 1 Day and < 1 Week",
                        ">= 1 Week and < 1 Month",
                        ">= 1 Month and < 6 Month",
                        ">= 6 Month and < 1 Year",
                        ">= 1 Year"]
            scatter = ax.scatter(range(len(df.index)), df["count"], s=df["count"] * 100, c=range(len(df.index)),
                                 cmap="hsv", alpha=0.7)
            ax.set_title(teamName)
            ax.set_xticklabels([' '] * len(df.index))
            if len(legendEle) < len(scatter.legend_elements()):
                legendEle = scatter.legend_elements()
        lgnd = fig.legend(*legendEle, loc="upper center", fontsize=10)

        for handle in lgnd.legendHandles:
            handle._sizes = [30]
        for text, new_text in zip(lgnd.get_texts(), df.index):
            text.set_text(new_text)
        # fig.suptitle("Overview Plot", fontsize=24, fontweight="bold");
        if not os.path.exists("./graphs/overview"):
            os.mkdir("./graphs/overview")
        fig.savefig("./graphs/overview/integrationTime.png")

    except Exception as e:
        logging.exception("ovrvwIntegrationTime: Exception occurred: {}".format(e))
        print("ovrvwIntegrationTime: Exception occurred: {}".format(e))


def rvwCount(teamNames, data):
    """
    Creates a bar graph to obtain the total count of review count
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("seaborn-whitegrid")
        fig, axes = plt.subplots(nrows=6, ncols=3, figsize=(15, 19), sharey=True)
        for teamName, ax in zip(teamNames, np.array(axes).flatten()):
            df = pd.DataFrame({"count": data[teamName]["reviewers"]})
            rects = ax.scatter(range(len(df.index)), df["count"], s=df["count"] * 100, c=range(len(df.index)),
                               cmap="hsv", alpha=0.7)
            ax.set_xticklabels([' '] * len(df.index))
            ax.set_title(teamName)
        if not os.path.exists("./graphs/overview"):
            os.mkdir("./graphs/overview")
        fig.savefig("./graphs/overview/reviewCount.png")

    except Exception as e:
        logging.exception("rvwCount: Exception occurred: {}".format(e))
        print("rvwCount: Exception occurred: {}".format(e))


def approversCount(teamNames, data):
    """
    Creates graph to obtain the total count of approves count
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        plt.style.use("seaborn-whitegrid")
        fig, axes = plt.subplots(nrows=6, ncols=3, figsize=(15, 19))
        for teamName, ax in zip(teamNames, np.array(axes).flatten()):
            df = pd.DataFrame({"count": data[teamName]["approvers"]})
            ax.scatter(range(len(df.index)), df["count"], s=df["count"] * 100, c=range(len(df.index)), cmap="hsv",
                       alpha=0.65)
            ax.set_xticklabels([' '] * len(df.index))
            ax.set_title(teamName)
        if not os.path.exists("./graphs/overview"):
            os.mkdir("./graphs/overview")
        fig.savefig("./graphs/overview/approversCount.png")

    except Exception as e:
        logging.exception("approversCount: Exception occurred: {}".format(e))
        print("approversCount: Exception occurred: {}".format(e))


def reportPage(startDate, endDate):
    """
    Creates report page
    :param startDate: start date of the report
    :type startDate: str
    :param endDate: end date of the report
    :type endDate: str
    :return none
    """
    try:
        html = """<!DOCTYPE html>
        <html lang="en">

        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
            <link rel="stylesheet" href="/home/vsts/work/1/prInsights/pdfFormatting/public/tailwind.css">
        </head>

        <body class="w-full h-full">
            <div class="flex justify-center">
                <p class="mr-auto text-lg font-bold">Created At - {curr_date}</p>
                <img class="h-18" src="/home/vsts/work/1/prInsights/pdfFormatting/public/saplogo.png" alt="SAP IMAGE LOGO">
            </div>
            <div>
                <p class="text-2xl bg-blue-300 font-bold py-1 shadow-2xl">TEAM REPORT</p>
                <p class="text-lg mt-4">
                    {startDate} - {endDate}
                </p>
            </div>x

        </body>

        </html>"""

        with open('./graphs/frontPage.html', 'w') as file:
            startDate = datetime.datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%SZ")
            endDate = datetime.datetime.strptime(endDate, "%Y-%m-%dT%H:%M:%SZ")
            file.write(html.format(curr_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   startDate=startDate.strftime("%Y-%m-%d"), endDate=endDate.strftime("%Y-%m-%d")))

    except Exception as e:
        logging.exception("reportPage: Exception occurred: {}".format(e))
        print("reportPage: Exception occurred: {}".format(e))


def topPrLocCount(teamNames, data):
    """
    Creates graph to obtain the total count of reviewers per Team
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        newData = defaultdict(lambda:
                               {'open_count': 0,
                                'LOC_count': 0}
                               )
        for teamName in teamNames:
            for key, value in data[teamName]["openers"].items():
                newData[key]['open_count'] += value['open_count']
                newData[key]['LOC_count'] += value['LOC_count']

        df = pd.DataFrame(newData).T
        df1 = df.sort_values(by='open_count', ascending=False).head(30)
        df2 = df.sort_values(by='LOC_count', ascending=False).head(30)

        fig, ax = plt.subplots(figsize=(18, 12))
        rects = ax.barh(df1.index, df1.open_count)
        ax.invert_yaxis()
        for rect in rects:
            width = rect.get_width()
            ax.annotate(str(width),
                        xy=(width, rect.get_y() + rect.get_height() / 2),
                        xytext=(3, 0),
                        textcoords="offset points",
                        fontweight="bold",
                        fontsize="11",
                        ha="left", va="center")
        if not os.path.exists("./graphs/top30NamesforPR"):
            os.mkdir("./graphs/top30NamesforPR")
        fig.savefig("./graphs/top30NamesforPR/top30PR.png")
        fig, ax = plt.subplots(figsize=(18, 12))
        rects = ax.barh(df2.index, df2.LOC_count)
        ax.invert_yaxis()
        for rect in rects:
            width = rect.get_width()
            ax.annotate(str(width),
                        xy=(width, rect.get_y() + rect.get_height() / 2),
                        xytext=(3, 0),
                        textcoords="offset points",
                        fontweight="bold",
                        fontsize="11",
                        ha="left", va="center")
        if not os.path.exists("./graphs/top30LOCforPR"):
            os.mkdir("./graphs/top30LOCforPR")
        fig.savefig("./graphs/top30LOCforPR/top30LOC.png")

    except Exception as e:
        logging.exception("topPrLocCount: Exception occurred: {}".format(e))
        print("topPrLocCount: Exception occurred: {}".format(e))


def nameFollowCnvtn(teamNames, data):
    """
    Creates a bar graph to obtain the total count PR naming guidance
    :param teamNames: Name of the Team mapped with repos
    :type teamNames: dict
    :param data: Teams repo pr Data
    :type data: dict
    :return none
    """
    try:
        nwD = defaultdict(lambda: {"follow": 0, "not_follow": 0})
        for teamName in teamNames:
            nwD[teamName]["follow"] += data[teamName]["follow_name_conv"]
            nwD[teamName]["not_follow"] += data[teamName]["not_follow_name_conv"]

        df = pd.DataFrame(nwD).T
        print(df)
        # the label locations
        x = np.arange(len(df.index))
        # the width of the bars
        width = 0.35
        fig, ax = plt.subplots(figsize=(13, 8))
        rects1 = ax.bar(x - width / 2, df.follow, width, label='Follow PR naming guidance')
        rects2 = ax.bar(x + width / 2, df.not_follow, width, label='Not Follow PR naming guidance')
        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Count')
        ax.set_xticks(x)
        ax.set_xticklabels(df.index)
        ax.legend()
        autolabel(ax, rects1)
        autolabel(ax, rects2)
        fig.tight_layout()
        if not os.path.exists("./graphs/prNamingGuidance"):
            os.mkdir("./graphs/prNamingGuidance")
        fig.savefig("./graphs/prNamingGuidance/prNamingGuidance.png")

    except Exception as e:
        logging.exception("nameFollowCnvtn: Exception occurred: {}".format(e))
        print("nameFollowCnvtn: Exception occurred: {}".format(e))


def renderMplTable(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, file_path="path", *args, **kwargs):
    try:
        if ax is None:
            size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
            fig, ax = plt.subplots(figsize=size)
            ax.axis('off')
        mplTable = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
        mplTable.auto_set_font_size(False)
        mplTable.set_fontsize(font_size)
        for k, cell in six.iteritems(mplTable._cells):
            cell.set_edgecolor(edge_color)
            if k[0] == 0 or k[1] < header_columns:
                cell.set_text_props(weight='bold', color='w')
                cell.set_facecolor(header_color)
            else:
                cell.set_facecolor(row_colors[k[0] % len(row_colors)])

        fig.savefig(f"./{file_path}")

    except Exception as e:
        logging.exception("renderMplTable: Exception occurred: {}".format(e))
        print("renderMplTable: Exception occurred: {}".format(e))


def autolabel(ax, rects):
    try:
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        # 3 points vertical offset
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    except Exception as e:
        logging.exception("autolabel: Exception occurred: {}".format(e))
        print("autolabel: Exception occurred: {}".format(e))


def getRepoToTeamMapping(dmc, token):
    """
    Creates a python dictionary mapping repo name to team name using Repo_Team_List.json file
    :param org: Digital Manufacturing GitHub organization object.
    :type org: github object
    :return teamRepoDict: team dict mapped with repos
    :type teamRepoDict: dict
    """
    teamRepoDict = {}
    try:
        # repo = dmc.get_repo('dmc-msownership')
        # contents = repo.get_contents("Repo_Team_List.json", 'master')
        # data = base64.b64decode(contents.content, altchars=None).decode("utf-8", "ignore")
        # jsonObject = json.loads(data)
        fileSha = getFileSha(token, "dmc-msownership", "", "Repo_Team_List.json")
        jsonObject = parseJsonFile(token, "dmc-msownership", fileSha)

        for teamNames in jsonObject.keys():
            repoList = []
            repoDict = {}
            codeOwnersList = []
            print("getRepoToTeamMapping: {}".format(teamNames))
            logging.info("getRepoToTeamMapping: {}".format(teamNames))

            for grpName in jsonObject[teamNames]:
                if grpName.startswith(teamNames):
                    for repoNames in jsonObject[teamNames][grpName]['validRepoList']:
                        repoList.append(repoNames)
                    repoDict['validRepoList'] = repoList
                    for codeOwners in jsonObject[teamNames][grpName]['codeOwnersList']:
                        codeOwnersList.append(codeOwners)
                    repoDict["codeOwnersList"] = codeOwnersList

            teamRepoDict[teamNames] = repoDict

    except Exception as e:
        print("getRepoToTeamMapping: Exception occurred: {}".format(e))
        logging.exception("getRepoToTeamMapping: Exception occurred: {}".format(e))

    return teamRepoDict

def parseJsonFile(token, repoName, fileSha):
    prDict = {}
    try:
        url = ("https://github.tools.sap/api/v3/repos/DigitalManufacturing/{}/git/blobs/{}").format(repoName, fileSha)
        logging.info("parseJsonFile : File SHA URL : %s", url)
        r = requests.get(url=url,
                         headers={
                             'Accept': 'application/vnd.github.luke-cage-preview+json',
                             'Authorization': 'Token {}'.format(token)},

                         verify=False
                         )
        responseObject = json.loads(r.text)
        logging.info("parseJsonFile : received response object ")
        fileContent = responseObject.get("content")
        logging.info("parseJsonFile : fileContent is parsed.")
        data = base64.b64decode(bytearray(fileContent, "utf-8"))
        logging.info("parseJsonFile : data : %s", data)
        prDict = json.loads(data)
        logging.info("parseJsonFile : prDict : %s", prDict)
    except Exception as e:
        print(e)
        logging.exception("parseJsonFile : Exception occurred : %s", e)
    return prDict

def getFileSha(token, repoName, dirName, fileName):
    filesha = ""
    try:
        url = ("https://github.tools.sap/api/v3/repos/DigitalManufacturing/{}/git/trees/master:{}").format(repoName, dirName)
        logging.info("getFileSha : URL to get SHA of Files present in Directory : %s", url)
        r = requests.get(url=url,
                         headers={
                             'Accept': 'application/vnd.github.luke-cage-preview+json',
                             'Authorization': 'Token {}'.format(token)},

                         verify=False
                         )
        r = json.loads(r.text)
        logging.info("getFileSha : File sha is retrieved from Github.")
        treeList = r.get("tree")
        logging.info("getFileSha : Derived treeList from Github.")
        for tree in treeList:
            if tree.get("path") == fileName:
                filesha = tree.get("sha")
                logging.info("getFileSha : Derived sha from Github.")
    except Exception as e:
        print(e)
        logging.exception("getFileSha : Exception occurred : %s", e)
    return filesha

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
    try:
        start = time.time()
        logging.info("main: Start time = %.3f seconds", start)

        #format of startDate - endDate are : yyyy-mm-dd 
        startDate = "2021-10-01"
        endDate = "2022-02-20"
        startDate = startDate + "T0:0:0Z"
        endDate = endDate +  "T0:0:0Z"
        
        toolsUrl = 'https://github.tools.sap/api/v3'
        gitToken = "619f4f563ba7135480d8a8ad7a279c0917b8578f"
        
        dmc = Git(toolsUrl, gitToken)
        if not dmc:
            print("main: Unable to authenticate with Github org 'DigitalManufacturing'")
            logging.info("main: Unable to authenticate with Github org 'DigitalManufacturing'")
            sys.exit(1)
        
        tmp = Git(toolsUrl, gitToken, "TestOrg")

        allData = defaultdict(lambda : {"repos": 0, 
                                        "owners": 0,
                                        "deletions": 0, 
                                        "additions": 0,
                                        "opened_pr": 0,
                                        "open_dates": [],
                                        "openers": defaultdict(lambda : {"open_count": 0, "LOC_count": 0}),
                                        "integration_time": {
                                            "opt1": 0,
                                            "opt2": 0,
                                            "opt3": 0,
                                            "opt4": 0,
                                            "opt5": 0,
                                            "opt6": 0,
                                            "opt7": 0,
                                            "opt8": 0
                                        },
                                        "post_review_time": [],
                                        "approvers": defaultdict(int),
                                        "close_pr_number": [],
                                        "close_pr_status": [],
                                        "close_repo_name":[],
                                        "closed_pr": 0,
                                        "close_dates": [],
                                        "abandoned": 0,
                                        "inspection_rate": [],
                                        "inspection_time": [],
                                        "update_repo_name":[],
                                        "pre_review_time": [],
                                        "update_pr_number": [],
                                        "update_pr_status": [],
                                        "reviewers": defaultdict(int),
                                        "review_comments": 0,
                                        "review_threads":0,
                                        "pr_that_has_rvw_thrd":0,
                                        "review_threads_resolved": 0,
                                        "review_threads_unresolved": 0,
                                        "update_dates" :[],
                                        "follow_name_conv": 0,
                                        "not_follow_name_conv": 0
                                        })
        repoDict={}
        teamRepoDict = getRepoToTeamMapping(dmc, gitToken)
        allData, repoDict = repoCount(teamRepoDict, allData)
        repoPrData = prInfo(allData, repoDict, gitToken)
        df = getDataFrame(repoPrData, teamRepoDict)

        if df is None:
            print("main: collecting dataFrame was unsuccessful cannot proceed further")
            logging.info("main: collecting dataFrame was unsuccessful cannot proceed further")
        else:
            if not os.path.exists("./graphs"):
                os.mkdir("./graphs")

            repoBarGraph(df, tmp)
            repoPieChart(teamRepoDict, df)
            ownerBarGraph(df)
            ownerPieChart(teamRepoDict, df)
            locBarGraph(df)
            rvwThrdResolvedBarGraph(df)
            prsBarGraph(df)
            abndndPrBarGraph(df)
            rvwThrdBarGraph(df)
            rvwCmntsBarGraph(df)
            openersGraph(teamRepoDict, df, repoPrData)
            reviewersGraph(teamRepoDict, repoPrData)    
            integrationTimeGraph(teamRepoDict, repoPrData)
            approvers(teamRepoDict, repoPrData)
            inspectionRateGraph(teamRepoDict, repoPrData)
            preIntegrationTimeGraph(teamRepoDict, repoPrData)
            openCountGraph(teamRepoDict, repoPrData)
            ovrvwIntegrationTime(teamRepoDict, repoPrData)
            rvwCount(teamRepoDict, repoPrData)
            approversCount(teamRepoDict, repoPrData)
            reportPage(startDate, endDate)
            topPrLocCount(teamRepoDict, repoPrData)
            nameFollowCnvtn(teamRepoDict, repoPrData)
           
    except Exception as e:
        logging.exception("main: Exception occurred: {}".format(e))
        print("main: Exception occurred: {}".format(e))
        sys.exit(1)

    finally:
        end = time.time()
        logging.info("main : End time = %.3f seconds", end)
        print("main : Total Execution Time in seconds = ")
        print(end - start)
        logging.info("main : Total execution time = %.3f seconds", (end - start))


if __name__ == "__main__":
    main()
