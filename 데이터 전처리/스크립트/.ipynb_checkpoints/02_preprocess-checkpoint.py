"""
02_preprocess.py  -  인코딩 변환, 시간대 열→행 변환, 역 매칭표 생성 (A 담당 전처리 스크립트)

준비물 (raw/ 폴더)
  station_master.csv   : 01_collect_api.py 결과 (역 기준표, 서울교통공사_역명 지하철역 검색)
  fast_exit.csv        : 01_collect_api.py 결과 (빠른하차정보)
  congestion.xlsx      : 공공데이터포털 '서울교통공사_지하철혼잡도정보' (csv도 가능)
  ride_hourly.csv      : 공공데이터포털 '서울교통공사_역별 일별 시간대별 승하차인원' (xlsx도 가능)

필요 패키지: pip install pandas openpyxl
실행: python 02_preprocess.py
결과: clean/ 폴더
  congestion_long.csv      (역코드, 요일구분, 상하구분, 시간대, 혼잡도)
  ride_hourly_long.csv     (역코드, 수송일자, 시간대, 승차인원, 하차인원)
  station_match.csv        역 기준표 + 각 데이터에 존재하는지 여부
  unmatched_*.csv          자동 매칭 실패 목록 → manual_fix.csv에 채워 넣고 다시 실행

매칭 원리
  서울교통공사 데이터의 '역번호'(예: 서울역 1호선 = 150)는 역 기준표의 전철역코드(0150)와 같은 체계.
  → 숫자로 바꿔 비교하고, 실패하면 (호선, 역명)으로 다시 시도한다.
"""
import os, re
import pandas as pd

RAW, CLEAN = "raw", "clean"
os.makedirs(CLEAN, exist_ok=True)

# ───────────── [설정] 실제 컬럼명을 보고 맞추기 ─────────────
# 역 기준표 (SearchInfoBySubwayNameService 출력값)
M_CODE, M_NAME, M_LINE = "STATION_CD", "STATION_NM", "LINE_NUM"
# 혼잡도
C_DAY, C_LINE, C_NO, C_NAME, C_DIR = "요일구분", "호선", "역번호", "역명", "상하구분"   # 요일구분 = 시트 이름
# 시간대별 승하차 (캡처로 확인한 컬럼)
R_DATE, R_LINE, R_NO, R_NAME, R_TYPE = "수송일자", "호선", "역번호", "역명", "승하차구분"
RIDE_FROM, RIDE_TO = "2025-12-01", "2025-12-31"       # 기간을 자를 때: 예) "2025-10-01", "2025-12-31"
# 빠른하차 (getFstExit 응답 필드)
F_CODE_CANDIDATES = ["stnCd", "stnNo"]        # 역 기준표와 더 잘 맞는 쪽을 자동 선택
F_LINE, F_NAME = "lineNm", "stnNm"
TARGET_LINES = {str(i) for i in range(1, 9)}   # 1~8호선
# ─────────────────────────────────────────────────────────────


def read_any(name):
    """raw/name.(xlsx|csv)을 찾아 읽기. CSV는 UTF-8 → CP949 순으로 시도."""
    for ext in ("xlsx", "csv"):
        path = f"{RAW}/{name}.{ext}"
        if not os.path.exists(path):
            continue
        if ext == "xlsx":
            df = pd.read_excel(path, dtype=str)
        else:
            for enc in ("utf-8-sig", "cp949", "euc-kr"):
                try:
                    df = pd.read_csv(path, encoding=enc, dtype=str)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"인코딩을 알 수 없음: {path}")
        df.columns = [str(c).strip() for c in df.columns]
        print(f"  {os.path.basename(path)}: {len(df)}행, 컬럼 = {list(df.columns)}")
        return df
    raise FileNotFoundError(f"raw/{name}.xlsx 또는 raw/{name}.csv가 없습니다.")


def norm_name(s):
    """역명 비교용 키: 괄호 부기명·공백 제거, 끝의 '역' 제거 (서울역 → 서울)"""
    s = re.sub(r"\(.*?\)", "", str(s)).replace(" ", "").strip()
    return s[:-1] if len(s) > 1 and s.endswith("역") else s


def norm_line(s):
    """'01호선', '1호선', '1' → '1'  (인천2호선·신분당선 같은 다른 노선은 이름 그대로 둠)"""
    s = str(s).strip()
    m = re.fullmatch(r"0?(\d+)(호선)?", s)
    return str(int(m.group(1))) if m else s


def norm_no(s):
    """'0150', '150', '150.0' → '150' (숫자 코드 비교용)"""
    m = re.search(r"\d+", str(s))
    return str(int(m.group())) if m else None


def to_num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "").str.strip(), errors="coerce")


def save(df, name):
    df.to_csv(os.path.join(CLEAN, name), index=False, encoding="utf-8-sig")
    print(f"  → clean/{name} ({len(df)}행)")


def attach_code(df, line_col, no_col, name_col, source):
    """역번호 → 전철역코드 매칭, 실패 시 (호선, 역명) 매칭, 그래도 실패하면 manual_fix.csv 적용"""
    df["line"] = df[line_col].map(norm_line)
    df["no"] = df[no_col].map(norm_no)
    df["key"] = df[name_col].map(norm_name)
    df = df.merge(master[["no", M_CODE]], on="no", how="left")
    by_name = master[["line", "key", M_CODE]].rename(columns={M_CODE: "_cd2"})
    df = df.merge(by_name, on=["line", "key"], how="left")
    df[M_CODE] = df[M_CODE].fillna(df["_cd2"])
    for _, r in fixes[fixes["source"] == source].iterrows():
        df.loc[(df["line"] == norm_line(r["line"])) & (df[name_col] == r["raw_name"]), M_CODE] = r["station_cd"]
    miss = df[df[M_CODE].isna()][[line_col, no_col, name_col]].drop_duplicates()
    save(miss, f"unmatched_{source}.csv")
    return df.drop(columns=["_cd2"])


# 1. 역 기준표 ------------------------------------------------------------
print("[1] 역 기준표")
master = read_any("station_master")
master["line"] = master[M_LINE].map(norm_line)
master = master[master["line"].isin(TARGET_LINES)].copy()
master["key"] = master[M_NAME].map(norm_name)
master["no"] = master[M_CODE].map(norm_no)

fixes = (pd.read_csv("manual_fix.csv", dtype=str, encoding="utf-8-sig") if os.path.exists("manual_fix.csv")
         else pd.DataFrame(columns=["source", "line", "raw_name", "station_cd"]))

# 2. 혼잡도: 시간대 열 → 행 ----------------------------------------------
print("[2] 혼잡도")
if os.path.exists(f"{RAW}/congestion.xlsx"):
    # 2026-09-30 기준 파일: 시트가 평일/토요일/일요일로 나뉨 → 시트 이름을 요일구분 열로
    sheets = pd.read_excel(f"{RAW}/congestion.xlsx", sheet_name=None, dtype=str)
    cong = pd.concat([df.assign(**{C_DAY: name.strip()}) for name, df in sheets.items()], ignore_index=True)
    cong.columns = [str(c).strip() for c in cong.columns]
    print(f"  congestion.xlsx: 시트 {list(sheets)}, {len(cong)}행")
else:
    cong = read_any("congestion")
time_cols = [c for c in cong.columns
             if re.match(r"^\d{1,2}:\d{2}~\d{1,2}:\d{2}$", c) or re.match(r"^\d{1,2}시\d{2}분$", c)]
print(f"  시간대 열 {len(time_cols)}개: {time_cols[:2]} ... {time_cols[-2:]}")
cl = cong.melt(id_vars=[C_DAY, C_LINE, C_NO, C_NAME, C_DIR], value_vars=time_cols,
               var_name="시간대", value_name="혼잡도")
cl["시간대"] = (cl["시간대"].str.replace(r"(\d+)시(\d+)분", lambda m: f"{int(m[1]):02d}:{m[2]}", regex=True)
               .str.replace(r"^(\d{2}:\d{2})~.*$", r"\1", regex=True))          # '05:30~06:00' → '05:30'(시작 시각)
cl["혼잡도"] = to_num(cl["혼잡도"])
cl = attach_code(cl, C_LINE, C_NO, C_NAME, "congestion")
save(cl[[M_CODE, C_LINE, C_NAME, C_DAY, C_DIR, "시간대", "혼잡도"]], "congestion_long.csv")

# 3. 시간대별 승하차: 시간대 열 → 행, 승차/하차를 한 행으로 ------------------
print("[3] 시간대별 승하차")
ride = read_any("ride_hourly")
ride[R_DATE] = pd.to_datetime(ride[R_DATE], errors="coerce").dt.date
n0 = len(ride)
ride = ride[ride[R_DATE].notna()].copy()                        # 파일 끝의 빈 행 제거
print(f"  빈 행 {n0 - len(ride)}개 제거")
if RIDE_FROM:
    ride = ride[ride[R_DATE] >= pd.to_datetime(RIDE_FROM).date()]
if RIDE_TO:
    ride = ride[ride[R_DATE] <= pd.to_datetime(RIDE_TO).date()]
print(f"  기간: {ride[R_DATE].min()} ~ {ride[R_DATE].max()}")
slot_cols = [c for c in ride.columns if re.search(r"시이전|시간대|시이후", c)]
print(f"  시간대 열 {len(slot_cols)}개: {slot_cols[:2]} ... {slot_cols[-2:]}")
rl = ride.melt(id_vars=[R_DATE, R_LINE, R_NO, R_NAME, R_TYPE], value_vars=slot_cols,
               var_name="시간대", value_name="인원")
rl["시간대"] = (rl["시간대"].str.replace("시간대", "", regex=False)    # '06-07시간대' → '06-07'
                .str.replace(r"^06시이전$", "00-06", regex=True)       # 정렬되도록 통일
                .str.replace(r"^24시이후$", "24-", regex=True))
rl["인원"] = to_num(rl["인원"]).fillna(0).astype(int)
rl = rl.pivot_table(index=[R_DATE, R_LINE, R_NO, R_NAME, "시간대"], columns=R_TYPE,
                    values="인원", aggfunc="sum").reset_index()
rl.columns.name = None
rl = rl.rename(columns={"승차": "승차인원", "하차": "하차인원"})
for c in ("승차인원", "하차인원"):
    rl[c] = rl[c].fillna(0).astype(int)
rl = rl[rl[R_LINE].map(norm_line).isin(TARGET_LINES)]           # 1~8호선만
rl = attach_code(rl, R_LINE, R_NO, R_NAME, "ride")
save(rl[[M_CODE, R_LINE, R_NAME, R_DATE, "시간대", "승차인원", "하차인원"]], "ride_hourly_long.csv")

# 4. 빠른하차: 역코드 확인 ------------------------------------------------
print("[4] 빠른하차")
fast = read_any("fast_exit")
# stnCd / stnNo 중 역 기준표 코드와 더 많이 일치하는 쪽을 자동 선택
cands = [c for c in F_CODE_CANDIDATES if c in fast.columns]
scores = {c: fast[c].map(norm_no).isin(master["no"]).sum() for c in cands}
print(f"  코드 후보별 일치 건수: {scores}")
F_CODE = max(scores, key=scores.get)
print(f"  → '{F_CODE}' 사용")
fast = fast[fast[F_LINE].map(norm_line).isin(TARGET_LINES)].copy()   # 1~8호선만
fast = attach_code(fast, F_LINE, F_CODE, F_NAME, "fast_exit")
save(fast, "fast_exit_matched.csv")
fast["no"] = fast[F_CODE].map(norm_no)

# 5. 역 매칭표 -----------------------------------------------------------
print("[5] 역 매칭표")
master["in_congestion"] = master[M_CODE].isin(cl[M_CODE])
master["in_ride"] = master[M_CODE].isin(rl[M_CODE])
master["in_fast_exit"] = master[M_CODE].isin(fast[M_CODE])
# 역 기준표의 1~8호선에는 코레일 구간(예: 1호선 의정부, 4호선 과천)도 섞여 있으므로
# 세 데이터 중 하나 이상에 나오는 역(= 서울교통공사 운영 역)만 남긴다.
used = master[master[["in_congestion", "in_ride", "in_fast_exit"]].any(axis=1)]
print(f"  기준표 1~8호선 {len(master)}개 중 서울교통공사 데이터에 나오는 역 {len(used)}개")
for c in ("in_congestion", "in_ride", "in_fast_exit"):
    print(f"    {c}: {used[c].sum()}개")
save(used, "station_match.csv")
print("\nunmatched_*.csv에 남은 역은 manual_fix.csv(source,line,raw_name,station_cd)에 적고 다시 실행")
print("  source 값: congestion / ride / fast_exit")
