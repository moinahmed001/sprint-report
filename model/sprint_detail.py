from flask import jsonify
from flask import Flask, request
from connection import *
from utils import *

def create_sprint_detail(sprint_id, team_id, team_view_id):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        conn.execute("INSERT or ignore INTO sprint_detail (sprint_id, team_id, team_view_id) values (?, ?, ?);",(sprint_id, team_id, team_view_id))
        return cur.lastrowid

def get_sprint_detail(sprint_id):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT sd.team_id, sd.team_view_id, si.start_date, si.end_date FROM sprint_detail as sd left join sprint_info as si on sd.sprint_id=si.sprint_id where sd.sprint_id = "+str(sprint_id) +" LIMIT 1")
        sprints_detail = cur.fetchone()
        if sprints_detail is not None:
            return {"team_id": sprints_detail[0], "team_view_id": sprints_detail[1], "start_date": readable_date(sprints_detail[2]), "end_date": readable_date(sprints_detail[3])}
    return {}
