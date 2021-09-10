import json
import re


def load_json(file_name):
    try:
        with open(file_name, encoding="utf-8") as json_data:
            d = json.load(json_data)
            return d
    except Exception as e:
        return {}


def write_json(file_name, json_data):
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile, ensure_ascii=False)
        return json_data


def to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_camel(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
