from flask import Blueprint, request
from flask import Flask, jsonify, redirect, make_response, render_template
from cache import cache

from model.jira_api import *
from operator import itemgetter
import itertools


api_urls = Blueprint('api_urls', __name__)

@api_urls.route('/api/team_view_id/<teamId>')
def api_get_team_view_id(teamId):
    data = normalise_team(get_team_view_id_from_jira(teamId))
    return jsonify(data)

def normalise_team(boards):
    result = []
    for board in boards["values"]:
        data = {"name": board["name"], "team_view_id": board["id"]}
        result.append(data)
    return result

@api_urls.route('/api/sprints/<cookie_team_view_id>')
def api_get_sprints(cookie_team_view_id=0):
    if cookie_team_view_id == 0:
        cookie_team_view_id = request.cookies.get('team_view_id')
        if cookie_team_view_id is None:
            return redirect("/check_team")
    return jsonify(get_all_sprints_from_jira(cookie_team_view_id))

@api_urls.route('/api/sprint/id/<sprintId>/<cookie_team_id>/<cookie_team_view_id>/<cookie_team_key>')
@api_urls.route('/api/sprint/id/<sprintId>')
def api_get_sprint_with_id(sprintId, cookie_team_id=0, cookie_team_view_id=0, cookie_team_key=""):
    if cookie_team_id == 0:
        cookie_team_id = request.cookies.get('team_id')
        if cookie_team_id is None:
            return redirect("/check_team")

    if cookie_team_view_id == 0:
        cookie_team_view_id = request.cookies.get('team_view_id')
        if cookie_team_view_id is None:
            return redirect("/check_team")
    if cookie_team_key == "":
        cookie_team_key = request.cookies.get('team_key')
        if cookie_team_key is None:
            return redirect("/check_team")

    data = transformed_sprint_with_id(sprintId, cookie_team_id, cookie_team_view_id, cookie_team_key.upper())
    return jsonify(data)

def transformed_sprint_with_id(sprintId, cookie_team_id, cookie_team_view_id, cookie_team_key):
    full_sprint = get_full_sprint_details_with_id(sprintId, cookie_team_view_id)

    data = {}
    completed_tickets = []
    not_completed_tickets = []
    data['name']=full_sprint['sprint']['name']
    data['id']=full_sprint['sprint']['id']
    data['state']=full_sprint['sprint']['state']
    data['start_date']=readable_date(full_sprint['sprint']['startDate'])
    data['end_date']=readable_date(full_sprint['sprint']['endDate'])

    all_epics = all_epics_transformed(cookie_team_key)

# completed_tickets!!!
    for issue in full_sprint['contents']['completedIssues']:
        ticket = create_ticket(issue, all_epics, cookie_team_key)
        completed_tickets.append(ticket)

    data['completed_tickets']=completed_tickets
# not_completed_tickets!!!
    for issue in full_sprint['contents']['issuesNotCompletedInCurrentSprint']:
        ticket = create_ticket(issue, all_epics, cookie_team_key)
        not_completed_tickets.append(ticket)

    data['not_completed_tickets']=not_completed_tickets

    return data

def create_ticket(issue, all_epics, cookie_team_key):
    epic_details = {"epic_title": "", "ptd":"", "ptd_title": ""}
    if 'epic' not in issue:
        issue['epic'] = ""

    epic_number = issue['epic']
    if not epic_number.startswith(cookie_team_key):
        epic_number = ""
    if issue['epic'].startswith('PTD'):
        ptd_info = get_epic_details(issue['epic'])
        epic_details['ptd_title'] = ptd_info['epic_title']
        epic_details['ptd'] = ptd_info['epic_number']

# Setting estimate value
    if 'currentEstimateStatistic' not in issue or 'statFieldValue' not in issue['currentEstimateStatistic']:
        issue['currentEstimateStatistic']={}
        issue['currentEstimateStatistic']['statFieldValue']={}
    if 'value' not in issue['currentEstimateStatistic']['statFieldValue']:
        issue['currentEstimateStatistic']['statFieldValue']['value'] = ""        

    
    if 'epic' in issue:
        found = False
        for this_epic in all_epics:
            if epic_number == this_epic['epic_number']:
                epic_details = this_epic
                found = True
                break
        if found is False: 
            if epic_number.startswith(cookie_team_key):
                epic_details = get_epic_details(epic_number)

    if issue['currentEstimateStatistic']['statFieldValue']['value'] == "":
        estimate = 0
    else:
        estimate = issue['currentEstimateStatistic']['statFieldValue']['value']

    return {"ticket_number": issue['key'], "title": issue['summary'],"estimate": estimate, "epic_number": epic_number, "epic_title": epic_details["epic_title"], "ptd_title": epic_details["ptd_title"], "ptd": epic_details["ptd"]}

# gets all unique epics and its ptd
@api_urls.route('/api/epics/<cookie_team_key>')
@cache.cached(timeout=86400)
def api_get_epics(cookie_team_key=""):
    if cookie_team_key == "":
        cookie_team_key = request.cookies.get('team_key')
        if cookie_team_key is None:
            return redirect("/check_team")

    result = all_epics_transformed(cookie_team_key.upper())
    return jsonify(result)

def all_epics_transformed(cookie_team_key):
    all_epics = get_epics(cookie_team_key)
    result = []

    for epic in all_epics['issues']:
        if epic['key'].startswith(cookie_team_key):
            ptd = ''
            ptd_title = ''
            ptd_status = ''
            ptd_status_colour = ''

            for issuelinks in epic['fields']['issuelinks']:
                if 'inwardIssue' in issuelinks:
                    inwardIssue = issuelinks['inwardIssue']
                    if 'key' in inwardIssue:
                        if inwardIssue['key'].startswith('PTD'):
                            ptd = inwardIssue['key']
                            ptd_title = inwardIssue['fields']['summary']
                            ptd_status = inwardIssue['fields']['status']['name']
                            ptd_status_colour = colour_based_on_status(ptd_status)
                # loop through to make sure its epic_number unique
                exists = False
                for item in result:
                    if item['epic_number'] == epic['key']:
                        exists = True
                        break
                if not exists:
                    epic_status = epic['fields']['status']['name']
                    epic_status_colour = colour_based_on_status(epic_status)

                    result.append({"epic_title": epic['fields']['summary'], "epic_number": epic['key'], "ptd": ptd, "ptd_title": ptd_title, "ptd_status": ptd_status, "ptd_colour": ptd_status_colour, "epic_status": epic_status, "epic_status_colour": epic_status_colour})
    return result

def all_ptds_transformed(cookie_team_key):
    all_epics = get_epics(cookie_team_key)
    result = []

    for epic in all_epics['issues']:
        if epic['key'].startswith(cookie_team_key):
            ptd = ''
            ptd_title = ''
            ptd_status = ''
            ptd_status_colour = ''
            for issuelinks in epic['fields']['issuelinks']:
                if 'inwardIssue' in issuelinks:
                    inwardIssue = issuelinks['inwardIssue']
                    if 'key' in inwardIssue:
                        if inwardIssue['key'].startswith('PTD'):
                            ptd = inwardIssue['key']
                            ptd_title = inwardIssue['fields']['summary']
                            ptd_status = inwardIssue['fields']['status']['name']
                            ptd_status_colour = colour_based_on_status(ptd_status)
                            # loop through to make sure its ptd is unique
                            exists = False
                            for item in result:
                                if item['ptd'] == inwardIssue['key']:
                                    exists = True
                                    breakpoint
                            if not exists:
                                result.append({"ptd": ptd, "ptd_title": ptd_title, "ptd_status": ptd_status, "colour": ptd_status_colour})
    return result

# gets all the issues for a given epic
@api_urls.route('/api/epic_issues/<cookie_team_key>/<epic_number>')
def api_get_epic_issues(cookie_team_key, epic_number):
    if cookie_team_key == "":
        cookie_team_key = request.cookies.get('team_key')
    if cookie_team_key is None:
        return redirect("/check_team")
    issues_in_epic=[]
    # if cookie_team_key.upper().startswith(cookie_team_key.upper()):
    issues_in_epic = get_issues_from_epics(epic_number.upper())
    return jsonify(issues_in_epic)

# gets all the unique ptds
@api_urls.route('/api/ptds/<cookie_team_key>')
@cache.cached(timeout=86400)
def api_get_ptds(cookie_team_key=""):
    if cookie_team_key == "":
        cookie_team_key = request.cookies.get('team_key')
        if cookie_team_key is None:
            return redirect("/check_team")

    result = all_ptds_transformed(cookie_team_key.upper())
    return jsonify(result)

# gets all the unique epics and its ptd
# there can be many epics for one ptd
@api_urls.route('/api/ptd/epics/<cookie_team_key>/<ptd_number>')
def api_get_ptd_epics(cookie_team_key, ptd_number):
    if cookie_team_key == "":
      cookie_team_key = request.cookies.get('team_key')
    if cookie_team_key is None:
        return redirect("/check_team")
    epics_in_ptd = get_issue_details(ptd_number.upper())
    result = []
    for issuelinks in epics_in_ptd['fields']['issuelinks']:
        if 'outwardIssue' in issuelinks:
            outwardIssue = issuelinks['outwardIssue']
            if 'key' in outwardIssue:
                if outwardIssue['key'].startswith(cookie_team_key.upper()):
                    epic_status = outwardIssue['fields']['status']['name']
                    result.append({"epic_title": outwardIssue['fields']['summary'], "epic_number": outwardIssue['key'], "epic_status": epic_status, "epic_status_colour": colour_based_on_status(epic_status)})
    return jsonify(result)

@cache.cached(timeout=86400)
def get_issues_from_epics(epic_number):
    result = get_using_custom_query('"Epic%20Link"='+str(epic_number.upper()))
    all_issues = []
    all_issues_2 = []
    if 'issues' in result:
        for issue in result['issues']:
            issue = get_issue_details(issue['key'])
            estimated_number = issue['fields']['customfield_10008']
            estimated_number2 = issue['fields']['customfield_10008']
            issue_status = issue['fields']['status']['name']
            if estimated_number:
                estimated_number = issue['fields']['customfield_10008']
                estimated_number2 = issue['fields']['customfield_10008']
            else:
                estimated_number = "None provided"
                estimated_number2 = 0

            all_issues.append({"issue_number":issue['key'], "estimated": estimated_number, "issue_status": issue_status, "issue_colour": colour_based_on_status(issue_status)})
            all_issues_2.append({ "estimated": estimated_number2, "issue_status": issue_status})
    
    status_totals = dict()
    grouped_status_total = group_tickets_by_issue_status(all_issues_2, "total")
    status_totals["status_totals"] = grouped_status_total
    all_issues.append(status_totals)
    return all_issues

def group_tickets_by_issue_status(tickets, key_name):
    tickets.sort(key=itemgetter("issue_status"))
    result = []
    for key, group in itertools.groupby(tickets, lambda item: item["issue_status"]):
        if key == "":
            key = "No status Assigned"
        
        result.append({"status":key, "status_colour": colour_based_on_status(key), "total" :sum([int(float(item["estimated"])) for item in group])})
    return result

