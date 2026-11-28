import pymysql

host = "localhost"
port = 3306
database = "subway_db"
username = "root"
password = ""  # 본인 MySQL root 비밀번호를 입력하세요


def get_connection():
    conn = pymysql.connect(
        host=host,
        user=username,
        password=password,
        database=database,
        port=port,
        charset="utf8mb4"
    )
    return conn
