import os
import sys
import pandas as pd

# src 폴더의 db.py 연결 함수 사용
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from db import get_connection

CLEAN_DIR = os.path.join(os.path.dirname(__file__), "data")


def norm_line_name(line_str):
    s = str(line_str).strip()
    if s.endswith("호선"):
        num = s.replace("호선", "").lstrip("0")
        return num + "호선"
    return s.lstrip("0") + "호선"


def main():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 기존 데이터 초기화 (자식 테이블부터 순서대로 삭제)
        for table in ["RIDERSHIP", "CONGESTION", "FAST_EXIT", "FACILITY_TYPE", "LINE_STATION", "STATION", "LINE"]:
            cursor.execute(f"DELETE FROM {table};")
        conn.commit()

        # 1. LINE 테이블 적재
        match_df = pd.read_csv(os.path.join(CLEAN_DIR, "station_match.csv"), dtype=str)
        line_records = []
        for line_num in sorted(match_df["LINE_NUM"].unique()):
            line_name = norm_line_name(line_num)
            line_records.append((line_num, line_name))

        cursor.executemany(
            "INSERT INTO LINE (line_code, line_name) VALUES (%s, %s);",
            line_records
        )
        conn.commit()

        # 2. STATION 테이블 적재
        distinct_names = sorted(match_df["STATION_NM"].unique())
        station_records = [(name,) for name in distinct_names]
        cursor.executemany(
            "INSERT INTO STATION (station_name) VALUES (%s);",
            station_records
        )
        conn.commit()

        cursor.execute("SELECT station_id, station_name FROM STATION;")
        station_map = {name: sid for sid, name in cursor.fetchall()}

        # 3. LINE_STATION 테이블 적재
        line_station_records = []
        for _, row in match_df.iterrows():
            stn_cd = str(row["STATION_CD"]).zfill(4)
            stn_nm = row["STATION_NM"]
            stn_id = station_map[stn_nm]
            line_code = row["LINE_NUM"]
            ext_code = row["FR_CODE"] if pd.notna(row["FR_CODE"]) else None
            line_station_records.append((stn_cd, stn_id, line_code, stn_nm, ext_code))

        cursor.executemany(
            """INSERT INTO LINE_STATION (station_cd, station_id, line_code, source_station_name, external_code)
               VALUES (%s, %s, %s, %s, %s);""",
            line_station_records
        )
        conn.commit()

        # 4. FACILITY_TYPE 테이블 적재
        facility_types = ["계단", "엘리베이터", "에스컬레이터"]
        cursor.executemany(
            "INSERT INTO FACILITY_TYPE (facility_type_name) VALUES (%s);",
            [(f,) for f in facility_types]
        )
        conn.commit()

        cursor.execute("SELECT facility_type_id, facility_type_name FROM FACILITY_TYPE;")
        facility_map = {name: fid for fid, name in cursor.fetchall()}

        # 5. FAST_EXIT 테이블 적재
        fast_df = pd.read_csv(os.path.join(CLEAN_DIR, "fast_exit_matched.csv"), dtype=str)
        fast_records = []
        for _, row in fast_df.iterrows():
            mng_no = str(row["qckgffMngNo"])
            stn_cd = str(row["STATION_CD"]).zfill(4)
            fac_name = row["plfmCmgFac"]
            fac_id = facility_map.get(fac_name)
            ref_date = row["crtrYmd"] if pd.notna(row["crtrYmd"]) else None
            direction = row["upbdnbSe"] if pd.notna(row["upbdnbSe"]) else None
            dest_info = row["drtnInfo"] if pd.notna(row["drtnInfo"]) else None
            door_no = row["qckgffVhclDoorNo"] if pd.notna(row["qckgffVhclDoorNo"]) else ""
            fac_no = row["facNo"] if pd.notna(row["facNo"]) else None
            elv_no = row["elvtrNo"] if pd.notna(row["elvtrNo"]) else None
            loc_nm = row["fwkPstnNm"] if pd.notna(row["fwkPstnNm"]) else None
            fac_loc = row["facPstnNm"] if pd.notna(row["facPstnNm"]) else None

            fast_records.append((
                mng_no, stn_cd, fac_id, ref_date, direction, dest_info,
                door_no, fac_no, elv_no, loc_nm, fac_loc
            ))

        cursor.executemany(
            """INSERT INTO FAST_EXIT (
                management_no, station_cd, facility_type_id, reference_date, direction,
                destination_info, car_door_no, facility_no, elevator_no, location_name, facility_location
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            fast_records
        )
        conn.commit()

        # 6. CONGESTION 테이블 적재
        cng_path = os.path.join(CLEAN_DIR, "congestion_clean.csv")
        cng_df = pd.read_csv(cng_path, dtype={"STATION_CD": str, "혼잡도": float})
        
        cng_records = []
        for _, row in cng_df.iterrows():
            stn_cd = str(row["STATION_CD"]).zfill(4)
            day_type = row["요일구분"]
            direction = row["상하구분"]
            time_str = str(row["시간대"]).strip()
            if len(time_str) == 5:
                time_str += ":00"
            rate = float(row["혼잡도"])
            cng_records.append((stn_cd, day_type, direction, time_str, rate))

        # 5,000건 단위 분할 적재
        batch_size = 5000
        for i in range(0, len(cng_records), batch_size):
            batch = cng_records[i:i + batch_size]
            cursor.executemany(
                """INSERT INTO CONGESTION (station_cd, day_type, direction, time_start, congestion_rate)
                   VALUES (%s, %s, %s, %s, %s);""",
                batch
            )
            conn.commit()

        # 7. RIDERSHIP 테이블 적재
        ride_path = os.path.join(CLEAN_DIR, "ride_hourly_long.csv")
        ride_df = pd.read_csv(ride_path, dtype={"STATION_CD": str, "승차인원": int, "하차인원": int})

        ride_records = []
        for _, row in ride_df.iterrows():
            stn_cd = str(row["STATION_CD"]).zfill(4)
            t_date = row["수송일자"]
            t_slot = row["시간대"]
            b_cnt = int(row["승차인원"])
            a_cnt = int(row["하차인원"])
            ride_records.append((stn_cd, t_date, t_slot, b_cnt, a_cnt))

        # 10,000건 단위 분할 적재
        batch_size = 10000
        for i in range(0, len(ride_records), batch_size):
            batch = ride_records[i:i + batch_size]
            cursor.executemany(
                """INSERT INTO RIDERSHIP (station_cd, transport_date, time_slot, boarding_count, alighting_count)
                   VALUES (%s, %s, %s, %s, %s);""",
                batch
            )
            conn.commit()

        print("데이터 적재 완료")

    except Exception as e:
        conn.rollback()
        print(f"적재 중 오류: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
