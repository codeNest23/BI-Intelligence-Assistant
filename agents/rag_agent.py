"""
RAG Agent: tool-calling PDF Q&A backed by Pinecone integrated embeddings.
"""

from __future__ import annotations

import json
import logging
import re

from openai import APIConnectionError, APIStatusError, OpenAI

from agents.pinecone_store import PineconeChunkIndex, index_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] RAGAgent - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rag_agent")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_chunks",
            "description": "Search the document chunks for relevant passages using a query string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "top_k": {"type": "integer", "description": "Number of chunks to return (1-10)", "default": 3},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_mentions",
            "description": "Count how many times a keyword appears in the entire document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "The word or phrase to count"},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_entities",
            "description": "Extract named entities from a passage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "passage": {"type": "string", "description": "The passage to extract entities from"},
                },
                "required": ["passage"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "decompose_query",
            "description": "Break a complex user question into simpler sub-questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The complex question to decompose"},
                },
                "required": ["question"],
            },
        },
    },
]


def simple_ner(passage: str) -> dict:
    dates = re.findall(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b",
        passage,
    )
    money = re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?", passage, re.I)
    pct = re.findall(r"\d+(?:\.\d+)?\s*%", passage)
    caps = re.findall(r"\b[A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+\b", passage)
    return {"dates": dates, "money": money, "percentages": pct, "proper_nouns": caps[:10]}


def _safe_json_loads(raw: str) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            log.warning("Could not parse tool args: %s | raw=%r", e, raw[:200])
            return {}


class RAGAgent:
    """Agentic RAG with Pinecone-backed retrieval."""

    SYSTEM = """You are an expert research assistant with access to a document knowledge base.
You MUST use your tools to retrieve information before answering.

Workflow:
1. If the question is complex, use `decompose_query` first.
2. For each sub-question, call `search_chunks` to find relevant passages.
3. Use `count_mentions` to verify frequency claims.
4. Use `extract_entities` on relevant passages.
5. Synthesize retrieved evidence into a clear, structured answer.
6. Always cite page/chunk evidence in your final answer.

Answer only from the retrieved document evidence."""

    def __init__(
        self,
        pdf_text: str,
        api_key: str,
        model: str = "openai/gpt-oss-120b:free",
        pdf_name: str | None = None,
        pinecone_namespace: str | None = None,
    ):
        self.full_text = pdf_text
        self.model = model
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        if pinecone_namespace is None:
            pinecone_namespace = index_document(pdf_text, pdf_name)["namespace"]

        self.index = PineconeChunkIndex(
            pdf_text=pdf_text,
            pdf_name=pdf_name,
            namespace=pinecone_namespace,
        )

    def _execute_tool(self, name: str, args: dict) -> str:
        if name == "search_chunks":
            results = self.index.search(args["query"], args.get("top_k", 3))
            if not results:
                return "No relevant passages found."
            return "\n\n---\n\n".join(results)

        if name == "count_mentions":
            kw = args["keyword"].lower()
            count = self.full_text.lower().count(kw)
            return f"'{args['keyword']}' appears {count} times in the document."

        if name == "extract_entities":
            return json.dumps(simple_ner(args["passage"]), indent=2)

        if name == "decompose_query":
            q = args["question"]
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Break the question into 2-4 simpler sub-questions. Return only a JSON list of strings.",
                        },
                        {"role": "user", "content": q},
                    ],
                )
                raw = resp.choices[0].message.content.strip()
                match = re.search(r"\[.*?\]", raw, re.S)
                if match:
                    return match.group(0)
            except Exception as e:
                log.warning("decompose_query API error: %s", e)
            return json.dumps([q])

        return f"Unknown tool: {name}"

    def chat(self, user_message: str, history: list[dict] | None = None, status_callback=None) -> tuple[str, list[dict], list[str]]:
        log.info("chat() called - query: %r", user_message[:100])
        messages = [{"role": "system", "content": self.SYSTEM}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        steps = []
        max_rounds = 8

        for round_num in range(max_rounds):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                )
            except APIStatusError as e:
                err_msg = f"API error {e.status_code}: {e.message}"
                return err_msg, (history or []) + [{"role": "user", "content": user_message}, {"role": "assistant", "content": err_msg}], steps
            except APIConnectionError:
                err_msg = "Connection error - could not reach OpenRouter. Check your internet / API key."
                return err_msg, (history or []) + [{"role": "user", "content": user_message}, {"role": "assistant", "content": err_msg}], steps
            except Exception as e:
                err_msg = f"Unexpected error: {e}"
                return err_msg, (history or []) + [{"role": "user", "content": user_message}, {"role": "assistant", "content": err_msg}], steps

            msg = resp.choices[0].message
            if not msg.tool_calls:
                final = msg.content or "I couldn't find a clear answer."
                new_history = (history or []) + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": final},
                ]
                return final, new_history, steps

            tool_results = []
            for tc in msg.tool_calls:
                fn = tc.function.name
                args = _safe_json_loads(tc.function.arguments or "{}")
                step_msg = f"🔧 **{fn}**({', '.join(f'{k}={repr(v)}' for k, v in args.items())})"
                steps.append(step_msg)
                if status_callback:
                    status_callback(step_msg)

                result = self._execute_tool(fn, args)
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": fn,
                    "content": result,
                })

            messages.append(msg)
            messages.extend(tool_results)

        final = "I've gathered information but reached my reasoning limit. Please try a more specific question."
        return final, (history or []) + [{"role": "user", "content": user_message}, {"role": "assistant", "content": final}], steps
