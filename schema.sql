CREATE DATABASE IF NOT EXISTS subway_db;
USE subway_db;

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

-- 3. LINE_STATION (노선별 역 테이블)
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
