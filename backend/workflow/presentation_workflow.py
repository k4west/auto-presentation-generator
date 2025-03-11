from langgraph.graph import StateGraph
from langchain.schema import HumanMessage
from langchain_community.callbacks.manager import get_openai_callback
from time import time
from .nodes import *
from .graph_state import GraphState


def build_presentation_workflow():
    workflow = StateGraph(GraphState)

    # ✅ LangGraph 노드 추가
    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("check_relevance", check_relevance_node)
    workflow.add_node("refine_outline", refine_outline_node)
    workflow.add_node("split_outlines", split_outlines_node)
    workflow.add_node("parallel_slides", parallel_slides_node)
    workflow.add_node("handle_feedback", handle_feedback_node)
    workflow.add_node("generate_summary", generate_summary_node)
    workflow.add_node("generate_narration", generate_narration_node)
    workflow.add_node("finalize_presentation", finalize_presentation_node)

    # ✅ 워크플로우 연결
    workflow.set_entry_point("generate_outline")
    workflow.add_edge("generate_outline", "check_relevance")
    workflow.add_edge("check_relevance", "refine_outline")
    workflow.add_edge("refine_outline", "split_outlines")
    workflow.add_edge("split_outlines", "parallel_slides")
    workflow.add_edge("parallel_slides", "handle_feedback")

    # ✅ 피드백 처리 후 개요로 돌아가거나 요약 생성
    workflow.add_conditional_edges(
        "handle_feedback",
        check_feedback,
        {
            "yes": "generate_outline",
            "no": "generate_summary"
        }
    )

    workflow.add_edge("generate_summary", "generate_narration")
    workflow.add_edge("generate_narration", "finalize_presentation")

    workflow.set_finish_point("finalize_presentation")
    return workflow.compile()


async def generate_presentation(user_input: dict, thread_id: str):
    """LangGraph 워크플로우를 실행하여 프레젠테이션 생성"""
    graph = build_presentation_workflow()

    # 초기 상태 설정
    input_state = GraphState(
        message=[HumanMessage(content=user_input["message"])],
        topic=user_input["topic"],
        style=user_input["style"],
        check="no",
        thread_id=thread_id
    )

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": len(graph.nodes) + 3
    }

    # LangGraph 실행
    t = []
    s = time()
    try:
        with get_openai_callback() as cb:
            async for item in graph.astream(input=input_state, config=config):
                for node, value in item.items():
                    print(f"\n[\033[1;36m{node}\033[0m]\n" + "-" * 40)
                    print(value)
                    t.append(f"{node}: {(e:=time()) - s:.3f}초")
                    s = e
            print("\n".join(t), end='\n\n')
    except Exception as e: 
        print(e)
    print(cb)
    return item["finalize_presentation"] if "finalize_presentation" in item else item
