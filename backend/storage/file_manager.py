import os, requests
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


class FileManager:
    """파일 저장 및 관리"""

    def __init__(self, base_dir="storage/images"):
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]

    def save_image(self, image_url: str, thread_id: str) -> str:
        """이미지 URL을 다운로드하고 로컬에 저장"""
        response = requests.get(image_url)
        if response.status_code == 200:
            file_path = os.path.join(self.base_dir, f"{thread_id}.png")
            with open(file_path, "wb") as img_file:
                img_file.write(response.content)
            return file_path
        return ""
    
    def save_presentation(self, thread_id: str, presentation: str):
        """프레젠테이션 저장 (MongoDB + 파일)"""
        timestamp = datetime.now()
        self.collection.insert_one({"thread_id": thread_id, "content": presentation, "timestamp": timestamp})

        # 파일 저장 (Markdown)
        os.makedirs(f"presentations/{thread_id}", exist_ok=True)
        file_path = f"presentations/{thread_id}/presentation_{timestamp}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(presentation)
        
        return file_path
