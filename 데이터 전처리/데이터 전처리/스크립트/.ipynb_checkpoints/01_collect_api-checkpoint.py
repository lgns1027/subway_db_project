import csv, os, time
from datetime import date
import requests

# ───────────── [설정] ─────────────
KEY = "617666617363686f3631705272586e"

# 역 기준표: 서울교통공사_역명 지하철역 검색 (OA-121)
STATION_SERVICE = "SearchInfoBySubwayNameService"   # 샘플 URL과 다르면 수정

# 빠른하차정보: 페이지의 샘플 URL에 나온 서비스명으로 반드시 교체
FAST_EXIT_SERVICE = "빠른하차_서비스명"

# ──────────────────────────────────

BASE = "http://openapi.seoul.go.kr:8088"
OUT = "raw"
PAGE = 1000          # 열린데이터광장 1회 최대 건수


def fetch_all(service, extra=""):
    """1000건씩 끝까지 받아 row 리스트로 반환. extra는 URL 뒤에 붙는 추가 인자(예: 날짜)."""
    rows, start = [], 1
    while True:
        end = start + PAGE - 1
        url = f"{BASE}/{KEY}/json/{service}/{start}/{end}/{extra}"
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        body = res.json()
        if service not in body:                       # 오류 응답: {"RESULT": {"CODE":..., "MESSAGE":...}}
            print("  응답 오류:", body.get("RESULT", body))
            break
        data = body[service]
        rows += data.get("row", [])
        total = int(data.get("list_total_count", 0))
        if end >= total:
            break
        start = end + 1
        time.sleep(0.2)                               # 서버 부담 줄이기
    return rows


def save(rows, name):
    if not rows:
        print(f"  {name}: 0건 (저장 안 함)")
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {name}: {len(rows)}건 저장 → {path}")


if __name__ == "__main__":
    print("[1] 역 기준표")
    save(fetch_all(STATION_SERVICE), "station_master.csv")

    print("[2] 빠른하차정보")
    save(fetch_all(FAST_EXIT_SERVICE), "fast_exit.csv")

    print(f"\n수집일: {date.today()}  ← 보고서 2.1절 '기준 시점'에 기록")
