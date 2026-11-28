import sys
import os
from flask import Flask, render_template, request

# src 폴더의 db.py를 임포트하기 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from db import get_connection

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    menu = request.args.get("menu", "1")
    headers = []
    rows = []
    message = None
    least_time = None
    most_time = None

    if request.method == "POST":
        menu = request.form.get("menu", "1")
        conn = get_connection()
        cursor = conn.cursor()

        # 1. 빠른하차 위치 안내
        if menu == "1":
            station_name = request.form.get("station_name", "").strip()
            line_name = request.form.get("line_name", "1호선")
            facility = request.form.get("facility", "엘리베이터")

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '호선',
                ft.facility_type_name AS '이동설비',
                fe.direction AS '운행방향',
                fe.destination_info AS '방면',
                fe.car_door_no AS '하차 칸-문',
                fe.location_name AS '설비 위치명',
                fe.facility_location AS '상세 위치 설명'
            FROM FAST_EXIT fe
            JOIN LINE_STATION ls ON fe.station_cd = ls.station_cd
            JOIN STATION s ON ls.station_id = s.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            JOIN FACILITY_TYPE ft ON fe.facility_type_id = ft.facility_type_id
            WHERE s.station_name = '{station_name}'
              AND l.line_name = '{line_name}'
              AND ft.facility_type_name = '{facility}'
            ORDER BY fe.direction, fe.car_door_no;
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # 2. 시간대별 혼잡도 조회
        elif menu == "2":
            station_name = request.form.get("station_name", "").strip()
            line_name = request.form.get("line_name", "1호선")
            day_type = request.form.get("day_type", "평일")
            direction = request.form.get("direction", "상선")

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '호선',
                c.day_type AS '요일',
                c.direction AS '방향',
                c.time_start AS '시간대',
                c.congestion_rate AS '혼잡도'
            FROM CONGESTION c
            JOIN LINE_STATION ls ON c.station_cd = ls.station_cd
            JOIN STATION s ON ls.station_id = s.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            WHERE s.station_name = '{station_name}'
              AND l.line_name = '{line_name}'
              AND c.day_type = '{day_type}'
              AND c.direction = '{direction}'
            ORDER BY c.time_start ASC;
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            if rows:
                min_row = rows[0]
                max_row = rows[0]
                for r in rows:
                    if r[5] < min_row[5]:
                        min_row = r
                    if r[5] > max_row[5]:
                        max_row = r
                least_time = f"{str(min_row[4])[:5]} ({min_row[5]}%)"
                most_time = f"{str(max_row[4])[:5]} ({max_row[5]}%)"

        # 3. 승하차 이용객 집계
        elif menu == "3":
            line_name = request.form.get("line_name", "2호선")
            start_date = request.form.get("start_date", "2025-12-01").strip() or "2025-12-01"
            end_date = request.form.get("end_date", "2025-12-07").strip() or "2025-12-07"
            limit = request.form.get("limit", "10").strip() or "10"

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '호선',
                SUM(r.boarding_count) AS '총 승차인원',
                SUM(r.alighting_count) AS '총 하차인원',
                SUM(r.boarding_count + r.alighting_count) AS '총 이용객 합계'
            FROM RIDERSHIP r
            JOIN LINE_STATION ls ON r.station_cd = ls.station_cd
            JOIN STATION s ON ls.station_id = s.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            WHERE l.line_name = '{line_name}'
              AND r.transport_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY s.station_id, s.station_name, l.line_name
            ORDER BY SUM(r.boarding_count + r.alighting_count) DESC
            LIMIT {limit};
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # 4. 환승역 정보 조회
        elif menu == "4":
            station_name = request.form.get("station_name", "").strip()

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '경유 호선',
                ls.station_cd AS '전철역코드'
            FROM STATION s
            JOIN LINE_STATION ls ON s.station_id = ls.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            WHERE s.station_name = '{station_name}'
            ORDER BY l.line_name;
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # 5. 엘리베이터 설치 현황
        elif menu == "5":
            line_name = request.form.get("line_name", "7호선")

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '호선',
                COUNT(fe.management_no) AS '엘리베이터 설치 칸 수'
            FROM LINE_STATION ls
            JOIN STATION s ON ls.station_id = s.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            JOIN FAST_EXIT fe ON ls.station_cd = fe.station_cd
            JOIN FACILITY_TYPE ft ON fe.facility_type_id = ft.facility_type_id
            WHERE l.line_name = '{line_name}'
              AND ft.facility_type_name = '엘리베이터'
            GROUP BY s.station_id, s.station_name, l.line_name
            ORDER BY COUNT(fe.management_no) DESC;
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # 6. 혼잡 역 순위
        elif menu == "6":
            line_name = request.form.get("line_name", "2호선")
            day_type = request.form.get("day_type", "평일")
            time_query = request.form.get("time_str", "08:30:00").strip()
            if len(time_query) == 5:
                time_query += ":00"

            sql = f"""
            SELECT 
                s.station_name AS '역명',
                l.line_name AS '호선',
                c.direction AS '운행방향',
                c.time_start AS '시간대',
                c.congestion_rate AS '혼잡도'
            FROM CONGESTION c
            JOIN LINE_STATION ls ON c.station_cd = ls.station_cd
            JOIN STATION s ON ls.station_id = s.station_id
            JOIN LINE l ON ls.line_code = l.line_code
            WHERE l.line_name = '{line_name}'
              AND c.day_type = '{day_type}'
              AND c.time_start = '{time_query}'
            ORDER BY c.congestion_rate DESC
            LIMIT 10;
            """
            cursor.execute(sql)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if not rows:
            message = "조회 조건에 일치하는 결과가 없습니다."

    return render_template(
        "index.html",
        menu=menu,
        headers=headers,
        rows=rows,
        message=message,
        least_time=least_time,
        most_time=most_time
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
