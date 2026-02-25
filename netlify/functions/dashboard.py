# Netlify Python Function
# Requires: pip install psycopg2-binary duckdb pandas
import os
print("DB_HOST:", os.getenv("DB_HOST"))

import json
from nes_query import (
    connect_psycopg2,
    connect_duckdb,
    q_total_events,
    q_total_participants,
    q_by_pillar,
    q_by_program
)

def handler(event, context):
    params = event.get("queryStringParameters") or {}

    category = int(params.get("category", 1))
    subcategory = params.get("subcategory")
    program = params.get("program")
    org = params.get("org")
    start = params.get("start")
    end = params.get("end")

    duck = connect_duckdb()
    pg = connect_psycopg2()

    data = {
        "events": q_total_events(duck).to_dict("records")[0],
        "participants": q_total_participants(pg, category, org, start, end).to_dict("records")[0],
        "pillar": q_by_pillar(pg, category, org, start, end).to_dict("records"),
        "program": q_by_program(pg, category, subcategory, program, org, start, end).to_dict("records"),
    }

    duck.close()
    pg.close()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data)
    }
