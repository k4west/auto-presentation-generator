import asyncio
from backend.storage.file_manager import FileManager
from typing import List, Dict, Any
from .agents import *
from .graph_state import *


async def generate_outline_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    주제(topic)와 스타일(style)에 맞는 개요 목록(OutlineModel[])을 생성하여
    state["outlines"]에 저장.
    """
    topic = state["topic"]
    style = state["style"]
    last_user_msg = state["messages"][-1] if state["messages"] else ""

    outlines = generate_outline(topic, style, last_user_msg)  # List[OutlineModel]
    return {"outlines": outlines}


def check_relevance_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    개요 목록을 하나의 텍스트로 합쳐서 주제와 관련성 검사.
    관련 있으면 check='yes', 없으면 check='no'
    """
    topic = state["topic"]
    outlines: List[Dict] = state["outlines"]

    # 간단히 outlines 내용 합침
    combined_outline = "\n\n".join(
        f"{o['title']}\n{o['content']}" for o in outlines
    )

    is_relevant = check_relevance(combined_outline, topic)
    return {"check": "yes" if is_relevant else "no"}


def refine_outline_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 개요(OutlineModel)의 content를 refine_outline으로 보강하여 업데이트.
    """
    outlines: List[OutlineModel] = state["outlines"]
    refined_list = []

    for o in outlines:
        new_content = refine_outline(o["content"])
        refined_list.append(
            OutlineModel(
                title=o["title"],
                content=new_content,
                images=o["images"],
                image_positions=o["image_positions"],
                pages=o["pages"]
            )
        )

    return {"outlines": refined_list}


def split_outlines_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    모든 OutlineModel을 슬라이드들의 리스트로 변환하여 누적.
    """
    outlines: List[OutlineModel] = state["outlines"]
    all_slides: List[str] = []

    for o in outlines:
        slides_for_this_outline = split_outline_to_slides(o)
        all_slides.extend(slides_for_this_outline)

    return {"slides": all_slides}

file_manager = FileManager()


async def parallel_slides_node(state):
    """
    분할된 slides 각각을 비동기로 처리하여
    디자인 + 이미지 생성 후 최종 문자열로 합침
    """
    slides = state["slides"]
    style = state["style"]
    topic = state["topic"]
    thread_id = state["thread_id"]

    # slides가 없으면 바로 return
    if not slides:
        return {"designed_slides": ""}

    # 🟢 각 슬라이드를 처리하는 비동기 함수
    async def process_slide(slide_text: str, idx: int):
        # 1) 디자인 적용
        designed_part = await apply_design_async(slide_text, style)

        # 2) 이미지 생성
        image_url = await generate_image_async(topic, thread_id)
        local_image_path = file_manager.save_image(image_url, thread_id+f"_{idx}")

        # 3) 슬라이드 + 이미지 Markdown 생성
        final_slide = f"{designed_part}\n\n![image]({image_url})"
        return final_slide

    # 🟢 모든 슬라이드를 비동기로 처리
    tasks = [process_slide(s, i) for i, s in enumerate(slides, 1)]
    results = await asyncio.gather(*tasks)

    # 🟢 마크다운 슬라이드 구분자 `---` 로 합치기
    combined_slides = "\n---\n".join(results)
    return {"designed_slides": combined_slides}

async def apply_design_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    슬라이드 배열(slides)에 지정된 스타일(style)을 비동기로 적용.
    결과물은 줄바꿈된 문자열 리스트가 아닌, 각 슬라이드별 텍스트(List[str])로 반환.
    """
    slides: List[str] = state["slides"]
    style: str = state["style"]

    designed_list = await apply_design_async(slides, style)
    return {"designed_slides": designed_list}


async def generate_image_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    프레젠테이션 전체(또는 한 슬라이드)에 사용될 대표 이미지를 생성.
    필요하다면 각 슬라이드마다 이미지를 생성하도록 확장 가능.
    """
    thread_id: str = state["thread_id"]
    topic: str = state["topic"]

    image_url = await generate_image_async(topic, thread_id)
    # 간단히 하나의 이미지만 추가한다고 가정
    return {"image_url": image_url}


def generate_summary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    designed_slides(list[str])를 하나로 합쳐 요약 슬라이드를 생성.
    """
    designed_slides: List[str] = state["designed_slides"]
    # 하나의 문자열로 합침
    combined_slides = "\n".join(designed_slides)

    summary_slide = generate_summary([combined_slides])
    return {"summary": summary_slide}


def generate_narration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    designed_slides(list[str])를 기반으로 발표 스크립트 생성.
    """
    designed_slides: List[str] = state["designed_slides"]
    combined_slides = "\n".join(designed_slides)

    narration = generate_narration([combined_slides])
    return {"script": narration}


def finalize_presentation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 Marp 포맷으로 슬라이드를 이어붙여 문자열로 만든다.
    - slides_marp 필드에 저장 (마크다운 형태)
    - 예) --- 구분자 사용
    """
    designed_slides: List[str] = state["designed_slides"]
    marp_header = """---
marp: true
paginate: true
---
"""
    # 슬라이드들을 --- 로 구분
    body = "\n---\n".join(designed_slides)
    final_markdown = f"{marp_header}\n{body}"

    return {"slides_marp": final_markdown}

# 🟢 피드백을 위한 비동기 큐 (사용자 입력 대기)
feedback_queue = asyncio.Queue()

# 🟢 피드백 확인 함수 (피드백 여부에 따라 흐름 결정)
def check_feedback(state) -> str:
    return state.get("check", "no")  # 기본값 "no" (피드백 없으면 최종 완료로 진행)

# 🟢 사용자 피드백을 비동기적으로 기다리는 함수
async def handle_feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자의 피드백을 대기하고, messages에 피드백을 추가하여 반환.
    'modify'/'change'/'edit' 등의 단어 포함 시 check='yes', 아니면 'no'.
    """
    thread_id = state["thread_id"]
    print(f"[handle_feedback_node] Waiting for user feedback on thread {thread_id}...")

    # 사용자 피드백 대기 (FastAPI의 /feedback/{thread_id} 엔드포인트에서 feedback_queue.put(...)로 전달)
    user_feedback = await feedback_queue.get()
    print(f"[handle_feedback_node] Received feedback: {user_feedback}")

    # 피드백 내용 판단
    if any(word in user_feedback.lower() for word in ["modify", "change", "edit"]):
        return {"check": "yes", "messages": [user_feedback]}
    else:
        return {"check": "no"}
