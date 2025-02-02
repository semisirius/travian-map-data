from datetime import datetime, timezone, timedelta
from json import dump
from pathlib import Path
import urllib.request

mapsql_fields = ["field_id", "x", "y", "tribe", "village_id", "village_name", "player_id", "player_name", "alliance_id", "alliance_tag", "population", "region", "capital",	"city", "harbor", "victory_points"]
mapsql_types = [int, int, int, int, int, str, int, str, int, str, int, str, bool, bool, bool, int]

def load_mapsql(server_url):
    url = f"{server_url}/map.sql"
    response = urllib.request.urlopen(url)
    if response.status != 200:
        raise Exception(f"Request for {server_url} return status {response.status} with reason: {response.reason}")

    return response.read().decode("utf8")

def actual_value(raw, field_type):
    if raw == "NULL":
        return None
    elif field_type is str:
        return raw
    elif field_type is int:
        return int(raw)
    elif field_type is bool:
        return raw == "TRUE"


def parse_mapsql(mapsql):
    matches = []
    rows = mapsql.splitlines()
    for row in rows:
        opening = row.index("(")
        closing = row.rindex(")")
        values = row[opening+1:closing]
        field_index = 0
        opened = False
        buffer = ""
        matches_row = {}
        for char in values:
            if char == "," and not opened:
                current_type = mapsql_types[field_index]
                current_field = mapsql_fields[field_index]
                value = actual_value(buffer, current_type)
                matches_row[current_field] = value
                buffer = ""
                field_index += 1
            elif char == " " and not opened:
                pass
            elif char == "'":
                opened = not opened
            else:
                buffer += char
        matches.append(matches_row)
    return matches

def load_servers():
    with open("servers.txt", "r", encoding="utf8") as server_config:
        return server_config.read().splitlines()

def server_name(url):
    parts = url.removeprefix("https://").split(".")
    return f"{parts[2]}_{parts[0]}"

servers = load_servers()
print(f"{len(servers)} servers configured, starting import")
for idx, server in enumerate(servers):
    print(f"Importing map data for {server} {idx+1}/{len(servers)}")
    raw_data = load_mapsql(server)
    print("Raw map data loaded, parsing")
    parsed = parse_mapsql(raw_data)
    date = datetime.now(timezone.utc) - timedelta(days=1)
    formatted_date = date.strftime("%Y-%m-%d")
    print(f"Map data parsed, saving for {formatted_date}")
    folder = server_name(server)
    output_path = Path(f"{folder}/{formatted_date}.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    dump(parsed, output_path.open("w", encoding="utf8"))

print("All done")