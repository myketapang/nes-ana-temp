import json
import tempfile
from nes_query import connect_duckdb, q_total_events

def handler(event, context):
    params = event.get("queryStringParameters") or {}
    category = int(params.get("category", 1))

    duck = connect_duckdb()
    df = q_total_events(duck)
    duck.close()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)

    with open(tmp.name, "r") as f:
        csv_data = f.read()

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=nes_export.csv"
        },
        "body": csv_data
    }
