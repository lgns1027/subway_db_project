# 서울 지하철 하차 동선 및 이용 현황 조회 시스템

서울교통공사 1~8호선 데이터를 기반으로 구축한 MySQL 데이터베이스 연동 조회 응용프로그램입니다.

---

## 1. 실행 환경

- **OS**: Windows 10 / 11
- **DBMS**: MySQL Server 8.0 (포트: 3306)
- **Python**: Python 3.8 이상
- **사용 라이브러리**: `pymysql`, `tabulate`, `pandas`, `openpyxl`, `flask`

---

## 2. 디렉터리 및 파일 구조

```text
📁 subway_db_project/
├── 📁 report/
│   └── 📄 데이터베이스[B] 4조 프로젝트 결과보고서.docx   # 결과보고서
│
├── 📁 presentation/                                      # 발표 자료
│
├── 📁 source/
│   ├── 📄 app.py                                         # Flask 웹 조회 프로그램
│   ├── 📁 templates/
│   │   └── 📄 index.html                                 # 웹 UI 화면
│   ├── 📁 src/
│   │   ├── 📄 main.py                                    # 터미널 조회 프로그램
│   │   └── 📄 db.py                                      # MySQL 연결 설정
│   ├── 📄 load_data.py                                   # CSV 데이터 적재 스크립트
│   └── 📁 data/                                          # 전처리 CSV 파일
│
├── 📁 sql/
│   ├── 📄 subway_db_data.sql                             # 테이블 구조 및 데이터 복원 SQL
│   └── 📄 subway_db.sql                                  # 테이블 생성 및 조회 질의문
│
└── 📄 README.md                                          # 실행 안내서
```

---

## 3. 설치 및 데이터베이스 복원

### 1단계: 라이브러리 설치
```bash
pip install pymysql tabulate pandas openpyxl flask
```

### 2단계: 데이터베이스 복원
명령 프롬프트에서 아래 명령어를 실행하여 데이터베이스(`subway_db`), 7개 테이블, 데이터를 복원합니다.
```bash
mysql -u root -p < sql/subway_db_data.sql
```
또는 MySQL Workbench에서 `sql/subway_db_data.sql` 파일을 열어 실행합니다.

테이블 생성 후 CSV 파일로 직접 적재할 경우 `sql/subway_db.sql`의 테이블 생성문을 실행한 뒤 아래 명령어를 실행합니다.
```bash
cd source
python load_data.py
```

### 3단계: MySQL 연결 설정
`source/src/db.py` 파일을 열어 MySQL 접속 정보를 입력합니다.

```python
# source/src/db.py
host = "localhost"
port = 3306
database = "subway_db"
username = "root"
password = "MySQL_비밀번호"
```

---

## 4. 응용프로그램 실행

`source` 폴더로 이동하여 실행합니다.

### 방법 1. 웹 브라우저 실행
```bash
cd source
python app.py
```
1. 웹 서버 실행 후 브라우저에서 `http://localhost:5000` 주소로 접속합니다.
2. 상단 메뉴(1~6번)를 선택하고 조건을 입력한 뒤 **[조회하기]**를 클릭합니다.

### 방법 2. 터미널 실행
```bash
cd source
python src/main.py
```
1. 메뉴 번호(1~6)를 선택합니다.
2. 역명, 호선 등 조건을 입력하면 결과가 출력됩니다.
3. `0`을 입력하면 종료됩니다.

---

## 5. 조회 기능 목록

1. **빠른하차 위치 안내**: 역명, 호선, 설비 종류를 지정하여 하차 칸-문 번호 및 설비 위치 조회
2. **시간대별 열차 혼잡도 조회**: 역명, 호선, 요일, 운행방향별 30분 단위 혼잡도 및 최저/최고 혼잡 시간대 조회
3. **노선 및 기간별 역 승하차 이용객 집계**: 호선 및 날짜 범위를 지정하여 역별 승차/하차 합계 및 이용객 순위 집계
4. **환승역 정보 조회**: 역명 입력 시 경유 노선 목록 및 전철역코드 조회
5. **노선별 이동설비 설치 현황**: 노선 내 역별 엘리베이터 연결 하차 위치 수 집계
6. **특정 시간대 노선 내 혼잡 역 순위**: 호선, 요일, 시간대를 지정하여 혼잡도 상위 10개 역 순위 조회
