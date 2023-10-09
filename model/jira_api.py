from utils import *
import json
from os import environ


username = environ.get('API_USERNAME')
if username is None:
    username = 206703889
password = environ.get('API_PASSWORD')

headers = {'Authorization': str(username)+':'+str(password), 'Content-Type': 'application/json'}
url = "https://jira.inbcu.com"


def get_all_teams_from_jira():
    return fetch_url(url + "/rest/api/latest/project", headers=headers)

def get_team_view_id_from_jira(team_id):
    return fetch_url(url + "/rest/agile/1.0/board?projectKeyOrId="+str(team_id), headers=headers)

def get_all_sprints_from_jira(cookie_team_view_id):
    return fetch_url(url + "/rest/greenhopper/latest/sprintquery/"+str(cookie_team_view_id)+"?includeHistoricSprints=true&includeFutureSprints=true", headers=headers)

def get_full_sprint_details_with_id(sprintId, cookie_team_view_id):
    return fetch_url(url + "/rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId="+str(cookie_team_view_id)+"&sprintId="+str(sprintId), headers=headers)

def get_epic_details(epic_number):
    result = fetch_url(url + "/rest/agile/1.0/issue/"+str(epic_number), headers=headers)
    if "errorMessages" in result:
        return {"epic_title": "Does not exists!", "ptd":"", "ptd_title": ""}

    ptd = ''
    ptd_title = ''
    for issuelinks in result['fields']['issuelinks']:
        if 'inwardIssue' in issuelinks:
            inwardIssue = issuelinks['inwardIssue']
            if 'key' in inwardIssue:
                ptd = inwardIssue['key']
                ptd_title = inwardIssue['fields']['summary']
    return {"epic_title": result['fields']['summary'], "epic_number": result['key'], "ptd": ptd, "ptd_title": ptd_title}

def get_epics(cookie_team_key):
    return fetch_url(url + "/rest/api/2/search?jql=issuetype=Epic%20AND%20project="+str(cookie_team_key)+"&maxResults=200", headers=headers)

def get_using_custom_query(query):
    print(url + "/rest/api/2/search?jql="+str(query))
    return fetch_url(url + "/rest/api/2/search?jql="+str(query), headers=headers)
    # return fetch_url(url + "/rest/api/2/search?jql=Epic%20Link="+str(issueId), headers=headers)

def get_issue_details(issue_number):
    return fetch_url(url + "/rest/agile/1.0/issue/"+str(issue_number), headers=headers)