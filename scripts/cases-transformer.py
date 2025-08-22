#!/usr/bin/env python

import os
import psycopg 
import json
import uuid
import redis
import hashlib
from dotenv import load_dotenv
from psycopg.rows import dict_row
from sentence_transformers import SentenceTransformer

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_DB = os.getenv("PG_DB", "dummy")
PG_USER = os.getenv("PG_USER", "dummy")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dummy")
START_CASE_NO = os.getenv("START_CASE_NO", "1") #386
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

def insert_data(rd, conn, cur, row, embedded_text, normalized_text, category, chunk_no):
    case_no = row['case_no']

    hash_object = hashlib.sha256(normalized_text.encode())
    hex_dig = hash_object.hexdigest()

    key = f"case_transformer:{case_no}:{category}:{chunk_no}"
    value = rd.get(key)

    if (value == hex_dig):
        # No need to do any transform
        print(f"Found this key=[{key}], value=[{value}] in cache, no need to do any transform")
        return

    rd.set(key, hex_dig) #No expiration

    sql = """
INSERT INTO "TextEmbedding"
(
    embedding_id, 
    org_id, 
    embedding_bge_m3,
    normalized_text,
    category,
    ref_no,
    chunk_no,
    tags,
    created_date
)
VALUES
(
    %s, 
    %s, 
    %s,
    %s,
    %s,
    %s,
    %s,
    '',
    NOW()
)
"""
    id = uuid.uuid4()

    values = (id, 'default', embedded_text, normalized_text, category, case_no, chunk_no)
    cur.execute(sql, values)
    conn.commit()

    return

def transform_text(model, text):
    embeddings = model.encode(text)
    return embeddings.tolist()

def normalized_text(row, field_name, field_name_th):
    if field_name not in row:
        raise ValueError(f"Field '{field_name}' not found in row")
    
    text = row[field_name]

    start_date = row['start_date']
    formatted_date = start_date.strftime("%d/%m/%Y")
    case_no = row['case_no']
    case_title = row['case_title']
    case_severity = row['case_severity']
    created_by = row['created_by']

    data_map = {
        f"{field_name_th}": text,
        "ชื่อเรื่อง": case_title,
        "ชนิดของข้อมูล": field_name_th,
        "วันที่เกิดเหตุการณ์": f"{formatted_date} อยู่ในรูปปี ค.ศ. DD/MM/YYYY",
        "หมายเลขเหตุการณ์": f"{case_no}",
        "ระดับความรุนแรง": f"{case_severity}",
        "รายงานเหตุการณ์โดย": f"{created_by}",
    }

    json_str = json.dumps(data_map, ensure_ascii=False, indent=2)
 
    return json_str

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
print(f"Selected only case number start from [{START_CASE_NO}]")

cur = conn.cursor()

cur.execute('SELECT * FROM "Cases" ORDER BY created_date ASC')
rows = cur.fetchall()

model = SentenceTransformer('BAAI/bge-m3')
cnt = 0

for row in rows:
    case_no = row['case_no']
    if int(case_no) < int(START_CASE_NO):
        continue
    
    cnt += 1

    normalized_summary = normalized_text(row, 'case_summary', 'สรุปเหตุการณ์')
    vector_summary = transform_text(model, normalized_summary)
    insert_data(rd, conn, cur, row, vector_summary, normalized_summary, 'case_summary', 1)

    normalized_desc = normalized_text(row, 'description', 'รายละเอียดเหตุการณ์')
    vector_desc = transform_text(model, normalized_desc)
    insert_data(rd, conn, cur, row, vector_desc, normalized_desc, 'case_description', 1)

    print(f"Transformed case number=[{case_no}]")

print(f"Done processing [{cnt}] records")

cur.close()
conn.close()
