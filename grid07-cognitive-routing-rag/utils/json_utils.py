import json

def parse_json_safely(json_str: str, default_val: dict = None) -> dict:
    if default_val is None:
        default_val = {}
    try:
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        return json.loads(json_str.strip())
    except Exception:
        return default_val
