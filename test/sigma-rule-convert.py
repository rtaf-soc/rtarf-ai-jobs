#!/usr/bin/env python3
import sys
import yaml  # ถ้าจะอ่าน yaml
import re

def load_field_mapping(mapping_file):
    with open(mapping_file, 'r') as f:
        data = yaml.safe_load(f)
    # data['fields'] เป็น dict {rule_field: target_field}
    return data.get('fields', {})

def replace_fields(query, field_mapping):
    for orig_field, target_field in field_mapping.items():
        # replace field.keyword / field.* → target_field.keyword
        pattern = re.compile(rf'\b{re.escape(orig_field)}\b(\.keyword)?')
        query = pattern.sub(f"{target_field}.keyword", query)
    return query

def main():
    # ตรวจสอบจำนวน argument
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <config.yaml> <es-qs.txt>")
        sys.exit(1)

    # อ่าน argument
    config_file = sys.argv[1]
    sigma_query_file = sys.argv[2]

    #print(f"Config file: {config_file}")
    #print(f"Sigma query file: {sigma_query_file}")

    # ถ้าต้องการโหลด YAML
    try:
        with open(config_file, 'r') as f:
            fields_map = load_field_mapping(config_file)
        #print("Config loaded:", fields_map)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)

    try:
        with open(sigma_query_file, "r", encoding="utf-8") as f:
            qyery_content = f.read()  # อ่านไฟล์ทั้งหมดเป็น string
        #print("Sigma query:", qyery_content)
    except FileNotFoundError:
        print(f"Error: Sigma rule file '{sigma_query_file}' not found.")
        sys.exit(1)

    lucene = replace_fields(qyery_content, fields_map).strip()
    print(lucene)

if __name__ == "__main__":
    main()
