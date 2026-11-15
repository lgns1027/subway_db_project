# 서울 지하철 하차 동선 및 이용 현황 조회 시스템 

서울교통공사 1~8호선 공개 데이터를 기반으로 구축한 MySQL 관계형 데이터베이스와 연동하여, 하차 칸 및 이동설비 위치 안내, 혼잡도 분석, 승하차 이용객 집계 등의 조회를 수행하는 콘솔 응용프로그램입니다.

---

## 1. 실행 환경

- **OS**: Windows 10/11
- **DBMS**: MySQL Server 8.0 (포트: 3306)
- **Python**: Python 3.8 이상
- **필수 패키지**: `pymysql`, `tabulate`, `pandas`, `openpyxl`

---

## 2. 디렉터리 구조

```text
📁 subway_db_project/
├── 📄 process.md               # 데이터 정제 및 스키마 매핑 작업 일지
├── 📄 schema.sql               # 데이터베이스 7개 테이블 DDL
├── 📄 queries.sql              # 핵심 조회 SQL 쿼리 모음
├── 📄 load_data.py             # CSV 데이터 MySQL 적재 스크립트
├── 📄 erd1.png / erd2.png      # ER 다이어그램 및 테이블 스키마 다이어그램
├── 📁 docs/                    # 세부 보고서 모음
├── 📁 src/
│   ├── db.py                   # MySQL 커넥션 연결 모듈
│   └── main.py                 # 대화형 조회 응용프로그램 메인
└── 📁 데이터 전처리/            # 원본 및 정제 데이터
```

---

## 3. 데이터베이스 구축 및 실행

### 1) 패키지 설치
```bash
pip install pymysql tabulate pandas openpyxl
```

### 2) 데이터베이스 구축
```bash
# 1. 테이블 생성
mysql -u root -p0000 < schema.sql

# 2. 데이터 적재
python load_data.py
```

---

## 4. 응용프로그램 실행

```bash
python src/main.py
```

### 기능 목록
1. **빠른하차 위치 안내**: 역명, 호선, 설비 종류를 입력하여 최적 하차 칸-문 및 시설 위치 조회
2. **시간대별 열차 혼잡도 조회**: 역명, 호선, 요일, 방향별 30분 단위 혼잡도 및 최저 혼잡 시간대 안내
3. **노선 및 기간별 역 승하차 이용객 집계**: 호선 및 기간별 역 승하차 총합 및 이용객 순위 집계
4. **환승역 정보 조회**: 역명 입력 시 경유하는 모든 노선 목록 및 역코드 조회
5. **노선별 이동설비(엘리베이터) 설치 현황**: 노선별 역당 엘리베이터 연결 칸 수 및 미설치 역 조회
6. **특정 시간대 노선 내 혼잡 역 순위**: 호선, 요일, 시간대별 혼잡도 상위 역 순위 조회
0. **프로그램 종료**

---

## 5. DB 접속 설정 변경
MySQL 접속 계정 또는 비밀번호가 다를 경우 `src/db.py` 파일의 `DB_CONFIG`를 수정합니다:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "본인_비밀번호",
    "database": "subway_db",
    "charset": "utf8mb4"
}
```
