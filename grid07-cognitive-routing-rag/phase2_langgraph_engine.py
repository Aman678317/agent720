import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from personas import PERSONAS
from config import get_llm_provider
from utils.json_utils import parse_json_safely

def mock_searxng_search(query: str) -> str:
    headlines = {
        "ai": "AI models are becoming smaller and faster.",
        "crypto": "Bitcoin rallies to new all time highs amidst regulation rumors.",
        "finance": "Federal reserve hints at cutting interest rates.",
        "privacy": "New bills passed to protect user data from tech giants.",
        "elon musk": "Elon Musk announces new SpaceX mission to Mars.",
        "space": "James Webb telescope discovers new exoplanet.",
        "economy": "Inflation cools down slightly this quarter.",
    }
    for key, val in headlines.items():
        if key in query.lower():
            return val
    return "Tech industry continues to evolve rapidly."

class GraphState(TypedDict):
    bot_id: str
    bot_name: str
    persona: str
    topic: str
    search_query: str
    search_results: str
    post_content: str
    final_json: dict

def decide_search(state: GraphState):
    provider = get_llm_provider()
    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            prompt = f"Given this persona: '{state['persona']}', what topic should you post about? Output just a short search query."
            query = llm.invoke(prompt).content.strip()
            topic = query
        except:
            topic = "AI"
            query = "AI news"
    else:
        # Mock mode
        topic = "AI and Crypto" if state["bot_id"] == "bot_a" else "Tech Monopolies"
        query = "ai crypto" if state["bot_id"] == "bot_a" else "privacy economy"
        
    state["topic"] = topic
    state["search_query"] = query
    return state

def web_search(state: GraphState):
    res = mock_searxng_search(state["search_query"])
    state["search_results"] = res
    return state

def draft_post(state: GraphState):
    provider = get_llm_provider()
    
    final_dict = {
        "bot_id": state["bot_id"],
        "topic": state["topic"],
        "post_content": ""
    }
    
    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            prompt = f"""
            Persona: {state['persona']}
            Search Context: {state['search_results']}
            Write a short opinionated post under 280 characters.
            Return ONLY a valid JSON object with 'bot_id', 'topic', and 'post_content'.
            """
            res = llm.invoke(prompt).content
            parsed = parse_json_safely(res)
            if "post_content" in parsed:
                final_dict = parsed
            else:
                final_dict["post_content"] = "This is a mock post based on context: " + state["search_results"]
        except:
            final_dict["post_content"] = "This is a fallback mock post based on context: " + state["search_results"]
    else:
        final_dict["post_content"] = f"Just read: {state['search_results']}. Absolutely insane. Matches my persona!"
        
    state["final_json"] = final_dict
    return state

def run_langgraph_engine(bot_id: str):
    persona_data = next((p for p in PERSONAS if p["bot_id"] == bot_id), None)
    if not persona_data:
        raise ValueError("Bot not found")
        
    workflow = StateGraph(GraphState)
    workflow.add_node("decide_search", decide_search)
    workflow.add_node("web_search", web_search)
    workflow.add_node("draft_post", draft_post)
    
    workflow.set_entry_point("decide_search")
    workflow.add_edge("decide_search", "web_search")
    workflow.add_edge("web_search", "draft_post")
    workflow.add_edge("draft_post", END)
    
    app = workflow.compile()
    
    initial_state = {
        "bot_id": bot_id,
        "bot_name": persona_data["name"],
        "persona": persona_data["persona"],
        "topic": "",
        "search_query": "",
        "search_results": "",
        "post_content": "",
        "final_json": {}
    }
    
    res = app.invoke(initial_state)
    return res["final_json"]

if __name__ == "__main__":
    print(json.dumps(run_langgraph_engine("bot_a"), indent=2))
