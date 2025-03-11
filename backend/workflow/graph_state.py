from typing import Annotated, List, Dict, Union
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[List[str], add_messages]
    topic: Annotated[str, "Presentation Topic"]
    style: Annotated[str, "Presentation Style"]
    outlines: Annotated[List[Union[Dict, BaseModel]], "Presentation Outline"]
    slides: Annotated[List[str], "Split Slides"]         # 분할된 슬라이드 텍스트
    designed_slides: Annotated[str, "Final MARP Slides"] # 최종으로 합쳐진 Slides
    # 이미지 관련은 슬라이드마다 생성하므로, slide별로 처리 후 합칠 예정
    check: Annotated[str, "Conditional Edge Check"]
    thread_id: Annotated[str, "Session Thread ID"]
    summary: Annotated[str, "Summary"]
    script: Annotated[str, "Script"]
    slides_marp: Annotated[str, "Slides for Marp"]
    
    

class OutlineModel(BaseModel):
    """
    각 개요에서 필요한 정보 (내용, 이미지 개수, 위치 등)
    """
    title: Annotated[str, "Outline Title"]
    content: Annotated[str, "Actual text (markdown/HTML)"]
    images: Annotated[int, "Number of images per outline"] = 0
    image_positions: Annotated[List[str], "Positions where images will appear"] = []
    pages: Annotated[int, "Number of pages if content is large"] = 1

class SlideContentModel(BaseModel):
    """
    슬라이드 하나에 들어갈 내용과 이미지 (마크다운 형식)
    """
    slide_markdown: Annotated[str, "Markdown for a single slide"]

class FinalMarpModel(BaseModel):
    """
    최종 Marp 슬라이드 코드
    """
    slides_marp: Annotated[str, "Concatenated Marp code, separated by '---'"]
