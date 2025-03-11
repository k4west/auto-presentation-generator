# agents.py

import json
from dotenv import load_dotenv
from typing import List
from pydantic import ValidationError
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from .graph_state import OutlineModel, SlideContentModel, FinalMarpModel

# ✅ 환경 변수 로드
load_dotenv()

# ✅ LLM 기본 설정 (ChatOpenAI / OpenAI)
# JSON 형식 LLM (코드 블록 / 설명 없이 "json_object"만 반환)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_json = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}}
)
openai_llm = OpenAI(model="gpt-4o-mini", temperature=0)

# ✅ DALL·E API 설정 (이미지 생성용)
dalle = DallEAPIWrapper(model="dall-e-3", size="1024x1024", quality="standard", n=1)


# 🟢 개요들(OutlineModel 리스트)을 JSON으로 반환
def generate_outline(topic: str, style: str, last_msg: str) -> List[OutlineModel]:
    """
    개요들(OutlineModel 리스트)을 JSON으로 반환.
    마지막 메시지(last_msg)를 추가 문맥으로 고려.
    """
    prompt = f"""Return a JSON array of outline items for a {style} style presentation on '{topic}'.
The user has an additional message or context: '{last_msg}'

return type: arrayed objects
{{
    title (string):  "Outline Title"
    content (string):  "Actual text (markdown/HTML)"
    images (int):  "Number of images per outline"
    image_positions (list[string]):  "Positions where images will appear"
    pages (int):  "Number of pages if content is large"
}}
Do not include extra keys. No code blocks. JSON only.
"""

    resp = llm_json.invoke(prompt).content
    try:
        data = json.loads(resp)
        if isinstance(data, dict):
            data = data[[*data.keys()][0]]
        # print(data)
        return data
        outlines = []
        for item in data:
            outlines.append(OutlineModel(**item))
        return outlines
    except (json.JSONDecodeError, ValidationError):
        return []


# 🟢 개요 관련성 검사 Agent
def check_relevance(outline: str, topic: str) -> bool:
    """개요가 주제와 관련이 있는지 평가"""
    prompt = (
        f"Does the following outline accurately match the topic '{topic}'? "
        f"Respond with 'Yes' if relevant and 'No' if not.\n\nOutline:\n{outline}"
    )
    response = llm.invoke(prompt).content
    return "yes" in response.lower()

# 🟢 개요 확장 Agent
def refine_outline(outline: str) -> str:
    """기존 개요를 더 세부적으로 확장"""
    prompt = f"Expand and enrich this `content` for a presentation with more details.\nReturn only the content, without any other explanation.\ncontent:{outline}"
    return llm.invoke(prompt).content

# 🟢 슬라이드 분할 Agent (OutlineModel → list[str])
def split_outline_to_slides(outline_item: OutlineModel) -> List[str]:
    """
    pages 수에 맞춰 슬라이드를 분할 (간단 예시).
    내용이 길면 LLM에 맡겨도 되지만, 여기서는 단순 분할만 예시.
    """
    slides = []
    lines = outline_item.content.split("\n")
    chunk_size = max(1, len(lines)//outline_item.pages)

    idx = 0
    for p in range(outline_item.pages):
        part = "\n".join(lines[idx : idx + chunk_size])
        idx += chunk_size
        slide_text = f"# {outline_item.title}\n\n{part}"
        slides.append(slide_text)
    return slides

# 🟢 디자인 적용 Agent (비동기)
async def apply_design_async(slides: List[str], style: str) -> List[str]:
    """
    슬라이드에 디자인 스타일을 적용 (비동기)
    """
    prompt = (
        f"Apply a {style} design theme to the following slides. "
        "Format them properly for a professional presentation:\n\n"
        f"{slides}"
    )
    resp = await llm.ainvoke(prompt)
    return resp.content.split("\n")

# 🟢 이미지 생성 Prompt 생성 및 호출 (비동기)
async def generate_image_async(topic: str, thread_id: str) -> str:
    """프레젠테이션 주제에 맞는 이미지를 생성"""
    # LLM을 사용하여 이미지 생성 프롬프트 생성
    prompt_for_image = (
        f"Create a detailed description for an AI-generated image that represents '{topic}'. "
        "Make sure the description is visually descriptive, specifying colors, composition, and context."
    )
    image_description_resp = await llm.ainvoke(prompt_for_image)
    image_description = image_description_resp.content

    # DALL·E에 최적화된 프롬프트로 이미지 생성
    return dalle.run(image_description)

# 🟢 요약 슬라이드 생성 Agent
def generate_summary(slides: List[str]) -> str:
    """프레젠테이션의 요약 슬라이드를 생성"""
    prompt = (
        "Generate a concise summary slide that captures the key points "
        "from the following slides:\n\n"
        f"{slides}"
    )
    return llm.invoke(prompt).content

# 🟢 발표 스크립트 생성 Agent
def generate_narration(slides: List[str]) -> str:
    """발표자가 참고할 발표 스크립트 생성"""
    prompt = (
        "Write a professional and engaging presentation script based on the following slides. "
        "Ensure a natural flow and appropriate transitions:\n\n"
        f"{slides}"
    )
    return llm.invoke(prompt).content
