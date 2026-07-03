import csv
import json
import os
import time
from datetime import datetime
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TOP_N = 200
OUT_CSV = "leaderboard_log.csv"
BASE_URL = "https://d32m8h9cownzsg.cloudfront.net/public/leaderboard_group/latest.json"


def fetch_json():
    url = f"{BASE_URL}?_={int(time.time() * 1000)}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def find_rows(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["rows", "data", "leaderboard", "rankings", "entries", "items", "teams"]:
            if key in data and isinstance(data[key], list):
                return data[key]

        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value

    raise ValueError("leaderboard 목록을 찾지 못했습니다.")


def get_team_name(row):
    for key in ["team", "team_name", "teamName", "name", "displayName", "title"]:
        if key in row:
            value = row[key]
            if isinstance(value, dict):
                return value.get("name") or value.get("team_name") or str(value)
            return str(value)
    return str(row)


def get_rank(row, default_rank):
    for key in ["rank", "ranking", "place", "position"]:
        if key in row:
            try:
                return int(row[key])
            except Exception:
                pass
    return default_rank


def read_leaderboard():
    rows = find_rows(fetch_json())

    ranked = []
    for i, row in enumerate(rows, start=1):
        ranked.append((get_rank(row, i), get_team_name(row)))

    ranked.sort(key=lambda x: x[0])
    return ranked[:TOP_N]


def load_csv():
    if not os.path.exists(OUT_CSV):
        return ["team"], {}

    with open(OUT_CSV, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        return ["team"], {}

    header = rows[0]
    table = {row[0]: row[1:] for row in rows[1:] if row}
    return header, table


def save_csv(header, table):
    def sort_key(item):
        _, values = item
        try:
            return int(values[-1])
        except Exception:
            return 10**9

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for team, values in sorted(table.items(), key=sort_key):
            writer.writerow([team] + values)


def main():
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H시")
    leaderboard = read_leaderboard()

    header, table = load_csv()
    old_count = len(header) - 1

    # 같은 시간대에 두 번 실행되면 중복 열을 만들지 않음
    if now in header:
        print(f"{now} 기록이 이미 있어서 건너뜁니다.")
        return

    header.append(now)
    current_ranks = {team: rank for rank, team in leaderboard}

    for team in table:
        table[team].append(current_ranks.get(team, ""))

    for rank, team in leaderboard:
        if team not in table:
            table[team] = [""] * old_count + [rank]

    save_csv(header, table)
    print(f"{now} 저장 완료")


if __name__ == "__main__":
    main()
