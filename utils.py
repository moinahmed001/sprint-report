import json
import requests
from datetime import date, datetime
from cache import cache

def fetch_url(url, headers=None):
    all_headers = {}
    session = requests.Session()
    if headers:
        for key, value in headers.items():
            if key == "Authorization":
                session.auth = (value.split(":")[0], value.split(":")[1])
                continue
            session.headers.update({key: value})
    resp = session.get(url)

    if resp.status_code != 200:
        print("ERROR cannot be fetched {} for url {}".format(resp, url))
        return {"error": resp.status_code}
    if resp.json() == None or resp.json() == "":
        print(">>>>URL " + url)
        print("ERROR")
        return {'error': 'no data found'}

    data = json.loads(resp.content)
    return data

# @cache.cached(timeout=50, key_prefix='all_comments')
# @cache.cached(timeout=1800)
def make_cache_call(session, url):
    return session.get(url)

def readable_date(date):
    date_obj = datetime.strptime(date, '%d/%b/%y %I:%M %p')
    return custom_strftime('%b {S}, %Y', date_obj)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def colour_based_on_status(status):
    mapping = {
        "OPEN": "primary",
        "TO DO": "primary",
        "BACKLOGGED": "primary",
        "IN REVISION": "primary",

        "IN TRIAGE": "secondary",
        "TRIAGE": "secondary",
        "IN REFINEMENT": "secondary",
        "IN BA REVIEW": "secondary",
        "IN TDA REVIEW": "secondary",
        "IN SOLUTION DESIGN": "secondary",
        "IN REQ. VALIDATION": "secondary",

        "BLOCKED": "danger",
        "QA BLOCKED": "danger",
        "ON HOLD": "danger",

        "IN IA": "warning",
        "IN PLANNING": "warning",
        "IN DEV": "warning",
        "IN PROGRESS": "warning",
        "IN REVIEW": "light text-warning",

        "IN QA": "dark",
        "READY FOR QA": "dark",
        "IN ROLLOUT": "dark",
        "IN DELIVERY": "dark",

        "CANCELLED": "success",
        "UAT READY": "success",
        "CLOSED": "success",
        "DONE": "success"
        }
    if status.upper() in mapping:
        return mapping[status.upper()]
    return ""