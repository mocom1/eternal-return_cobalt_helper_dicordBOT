import json
import os

DB_FILE = "cobalt_db.json"

def load_db():
    # 만약 컴퓨터에 'cobalt_db.json' 파일이 없다면?
    if not os.path.exists(DB_FILE):
        # 텅 빈 장부 파일({})을 새로 만들어라!
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return {}  # 빈 장부 데이터 리턴
    
    # 이미 장부 파일이 존재한다면, 열어서 내용을 읽어와라!
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_db(data):
    """변경된 데이터베이스 상태를 파일에 최종 세이브(저장)합니다."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



