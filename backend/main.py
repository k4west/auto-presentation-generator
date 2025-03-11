from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from backend.workflow import generate_presentation, feedback_queue
from backend.storage import FileManager
from backend.presentation_engine import MarpRenderer


app = FastAPI(title="Auto-Presentation Generator 🚀")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")


file_manager = FileManager()
renderer = MarpRenderer()

class UserInput(BaseModel):
    message: str
    topic: str
    style: str

class FeedbackInput(BaseModel):
    feedback: str

@app.get("/", response_class=HTMLResponse)
async def serve_html(request: Request):
    """
    테스트용 HTML 페이지 제공
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate_presentation/{thread_id}")
async def create_presentation(user_input: UserInput, thread_id: str):
    """프레젠테이션 생성 요청"""
    try:
        print(f"📩 Received JSON Request: {user_input.model_dump()}")  # ✅ FastAPI 로그 출력

        presentation = await generate_presentation(user_input.model_dump(), thread_id)
        file_path = 'test' # file_manager.save_presentation(thread_id, presentation)

        return {"presentation": presentation, "file_path": file_path}
    except Exception as e:
        print(f"🔥 Error: {e}")  # ✅ FastAPI 터미널에서 오류 로그 확인
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/feedback/{thread_id}")
async def receive_feedback(thread_id: str, feedback: FeedbackInput):
    """사용자의 피드백을 받아 LangGraph에 전달"""
    await feedback_queue.put(feedback.feedback)  # ✅ 비동기 큐 사용
    print(f"📩 Feedback received for thread {thread_id}: {feedback.feedback}")
    return {"status": "received", "thread_id": thread_id, "feedback": feedback.feedback}
