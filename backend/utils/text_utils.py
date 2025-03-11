import json

def clean_text(text: str) -> str:
    """텍스트 전처리 (예: 개행 제거)"""
    return text.strip()

def to_json(data) -> str:
    """데이터를 JSON 형식으로 변환"""
    return json.dumps(data, ensure_ascii=False, indent=2)
