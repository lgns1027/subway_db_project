"""
01b_collect_fast_exit.py  -  공공데이터포털 '서울교통공사_빠른하차정보' API → raw/fast_exit.csv

※ 이 API는 서울 열린데이터광장 키가 아니라 공공데이터포털(data.go.kr) 인증키가 필요하다.
   마이페이지 > 데이터활용 > Open API > 활용신청 현황 > '일반 인증키(Decoding)'를 복사.

실행: 노트북에서 %run 01b_collect_fast_exit.py  (또는 python 01b_collect_fast_exit.py)
"""
import csv, os, time
import xml.etree.ElementTree as ET
import requests

# ───────────── [설정] ─────────────
DATA_GO_KEY = "4e24ef83da14995de3faa058632e885a9f7e0d0295cb25359d080fa33f84cc4c"
URL = "https://apis.data.go.kr/B553766/inout/getFstExit"
ROWS = 1000                     # 한 번에 받을 건수 (오류 나면 100으로 줄이기)
EXTRA = {}                      # 명세에 필수 변수가 더 있으면 여기에: 예) {"lineNm": "2호선"}
# ──────────────────────────────────

OUT = "raw"


def find_items(obj):
    """JSON 응답 어디에 있든 데이터 목록(dict 리스트)과 totalCount를 찾아낸다."""
    total, items = None, None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == "totalcount":
                total = int(v)
            elif k.lower() in ("item", "items", "row", "data") and isinstance(v, list) and v and isinstance(v[0], dict):
                items = v
            elif k.lower() == "item" and isinstance(v, dict):      # 1건일 때 dict로 오는 경우
                items = [v]
            else:
                t, i = find_items(v)
                total = total if total is not None else t
                items = items if items is not None else i
    return total, items


def parse(res):
    """JSON이면 JSON으로, 아니면 XML로 파싱해서 (totalCount, rows, 오류메시지) 반환"""
    try:
        total, items = find_items(res.json())
        return total, items or [], None
    except ValueError:
        pass
    root = ET.fromstring(res.content)
    err = root.findtext(".//returnAuthMsg") or (root.findtext(".//resultMsg")
                                                if root.findtext(".//resultCode") not in (None, "00", "0", "INFO-000") else None)
    items = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("item")]
    total = root.findtext(".//totalCount")
    return (int(total) if total else None), items, err


def fetch_all():
    rows, page = [], 1
    while True:
        params = {"serviceKey": DATA_GO_KEY, "pageNo": page, "numOfRows": ROWS,
                  "type": "json", "dataType": "JSON", "_type": "json", **EXTRA}
        res = requests.get(URL, params=params, timeout=30)
        if res.status_code != 200:
            print(f"  HTTP {res.status_code}: {res.text[:300]}")
            break
        total, items, err = parse(res)
        if err:
            print("  응답 오류:", err)
            break
        if page == 1:
            print(f"  전체 {total}건 (응답 앞부분: {res.text[:200]!r})")
        rows += items
        if not items or total is None or len(rows) >= total:
            break
        page += 1
        time.sleep(0.2)
    return rows


if __name__ == "__main__":
    print("[빠른하차정보]")
    rows = fetch_all()
    if not rows:
        print("  0건 - 위 응답 내용을 캡처해서 보내주세요 (인증키는 가리기)")
    else:
        os.makedirs(OUT, exist_ok=True)
        keys = list(dict.fromkeys(k for r in rows for k in r))          # 모든 행의 필드 합집합
        with open(f"{OUT}/fast_exit.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"  {len(rows)}건 저장 → {OUT}/fast_exit.csv")
        print(f"  필드: {keys}")
