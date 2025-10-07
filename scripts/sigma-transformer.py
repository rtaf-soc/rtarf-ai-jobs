#!/usr/bin/env python

import os
import subprocess
import time
import psycopg
import redis
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_DB = os.getenv("PG_DB", "dummy")
PG_USER = os.getenv("PG_USER", "dummy")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dummy")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
DELAY_SEC = os.getenv("DELAY_SEC", "10")

def create_sigma_lucene_query(rule_name, rule_def, key_config):
    lucene = ""
    is_ok = False

    cfg_dir = os.getenv("SIGMA_RULE_CFG_DIR", "")
    tmp_dir = os.getenv("TMP_DIR", "/tmp")
    tmp_file = f"{tmp_dir}/{rule_name}"

    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(rule_def)

    config_file = f"{cfg_dir}/{key_config}.yaml"
    print(f"Processing rule [{rule_name}] => [{config_file}]")

    if os.path.exists(config_file):
        #print(f"Processing rule [{rule_name}] => [{config_file}]")
        print(f"Rule definition saved to [{tmp_file}]")

        result = subprocess.run(
            ["sigmac", "-t", "es-qs", "-c", config_file, tmp_file],
            capture_output=True, text=True
        )

        lucene = result.stdout.strip() or "N/A"
        #print(f"Lucene => [{lucene}]")

        is_ok = True
    else:
        print(f"Skip rule [{rule_name}]")

    return is_ok, lucene

def update_rule_lucene(conn, rule_lucenes):

    sql = """UPDATE "HuntingRules" SET lucene_query = %s WHERE rule_id = %s"""

    for r in rule_lucenes:
        lucene = r['lucene']
        id = r['id']
        name = r['name']

        print(f"[{id}]:[{name}] => [{lucene}]")

        values = (lucene, id)
        cur.execute(sql, values)

        conn.commit()

    return

rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
print(f"Connected to Redis host=[{REDIS_HOST}], port=[{REDIS_HOST}]")

conn = psycopg.connect(
    host=PG_HOST,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD,
    row_factory=dict_row
)

print(f"Connected to PostgreSQL host=[{PG_HOST}], db=[{PG_DB}]")

cur = conn.cursor()

cur.execute('SELECT * FROM "HuntingRules" WHERE ref_type = \'Sigma\' ORDER BY rule_name ASC')
rows = cur.fetchall()

cnt = 0
rules_array = []

for row in rows:
    rule_id = row['rule_id']
    rule_name = row['rule_name']
    rule_def = row['rule_definition']

    tokens = rule_name.split('_')
    key_config = '-'.join(tokens[:2])

    is_ok, lucene_str = create_sigma_lucene_query(rule_name, rule_def, key_config)
    if (is_ok):
        rule_lucene = { "id": rule_id, "lucene": lucene_str, "name": rule_name }
        rules_array.append(rule_lucene)

    cnt += 1

update_rule_lucene(conn, rules_array)
print(f"Done processing [{cnt}] records")

cur.close()
conn.close()

time.sleep(int(DELAY_SEC))
