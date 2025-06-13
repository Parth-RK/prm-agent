import json
import os

def count_api_call(filename: str):
    data_file = 'api_calls_count.json'
    data = {
        "total_calls": 0,
        "files": {}
    }

    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                content = f.read()
                if content:
                    data = json.loads(content)
                if "total_calls" not in data:
                    data["total_calls"] = 0
                if "files" not in data:
                    data["files"] = {}
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    data["total_calls"] = data.get("total_calls", 0) + 1

    file_basename = os.path.basename(filename)
    data["files"][file_basename] = data["files"].get(file_basename, 0) + 1

    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)