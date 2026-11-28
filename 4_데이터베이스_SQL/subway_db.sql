-- =====================================================================
-- 서울 지하철 하차 동선 및 이용 현황 데이터베이스 (subway_db.sql)
-- 1번: 데이터베이스 및 7개 테이블 생성 (DDL)
-- 2번: 조회 질의문 (DML)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS subway_db;
USE subway_db;

-- ---------------------------------------------------------------------
-- 1번: 테이블 초기화 및 생성 (DDL)
-- ---------------------------------------------------------------------

DROP TABLE IF EXISTS RIDERSHIP;
DROP TABLE IF EXISTS CONGESTION;
DROP TABLE IF EXISTS FAST_EXIT;
DROP TABLE IF EXISTS FACILITY_TYPE;
DROP TABLE IF EXISTS LINE_STATION;
DROP TABLE IF EXISTS STATION;
DROP TABLE IF EXISTS LINE;

-- 1. LINE (호선 테이블)
CREATE TABLE LINE (
    line_code VARCHAR(10) NOT NULL,
    line_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (line_code)
);

-- 2. STATION (역 테이블)
CREATE TABLE STATION (
    station_id BIGINT AUTO_INCREMENT NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (station_id)
);

-- 3. LINE_STATION (노선별 역 테이블 - 환승역 교차 릴레이션)
CREATE TABLE LINE_STATION (
    station_cd CHAR(4) NOT NULL,
    station_id BIGINT NOT NULL,
    line_code VARCHAR(10) NOT NULL,
    source_station_name VARCHAR(100) NOT NULL,
    external_code VARCHAR(20),
    PRIMARY KEY (station_cd),
    FOREIGN KEY (station_id) REFERENCES STATION (station_id),
    FOREIGN KEY (line_code) REFERENCES LINE (line_code)
);

-- 4. FACILITY_TYPE (이동설비 유형 테이블)
CREATE TABLE FACILITY_TYPE (
    facility_type_id BIGINT AUTO_INCREMENT NOT NULL,
    facility_type_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (facility_type_id)
);

-- 5. FAST_EXIT (빠른하차 정보 테이블)
CREATE TABLE FAST_EXIT (
    management_no VARCHAR(50) NOT NULL,
    station_cd CHAR(4) NOT NULL,
    facility_type_id BIGINT NOT NULL,
    reference_date DATE,
    direction VARCHAR(20),
    destination_info VARCHAR(100),
    car_door_no VARCHAR(20) NOT NULL,
    facility_no VARCHAR(50),
    elevator_no VARCHAR(50),
    location_name VARCHAR(100),
    facility_location VARCHAR(255),
    PRIMARY KEY (management_no),
    FOREIGN KEY (station_cd) REFERENCES LINE_STATION (station_cd),
    FOREIGN KEY (facility_type_id) REFERENCES FACILITY_TYPE (facility_type_id)
);

-- 6. CONGESTION (혼잡도 정보 테이블)
CREATE TABLE CONGESTION (
    congestion_id BIGINT AUTO_INCREMENT NOT NULL,
    station_cd CHAR(4) NOT NULL,
    day_type VARCHAR(20) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    time_start TIME NOT NULL,
    congestion_rate DECIMAL(5, 2) NOT NULL,
    PRIMARY KEY (congestion_id),
    FOREIGN KEY (station_cd) REFERENCES LINE_STATION (station_cd)
);

-- 7. RIDERSHIP (시간대별 승하차 인원 테이블)
CREATE TABLE RIDERSHIP (
    station_cd CHAR(4) NOT NULL,
    transport_date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    boarding_count INT NOT NULL,
    alighting_count INT NOT NULL,
    PRIMARY KEY (station_cd, transport_date, time_slot),
    FOREIGN KEY (station_cd) REFERENCES LINE_STATION (station_cd)
);


-- ---------------------------------------------------------------------
-- 2번: 조회 질의문 (DML)
-- ---------------------------------------------------------------------

-- 1. 빠른하차 위치 안내 (조건: 역명, 호선, 설비종류)
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


-- 2. 시간대별 혼잡도 조회 (조건: 역명, 호선, 요일, 운행방향)
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
WHERE s.station_name = '한성대입구'
  AND l.line_name = '4호선'
  AND c.day_type = '평일'
  AND c.direction = '상선'
ORDER BY c.time_start ASC;


-- 3. 노선 및 기간별 역 승하차 이용객 집계 (조건: 호선, 기간)
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
WHERE l.line_name = '2호선'
  AND r.transport_date BETWEEN '2025-12-01' AND '2025-12-07'
GROUP BY s.station_id, s.station_name, l.line_name
ORDER BY SUM(r.boarding_count + r.alighting_count) DESC
LIMIT 10;


-- 4. 환승역 정보 조회 (조건: 역명)
SELECT 
    s.station_name AS '역명',
    l.line_name AS '경유 호선',
    ls.station_cd AS '전철역코드'
FROM STATION s
JOIN LINE_STATION ls ON s.station_id = ls.station_id
JOIN LINE l ON ls.line_code = l.line_code
WHERE s.station_name = '서울역'
ORDER BY l.line_name;


-- 5. 노선별 이동설비(엘리베이터) 설치 현황 (조건: 호선)
SELECT 
    s.station_name AS '역명',
    l.line_name AS '호선',
    COUNT(fe.management_no) AS '엘리베이터 설치 칸 수'
FROM LINE_STATION ls
JOIN STATION s ON ls.station_id = s.station_id
JOIN LINE l ON ls.line_code = l.line_code
JOIN FAST_EXIT fe ON ls.station_cd = fe.station_cd
JOIN FACILITY_TYPE ft ON fe.facility_type_id = ft.facility_type_id
WHERE l.line_name = '4호선'
  AND ft.facility_type_name = '엘리베이터'
GROUP BY s.station_id, s.station_name, l.line_name
ORDER BY COUNT(fe.management_no) DESC;


-- 6. 특정 시간대 노선 내 혼잡 역 순위 (조건: 호선, 요일, 시간대)
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
WHERE l.line_name = '2호선'
  AND c.day_type = '평일'
  AND c.time_start = '08:30:00'
ORDER BY c.congestion_rate DESC
LIMIT 10;
