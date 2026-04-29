"""
Support Copilot - LangGraph multi-step support agent with tool calling.

Flow: classify -> retrieve -> answer (with tools) -> escalate (if low confidence)
"""
from typing import TypedDict, List, Optional
from pathlib import Path
import time
from langgraph.graph import StateGraph, END
from anthropic import Anthropic
import chromadb
from dotenv import load_dotenv

from tools import TOOLS, execute_tool

load_dotenv()


class AgentState(TypedDict):
    question: str
    history: List[dict]
    category: str
    chunks: List[str]
    sources: List[str]
    answer: str
    confidence: float
    needs_human: bool
    tool_calls: List[dict]
    metrics: dict


SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / "docs"
CONFIDENCE_THRESHOLD = 0.6
MAX_TOOL_ITERATIONS = 4
MODEL = "claude-sonnet-4-6"

client = Anthropic()
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("support_docs")


def auto_ingest():
    if collection.count() > 0:
        return
    for doc_file in DOCS_DIR.glob("*.txt"):
        with open(doc_file, "r") as f:
            text = f.read()
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, chunk in enumerate(chunks):
            collection.add(
                ids=[f"{doc_file.stem}_chunk_{i}"],
                documents=[chunk],
                metadatas=[{"source": doc_file.name}],
            )


auto_ingest()


def classify(state: AgentState) -> AgentState:
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        system=(
            "Classify the user's question as exactly one word: "
            "'technical' (API usage, errors, integration), "
            "'billing' (pricing, invoices, payment, disputes), "
            "'account' (login, settings, profile, usage, quota), "
            "or 'other'. Respond with only the category word."
        ),
        messages=[{"role": "user", "content": state["question"]}],
    )
    category = response.content[0].text.strip().lower()
    if category not in ["technical", "billing", "account", "other"]:
        category = "other"
    return {**state, "category": category}


def retrieve(state: AgentState) -> AgentState:
    results = collection.query(query_texts=[state["question"]], n_results=5)
    chunks = results["documents"][0]
    sources = list({m["source"] for m in results["metadatas"][0]})
    return {**state, "chunks": chunks, "sources": sources}


def answer(state: AgentState) -> AgentState:
    """Generate answer. Tools-first prompting."""
    context = "\n\n---\n\n".join(state["chunks"])

    history_text = ""
    if state.get("history"):
        recent = state["history"][-3:]
        history_text = "\nPREVIOUS TURNS:\n"
        for turn in recent:
            history_text += f"- User: {turn['question']}\n  Agent: {turn['answer'][:200]}\n"

    system_prompt = f"""You are a customer support agent for Acme API.

YOU HAVE TWO TOOLS - USE THEM EAGERLY:

1. lookup_account(user_email) - CALL THIS WHENEVER the user gives an email address or asks about their own account/plan/usage/quota. The user does not have to say "look up" - just the presence of an email triggers this.

2. create_support_ticket(subject, body, priority) - CALL THIS WHENEVER the user asks to file/open/create a ticket, OR has a billing dispute, refund request, double-charge, or urgent issue.

ABSOLUTELY DO NOT SAY:
- "I don't have access to your account" -> instead call lookup_account
- "I cannot create tickets" -> instead call create_support_ticket
- "Contact billing@acme.com" for disputes -> instead call create_support_ticket

You DO have access via these tools. USE THEM.

For general questions (no email, no ticket request), use this reference documentation:
{context}
{history_text}

Always end your final answer on a separate line with: CONFIDENCE: 0.X (0.0 to 1.0).
"""

    messages = [{"role": "user", "content": state["question"]}]
    tool_calls_made: List[dict] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Detect tool_use via content blocks (most reliable)
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in tool_use_blocks:
                result = execute_tool(block.name, dict(block.input))
                tool_calls_made.append({
                    "name": block.name,
                    "input": dict(block.input),
                    "result": result,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Final text answer
        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        confidence = 0.5
        answer_text = text
        if "CONFIDENCE:" in text:
            try:
                parts = text.split("CONFIDENCE:")
                answer_text = parts[0].strip()
                confidence = float(parts[1].strip().split()[0])
            except (ValueError, IndexError):
                pass

        return {
            **state,
            "answer": answer_text,
            "confidence": confidence,
            "needs_human": confidence < CONFIDENCE_THRESHOLD,
            "tool_calls": tool_calls_made,
        }

    return {
        **state,
        "answer": "I had trouble resolving this. Escalating to a human.",
        "confidence": 0.3,
        "needs_human": True,
        "tool_calls": tool_calls_made,
    }


def escalate(state: AgentState) -> AgentState:
    handoff = (
        f"I'm not confident enough to be helpful here, so I'm connecting "
        f"you with a human support agent.\n\n"
        f"Summary for the team:\n"
        f"- Question: {state['question']}\n"
        f"- Category: {state.get('category', 'unclassified')}\n"
        f"- My best attempt: {state.get('answer', 'no draft')}\n"
        f"- Confidence: {state.get('confidence', 0.0):.2f}\n\n"
        f"A team member will follow up shortly."
    )
    return {**state, "answer": handoff, "needs_human": True}


def route_after_answer(state: AgentState) -> str:
    return "escalate" if state["needs_human"] else END


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("classify", classify)
    g.add_node("retrieve", retrieve)
    g.add_node("answer", answer)
    g.add_node("escalate", escalate)

    g.set_entry_point("classify")
    g.add_conditional_edges(
        "classify",
        lambda s: "escalate" if s["category"] == "other" else "retrieve",
        {"escalate": "escalate", "retrieve": "retrieve"},
    )
    g.add_edge("retrieve", "answer")
    g.add_conditional_edges(
        "answer",
        route_after_answer,
        {"escalate": "escalate", END: END},
    )
    g.add_edge("escalate", END)
    return g.compile()


agent = build_graph()


def run_agent(question: str, history: Optional[List[dict]] = None) -> dict:
    start = time.time()
    initial_state: AgentState = {
        "question": question,
        "history": history or [],
        "category": "",
        "chunks": [],
        "sources": [],
        "answer": "",
        "confidence": 0.0,
        "needs_human": False,
        "tool_calls": [],
        "metrics": {},
    }
    result = agent.invoke(initial_state)
    result["metrics"] = {"latency_seconds": round(time.time() - start, 2)}
    return result


if __name__ == "__main__":
    print("Support Copilot - type a question, or 'quit' to exit")
    history: List[dict] = []
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"quit", "exit"}:
            break
        if not q:
            continue
        result = run_agent(q, history)
        print(f"\n[category: {result['category']} | confidence: {result['confidence']:.2f} | latency: {result['metrics']['latency_seconds']}s | tools: {len(result['tool_calls'])}]")
        if result["needs_human"]:
            print("ESCALATED TO HUMAN")
        print(f"\nAgent: {result['answer']}")
        if result["tool_calls"]:
            print("\nTool calls:")
            for tc in result["tool_calls"]:
                print(f"  - {tc['name']}({tc['input']}) -> {tc['result']}")
        if result["sources"]:
            print(f"\nSources: {', '.join(result['sources'])}")
        history.append({"question": q, "answer": result["answer"]})
