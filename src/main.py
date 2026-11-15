import sys
from tabulate import tabulate
from db import get_connection


def select_line():
    num = input("\n[호선 선택] 1 ~ 8 사이의 숫자를 입력하세요 (예: 2 -> 2호선): ").strip()
    if num.endswith("호선"):
        return num
    return num + "호선"


def select_facility():
    print("\n[이동설비 선택]")
    print("  1. 엘리베이터 (기본값)")
    print("  2. 에스컬레이터")
    print("  3. 계단")
    choice = input("선택 (1/2/3, 엔터시 1): ").strip()
    if choice == "2":
        return "에스컬레이터"
    elif choice == "3":
        return "계단"
    else:
        return "엘리베이터"


def select_day_type():
    print("\n[요일 구분 선택]")
    print("  1. 평일 (기본값)")
    print("  2. 토요일")
    print("  3. 일요일")
    choice = input("선택 (1/2/3, 엔터시 1): ").strip()
    if choice == "2":
        return "토요일"
    elif choice == "3":
        return "일요일"
    else:
        return "평일"


# 1. 빠른하차 위치 안내
def query_fast_exit(conn):
    print("\n" + "=" * 60)
    print(" 1. 빠른하차 위치 안내")
    print("=" * 60)

    station_name = input("조회할 역명을 입력하세요 (예: 서울역, 한성대입구): ").strip()
    if not station_name:
        print("역명이 입력되지 않았습니다.")
        return

    line_name = select_line()
    facility = select_facility()

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n조회 결과가 없습니다. (입력값: {station_name}, {line_name}, {facility})")
        return

    print(f"\n[조회 결과: {len(rows)}건]\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


# 2. 시간대별 열차 혼잡도 조회 및 한산한 시간대 안내
def query_congestion(conn):
    print("\n" + "=" * 60)
    print(" 2. 시간대별 열차 혼잡도 조회 및 한산한 시간대 안내")
    print("=" * 60)

    station_name = input("조회할 역명을 입력하세요 (예: 서울역, 한성대입구): ").strip()
    if not station_name:
        print("역명이 입력되지 않았습니다.")
        return

    line_name = select_line()
    day_type = select_day_type()

    print("\n[운행방향 선택]")
    print("  1. 상행 / 내선 (기본값)")
    print("  2. 하행 / 외선")
    dir_choice = input("선택 (1/2, 엔터시 1): ").strip()
    if line_name == "2호선":
        if dir_choice == "2":
            direction = "외선"
        else:
            direction = "내선"
    else:
        if dir_choice == "2":
            direction = "하선"
        else:
            direction = "상선"

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n혼잡도 데이터가 없습니다. (입력값: {station_name}, {line_name}, {day_type}, {direction})")
        return

    print(f"\n[{station_name}역 {line_name} ({day_type} / {direction})] 30분 단위 혼잡도 (단위: %):\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))

    # 가장 한산한 시간과 가장 혼잡한 시간 찾기 (기본 for문 비교)
    min_row = rows[0]
    max_row = rows[0]
    for r in rows:
        if r[5] < min_row[5]:
            min_row = r
        if r[5] > max_row[5]:
            max_row = r

    print(f"\n- 최저 혼잡 시간대: {str(min_row[4])[:5]} ({min_row[5]}%)")
    print(f"- 최고 혼잡 시간대: {str(max_row[4])[:5]} ({max_row[5]}%)")


# 3. 노선 및 기간별 역 승하차 이용객 집계
def query_ridership(conn):
    print("\n" + "=" * 60)
    print(" 3. 노선 및 기간별 역 승하차 이용객 집계")
    print("=" * 60)

    line_name = select_line()
    start_date = input("조회 시작일자 (YYYY-MM-DD, 엔터시 2025-12-01): ").strip()
    if not start_date:
        start_date = "2025-12-01"

    end_date = input("조회 종료일자 (YYYY-MM-DD, 엔터시 2025-12-07): ").strip()
    if not end_date:
        end_date = "2025-12-07"

    limit_input = input("조회할 상위 역 개수 (엔터시 10개): ").strip()
    if limit_input.isdigit():
        limit = int(limit_input)
    else:
        limit = 10

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n조회 결과가 없습니다. (입력값: {line_name}, {start_date} ~ {end_date})")
        return

    print(f"\n[{line_name}] 이용객 집계 ({start_date} ~ {end_date}, 상위 {limit}개역):\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


# 4. 환승역 정보 조회
def query_transfer_station(conn):
    print("\n" + "=" * 60)
    print(" 4. 환승역 정보 조회")
    print("=" * 60)

    station_name = input("조회할 역명을 입력하세요 (예: 서울역, 동대문역사문화공원): ").strip()
    if not station_name:
        print("역명이 입력되지 않았습니다.")
        return

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n'{station_name}' 역 정보를 찾을 수 없습니다.")
        return

    print(f"\n[{station_name}역] 환승 정보:\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


# 5. 노선별 이동설비(엘리베이터) 설치 현황
def query_elevator_infra(conn):
    print("\n" + "=" * 60)
    print(" 5. 노선별 이동설비(엘리베이터) 설치 현황")
    print("=" * 60)

    line_name = select_line()

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n'{line_name}' 데이터를 찾을 수 없습니다.")
        return

    print(f"\n[{line_name}] 역별 엘리베이터 연결 현황:\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


# 6. 특정 시간대 노선 내 혼잡 역 순위
def query_rush_hour_congestion(conn):
    print("\n" + "=" * 60)
    print(" 6. 특정 시간대 노선 내 혼잡 역 순위")
    print("=" * 60)

    line_name = select_line()
    day_type = select_day_type()
    time_str = input("조회할 시간대를 입력하세요 (HH:MM 형식, 엔터시 08:30): ").strip()
    if not time_str:
        time_str = "08:30"
    
    if len(time_str) == 5:
        time_query = time_str + ":00"
    else:
        time_query = time_str

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

    cursor = conn.cursor()
    cursor.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print(f"\n해당 조건의 데이터가 없습니다. (입력값: {line_name}, {day_type}, {time_str})")
        return

    print(f"\n[{line_name} / {day_type} / {time_str}] 혼잡 역 순위 TOP 10 (단위: %):\n")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


def main():
    conn = get_connection()

    while True:
        print("\n" + "=" * 60)
        print(" 서울 지하철 하차 동선 및 이용 현황 조회 시스템")
        print("=" * 60)
        print(" 1. 빠른하차 위치 안내 (역명, 호선, 설비종류)")
        print(" 2. 시간대별 열차 혼잡도 조회 및 한산한 시간대 안내")
        print(" 3. 노선 및 기간별 역 승하차 이용객 집계")
        print(" 4. 환승역 정보 조회")
        print(" 5. 노선별 이동설비(엘리베이터) 설치 현황")
        print(" 6. 특정 시간대 노선 내 혼잡 역 순위")
        print(" 0. 프로그램 종료")
        print("=" * 60)
        choice = input("메뉴 번호를 선택하세요 (0~6): ").strip()

        if choice == "1":
            query_fast_exit(conn)
        elif choice == "2":
            query_congestion(conn)
        elif choice == "3":
            query_ridership(conn)
        elif choice == "4":
            query_transfer_station(conn)
        elif choice == "5":
            query_elevator_infra(conn)
        elif choice == "6":
            query_rush_hour_congestion(conn)
        elif choice == "0":
            print("\n프로그램을 종료합니다.")
            break
        else:
            print("\n올바른 번호(0~6)를 입력해주세요.")

    conn.close()


if __name__ == "__main__":
    main()
