import os
from dotenv import load_dotenv
import psycopg2
import duckdb
import pandas as pd
from functools import lru_cache

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 5432)),
}

DUCKDB_PATH = os.getenv("DUCKDB_PATH", ":memory:")

_pg_conn = None
_duck_conn = None


def get_pg_connection():
    global _pg_conn
    if _pg_conn is None or _pg_conn.closed:
        _pg_conn = psycopg2.connect(connect_timeout=5, sslmode="require",**DB_CONFIG)
        _pg_conn.autocommit = True
    return _pg_conn


def get_duck_connection():
    global _duck_conn
    if _duck_conn is None:
        _duck_conn = duckdb.connect(DUCKDB_PATH)
    return _duck_conn


def fetch_pg(query, params=None):
    conn = get_pg_connection()
    return pd.read_sql_query(query, conn, params=params)


def fetch_duck(query):
    conn = get_duck_connection()
    return conn.execute(query).df()


@lru_cache(maxsize=4)
def q_total_events():
    query = "SELECT COUNT(*) AS total_all FROM events"
    return fetch_duck(query)


def q_total_participants(category, org=None, start=None, end=None):

    query = """
        SELECT 
            SUM(current) AS current,
            SUM(total) AS total,
            ROUND((SUM(current)::numeric / NULLIF(SUM(total),0))*100,2) AS percentage
        FROM participants
        WHERE category = %s
    """

    params = [category]

    if org:
        query += " AND org_uuid = %s"
        params.append(org)

    if start and end:
        query += " AND event_date BETWEEN %s AND %s"
        params.extend([start, end])

    return fetch_pg(query, params)


def q_by_pillar(category, org=None, start=None, end=None):

    query = """
        SELECT 
            pillar_title AS title,
            SUM(current) AS current
        FROM participants
        WHERE category = %s
    """

    params = [category]

    if org:
        query += " AND org_uuid = %s"
        params.append(org)

    if start and end:
        query += " AND event_date BETWEEN %s AND %s"
        params.extend([start, end])

    query += " GROUP BY pillar_title ORDER BY pillar_title"

    return fetch_pg(query, params)


def q_by_program(category, subcategory=None, program=None,
                 org=None, start=None, end=None):

    query = """
        SELECT 
            program_title AS title,
            SUM(current) AS current,
            SUM(total) AS total,
            ROUND((SUM(current)::numeric / NULLIF(SUM(total),0))*100,2) AS percentage
        FROM participants
        WHERE category = %s
    """

    params = [category]

    if subcategory:
        query += " AND subcategory = %s"
        params.append(subcategory)

    if program:
        query += " AND program_id = %s"
        params.append(program)

    if org:
        query += " AND org_uuid = %s"
        params.append(org)

    if start and end:
        query += " AND event_date BETWEEN %s AND %s"
        params.extend([start, end])

    query += " GROUP BY program_title ORDER BY program_title"

    return fetch_pg(query, params)