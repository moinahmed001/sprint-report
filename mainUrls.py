from flask import Flask, render_template, redirect, url_for, jsonify

from flask import request
from cache import cache
# from flask_caching import Cache
from flask_cors import CORS, cross_origin
from flask_json import FlaskJSON, JsonError, json_response, as_json
from flask_bootstrap import Bootstrap
from utils import *
from model.jira_api import *

import time
import json
import itertools
from operator import itemgetter
from apiUrls import api_urls

app = Flask(__name__)
app.register_blueprint(api_urls)

FlaskJSON(app)
Bootstrap(app)
CORS(app)
cache.init_app(app)

hostname = "http://127.0.0.1:5000"
url = "https://jira.inbcu.com"

@app.route("/")
@app.route("/index")
def home_page():
    cookie_team_view_id = request.cookies.get('team_view_id')
    if cookie_team_view_id is None:
        return redirect("/check_team")
    all_sprints = fetch_url(hostname+'/api/sprints/'+str(cookie_team_view_id))
    return render_template('index.html', all_sprints=all_sprints)

@app.route("/site-map")
def site_map():
    links = []

    map_of_endpoints = app.url_map.iter_rules()
    list_of_endpoints = list(map_of_endpoints)
    for endpoint in list_of_endpoints:
        str_endpoint = str(endpoint)
        links.append(str_endpoint)

    return jsonify(links)

@app.route('/check_team')
def check_team():
    teams = normalise_teams(get_all_teams_from_jira())
    return render_template('setCookie.html', teams=teams)

def normalise_teams(teams):
    result = []
    for team in teams:
        data = {"team_name": team["name"], "team_id": team["id"], "team_key": team["key"]}
        result.append(data)
    return result

@app.route("/sprint/<sprintId>")
def sprint_details_page(sprintId):
    cookie_team_id = request.cookies.get('team_id')
    cookie_team_view_id = request.cookies.get('team_view_id')
    cookie_team_key = request.cookies.get('team_key')

    if cookie_team_id is None or cookie_team_view_id is None or cookie_team_key is None:
        return redirect("/check_team")

    sprint_tickets = fetch_url(hostname+'/api/sprint/id/'+str(sprintId)+'/'+str(cookie_team_id)+'/'+str(cookie_team_view_id)+'/'+str(cookie_team_key))
    grouped_completed_ptds = group_tickets_by_project(sprint_tickets["completed_tickets"], "completed_value")
    grouped_not_completed_ptds = group_tickets_by_project(sprint_tickets["not_completed_tickets"], "not_completed_value")

    for not_completed_project in grouped_not_completed_ptds:
        found = False
        for completed_project in grouped_completed_ptds:
            if not_completed_project["ptd_title"] == completed_project["ptd_title"]:
                completed_project["not_completed_value"] = not_completed_project["not_completed_value"]
                found = True

        if found is False:
            not_completed_project["completed_value"] = 0
            grouped_completed_ptds.append(not_completed_project)
    
    total_effort = {"completed_effort": 0, "not_completed_effort": 0}

    for ptds in grouped_completed_ptds:
        if 'completed_value' in ptds:
            total_effort['completed_effort'] = total_effort['completed_effort'] + ptds["completed_value"]
        if 'not_completed_value' in ptds:
            total_effort['not_completed_effort'] = total_effort['not_completed_effort'] + ptds["not_completed_value"]
    sprint_report_url = str(url)+"/secure/RapidBoard.jspa?rapidView="+str(cookie_team_view_id)+"&projectKey="+str(cookie_team_key)+"&view=reporting&chart=sprintRetrospective&sprint="+str(sprintId)
    return render_template('sprint_details_page.html', sprint_report_url=sprint_report_url, url=url, sprint_tickets=sprint_tickets, cookie_team_view_id=cookie_team_view_id, cookie_team_id=cookie_team_id, grouped_ptds=grouped_completed_ptds, total_effort=total_effort)

def group_tickets_by_project(tickets, key_name):
    tickets.sort(key=itemgetter("ptd_title"))
    result = []
    for key, group in itertools.groupby(tickets, lambda item: item["ptd_title"]):
        if key == "":
            key = "No PTD Assigned"

        result.append({"ptd_title":key, key_name :sum([int(float(item["estimate"])) for item in group])})
    return result

@app.route("/epics_to_ptd")
def epics_to_ptd_page():
    cookie_team_id = request.cookies.get('team_id')
    cookie_team_key = request.cookies.get('team_key')

    if cookie_team_id is None or cookie_team_key is None:
        return redirect("/check_team")

    epics_to_ptds = fetch_url(hostname+'/api/epics/'+str(cookie_team_key))
    return render_template('epics_to_ptd.html', url=url, epics_to_ptds=epics_to_ptds)

@app.route("/ptd_details")
def ptd_details_page():
    cookie_team_id = request.cookies.get('team_id')
    cookie_team_key = request.cookies.get('team_key')

    if cookie_team_id is None or cookie_team_key is None:
        return redirect("/check_team")

    ptds = fetch_url(hostname+'/api/ptds/'+str(cookie_team_key))
    return render_template('ptd_details.html', url=url, ptds=ptds)
    

if __name__ == "__main__":
    app.run(debug=True)
