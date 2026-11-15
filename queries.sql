-- =====================================================================
-- 지하철 하차 동선 및 이용 현황 핵심 조회 쿼리 (queries.sql)
-- =====================================================================

USE subway_db;

-- ---------------------------------------------------------------------
-- 1. 빠른하차 위치 안내
-- 조건: 역명, 호선, 이동설비 종류
-- ---------------------------------------------------------------------
SELECT 
    s.station_name AS '역명',
    l.line_name AS '호선',
    ft.facility_type_name AS '이동설비',
    fe.direction AS '운행방향',
    fe.destination_info AS '방면',
    fe.car_door_no AS '하차 칸-문',
    fe.location_name AS '시설 위치명',
    fe.facility_location AS '상세 위치 설명'
FROM FAST_EXIT fe
JOIN LINE_STATION ls ON fe.station_cd = ls.station_cd
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
JOIN FACILITY_TYPE ft ON fe.facility_type_id = ft.facility_type_id
WHERE s.station_name = '서울역'
  AND l.line_name = '1호선'
  AND ft.facility_type_name = '엘리베이터'
ORDER BY fe.direction, fe.car_door_no;


-- ---------------------------------------------------------------------
-- 2. 시간대별 혼잡도 조회
-- 조건: 역명, 호선, 요일, 운행방향
-- ---------------------------------------------------------------------
SELECT 
    s.station_name AS '역명',
    l.line_name AS '호선',
    c.day_type AS '요일',
    c.direction AS '방향',
    TIME_FORMAT(c.time_start, '%H:%i') AS '시간대',
    c.congestion_rate AS '혼잡도(%)'
FROM CONGESTION c
JOIN LINE_STATION ls ON c.station_cd = ls.station_cd
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
WHERE s.station_name = '강남'
  AND l.line_name = '2호선'
  AND c.day_type = '평일'
  AND c.direction = '내선'
ORDER BY c.time_start ASC;


-- ---------------------------------------------------------------------
-- 3. 노선 및 기간별 역 승하차 이용객 집계
-- 조건: 호선, 기간(수송일자 범위)
-- ---------------------------------------------------------------------
SELECT 
    DENSE_RANK() OVER (ORDER BY SUM(r.boarding_count + r.alighting_count) DESC) AS '순위',
    s.station_name AS '역명',
    l.line_name AS '호선',
    FORMAT(SUM(r.boarding_count), 0) AS '총 승차인원',
    FORMAT(SUM(r.alighting_count), 0) AS '총 하차인원',
    FORMAT(SUM(r.boarding_count + r.alighting_count), 0) AS '총 이용객 합계'
FROM RIDERSHIP r
JOIN LINE_STATION ls ON r.station_cd = ls.station_cd
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
WHERE l.line_name = '2호선'
  AND r.transport_date BETWEEN '2025-12-01' AND '2025-12-07'
GROUP BY s.station_id, s.station_name, l.line_name
ORDER BY SUM(r.boarding_count + r.alighting_count) DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 4. 환승역 정보 조회
-- 조건: 역명
-- ---------------------------------------------------------------------
SELECT 
    s.station_name AS '역명',
    COUNT(ls.line_code) AS '경유 노선 수',
    GROUP_CONCAT(l.line_name ORDER BY l.line_name SEPARATOR ', ') AS '경유 노선 목록',
    GROUP_CONCAT(CONCAT(l.line_name, '(', ls.station_cd, ')') ORDER BY l.line_name SEPARATOR ', ') AS '노선별 전철역코드'
FROM STATION s
JOIN LINE_STATION ls ON s.station_id = ls.station_id
JOIN LINE l ON ls.line_code = l.line_code
WHERE s.station_name = '동대문역사문화공원'
GROUP BY s.station_id, s.station_name;


-- ---------------------------------------------------------------------
-- 5. 노선별 이동설비(엘리베이터) 설치 현황
-- 조건: 호선
-- ---------------------------------------------------------------------
SELECT 
    s.station_name AS '역명',
    l.line_name AS '호선',
    COUNT(CASE WHEN ft.facility_type_name = '엘리베이터' THEN fe.management_no END) AS '엘리베이터 연결 칸 수'
FROM LINE_STATION ls
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
LEFT JOIN FAST_EXIT fe ON ls.station_cd = fe.station_cd
LEFT JOIN FACILITY_TYPE ft ON fe.facility_type_id = ft.facility_type_id
WHERE l.line_name = '7호선'
GROUP BY s.station_id, s.station_name, l.line_name
ORDER BY `엘리베이터 연결 칸 수` ASC, s.station_name ASC;


-- ---------------------------------------------------------------------
-- 6. 특정 시간대 노선 내 혼잡 역 순위
-- 조건: 호선, 요일, 시간대
-- ---------------------------------------------------------------------
SELECT 
    DENSE_RANK() OVER (ORDER BY c.congestion_rate DESC) AS '혼잡 순위',
    s.station_name AS '역명',
    l.line_name AS '호선',
    c.direction AS '운행방향',
    TIME_FORMAT(c.time_start, '%H:%i') AS '시간대',
    c.congestion_rate AS '혼잡도(%)'
FROM CONGESTION c
JOIN LINE_STATION ls ON c.station_cd = ls.station_cd
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
WHERE l.line_name = '2호선'
  AND c.day_type = '평일'
  AND c.time_start = '08:30:00'
ORDER BY c.congestion_rate DESC
LIMIT 10;
