"""
Trend Analysis Agent — Multi-Step Tool Calling
================================================
Analyses text documents for:
  - Keyword frequency trends over pages/sections
  - Sentiment arc across the document
  - Topic distribution (simple TF-IDF)
  - Named-entity timelines
  - Comparative statistics

Returns structured JSON data for chart rendering.
"""

from __future__ import annotations
import re, json, math, logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from openai import OpenAI

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] TrendAgent — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("trend_agent")


def _safe_json_loads(raw: str) -> dict:
    """Parse JSON that may contain control characters from LLM output."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re as _re
        cleaned = _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            log.warning("Could not parse tool args after sanitising: %s | raw=%r", e, raw[:200])
            return {}

# ──────────────────────────────────────────────────────────────────────────────
# TREND TOOLS SCHEMA
# ──────────────────────────────────────────────────────────────────────────────
TREND_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "keyword_frequency_over_pages",
            "description": "Count occurrences of given keywords per page/section and return data for a line chart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keywords to track (max 5)",
                    }
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sentiment_arc",
            "description": "Compute a sentiment score per page to show emotional arc of the document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "granularity": {
                        "type": "string",
                        "enum": ["page", "paragraph"],
                        "description": "Granularity of sentiment analysis",
                        "default": "page",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_topics",
            "description": "Extract top N topics (words/phrases) by TF-IDF weight as a bar chart dataset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Number of top topics to return", "default": 15}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "word_count_stats",
            "description": "Return word count statistics per page (min, max, avg, per-page array) for histogram.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "entity_timeline",
            "description": "Extract named entities and which pages they appear on (people, money, dates).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_insight_summary",
            "description": "Generate a natural language insight summary given collected trend data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_description": {
                        "type": "string",
                        "description": "JSON or text description of the collected trend data",
                    }
                },
                "required": ["data_description"],
            },
        },
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# POSITIVE / NEGATIVE WORD LISTS (AFINN-lite)
# ──────────────────────────────────────────────────────────────────────────────
POS_WORDS = {
    "good","great","excellent","positive","strong","growth","increase","success",
    "profit","gain","improve","benefit","advantage","opportunity","effective",
    "efficient","innovative","achieve","outstanding","remarkable","best",
    "significant","robust","healthy","stable","progress","high","rise",
}
NEG_WORDS = {
    "bad","poor","negative","weak","decline","decrease","loss","fail","risk",
    "problem","issue","concern","difficult","challenge","low","fall","drop",
    "deficit","debt","crisis","threat","danger","critical","severe","worse",
}

def simple_sentiment(text: str) -> float:
    """Return sentiment score in [-1, 1]."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    total = pos + neg
    return (pos - neg) / total if total > 0 else 0.0

# ──────────────────────────────────────────────────────────────────────────────
# TF-IDF
# ──────────────────────────────────────────────────────────────────────────────
STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall","this",
    "that","these","those","it","its","from","by","as","page","---","their",
    "they","we","our","us","i","you","he","she","him","her","his","not","also",
    "which","who","what","when","where","how","all","more","than","into","over",
    "after","before","about","through","between","during","each","both","only",
}

def tfidf_top_words(pages: list[str], top_n: int = 15) -> list[dict]:
    n_docs = len(pages)
    tf_counters = [Counter(re.findall(r'\b[a-z]{3,}\b', p.lower())) for p in pages]
    df = Counter()
    for c in tf_counters:
        df.update(c.keys())

    scores = Counter()
    for c in tf_counters:
        for word, freq in c.items():
            if word in STOP_WORDS:
                continue
            idf = math.log((n_docs + 1) / (df[word] + 1)) + 1
            scores[word] += (freq / max(sum(c.values()), 1)) * idf

    return [{"word": w, "score": round(s, 4)} for w, s in scores.most_common(top_n)]

# ──────────────────────────────────────────────────────────────────────────────
# TREND ANALYSIS AGENT
# ──────────────────────────────────────────────────────────────────────────────
class TrendAgent:
    """
    Agentic trend analyser.
    Runs a tool-calling loop and returns both:
      - `charts`: list of chart-spec dicts for rendering
      - `insights`: natural language summary
      - `steps`: reasoning trace
    """

    SYSTEM = (
        "You are a senior data analyst specialising in document trend analysis.\n"
        "Your role is to call each available tool exactly once, in order, to build\n"
        "a complete picture of the document's structure, language, and themes.\n\n"
        "Tool call order (mandatory):\n"
        "  1. keyword_frequency_over_pages — track term evolution across pages.\n"
        "  2. sentiment_arc               — map the emotional tone per page.\n"
        "  3. top_topics                  — find dominant TF-IDF themes.\n"
        "  4. word_count_stats            — surface density and length patterns.\n"
        "  5. entity_timeline             — locate dates and monetary references.\n"
        "  6. generate_insight_summary    — synthesise ONLY after the above 5 tools.\n\n"
        "Rules:\n"
        "- Do NOT skip any tool.\n"
        "- Do NOT call a tool more than once.\n"
        "- Pass only a compact JSON summary (<1 500 chars) to generate_insight_summary.\n"
        "- After generate_insight_summary returns, output NOTHING else — stop immediately."
    )

    def __init__(self, pdf_pages: list[str], api_key: str, model: str = "openai/gpt-oss-120b:free"):
        """
        pdf_pages: list of page text strings (one per page)
        """
        self.pages = pdf_pages
        self.model = model
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.charts: list[dict] = []

    # ── Tool execution ─────────────────────────────────────────────────────────
    def _execute_tool(self, name: str, args: dict) -> str:
        pages = self.pages

        if name == "keyword_frequency_over_pages":
            keywords = [k.lower() for k in args.get("keywords", [])[:5]]
            series = {}
            for kw in keywords:
                series[kw] = [page.lower().count(kw) for page in pages]
            chart = {
                "type": "line",
                "title": f"Keyword Frequency Over Pages",
                "labels": [f"P{i+1}" for i in range(len(pages))],
                "datasets": [
                    {"label": kw, "data": counts}
                    for kw, counts in series.items()
                ],
            }
            self.charts.append(chart)
            return json.dumps({"keywords": series, "page_count": len(pages)})

        elif name == "sentiment_arc":
            scores = [round(simple_sentiment(p), 3) for p in pages]
            chart = {
                "type": "line",
                "title": "Sentiment Arc Across Document",
                "labels": [f"P{i+1}" for i in range(len(pages))],
                "datasets": [{"label": "Sentiment", "data": scores}],
                "yMin": -1, "yMax": 1,
            }
            self.charts.append(chart)
            avg = round(sum(scores) / len(scores), 3) if scores else 0
            return json.dumps({"sentiment_per_page": scores, "avg_sentiment": avg})

        elif name == "top_topics":
            top_n = args.get("top_n", 15)
            items = tfidf_top_words(pages, top_n)
            chart = {
                "type": "bar",
                "title": f"Top {top_n} Topics by TF-IDF",
                "labels": [x["word"] for x in items],
                "datasets": [{"label": "TF-IDF Score", "data": [x["score"] for x in items]}],
            }
            self.charts.append(chart)
            return json.dumps(items)

        elif name == "word_count_stats":
            counts = [len(p.split()) for p in pages]
            chart = {
                "type": "bar",
                "title": "Word Count per Page",
                "labels": [f"P{i+1}" for i in range(len(pages))],
                "datasets": [{"label": "Words", "data": counts}],
            }
            self.charts.append(chart)
            return json.dumps({
                "per_page": counts,
                "min": min(counts) if counts else 0,
                "max": max(counts) if counts else 0,
                "avg": round(sum(counts) / len(counts), 1) if counts else 0,
                "total": sum(counts),
            })

        elif name == "entity_timeline":
            date_pat  = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b')
            money_pat = re.compile(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?', re.I)
            per_page  = []
            for i, page in enumerate(pages):
                dates = date_pat.findall(page)
                money = money_pat.findall(page)
                per_page.append({"page": i + 1, "dates": dates, "money": money})

            date_counts  = [len(p["dates"])  for p in per_page]
            money_counts = [len(p["money"]) for p in per_page]
            chart = {
                "type": "bar",
                "title": "Entity Density per Page",
                "labels": [f"P{i+1}" for i in range(len(pages))],
                "datasets": [
                    {"label": "Dates",  "data": date_counts},
                    {"label": "Monetary Refs", "data": money_counts},
                ],
            }
            self.charts.append(chart)
            return json.dumps(per_page)

        elif name == "generate_insight_summary":
            data_desc = args.get("data_description", "")[:2000]  # hard cap — prevents token overflow
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=512,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise document analyst. "
                            "Write exactly 4-5 bullet points (• prefix). "
                            "Each bullet must be one sentence, ≤ 20 words. "
                            "No preamble, no headers, no extra text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Summarise these document trend findings in 4-5 bullet points:\n{data_desc}",
                    },
                ],
            )
            return resp.choices[0].message.content.strip()

        return f"Unknown tool: {name}"

    # ── Agentic loop ───────────────────────────────────────────────────────────
    def analyse(self, user_query: str = "Perform a comprehensive trend analysis of this document.", status_callback=None) -> dict:
        """
        Returns {charts, insights, steps}.
        """
        log.info("analyse() called — query: %r", user_query[:80])
        self.charts = []
        keyword_match = re.search(r"keywords?:\s*(.+?)(?:\.|$)", user_query, re.I)
        keywords = ["risk", "growth", "revenue", "innovation", "cost"]
        if keyword_match:
            parsed = [k.strip() for k in keyword_match.group(1).split(",") if k.strip()]
            if parsed:
                keywords = parsed[:5]

        jobs = [
            ("keyword_frequency_over_pages", {"keywords": keywords}),
            ("sentiment_arc", {"granularity": "page"}),
            ("top_topics", {"top_n": 15}),
            ("word_count_stats", {}),
            ("entity_timeline", {}),
        ]
        steps = []
        collected = {}

        with ThreadPoolExecutor(max_workers=min(len(jobs), 5)) as executor:
            future_to_job = {
                executor.submit(self._execute_tool, name, args): (name, args)
                for name, args in jobs
            }
            for future in as_completed(future_to_job):
                name, args = future_to_job[future]
                step = f"📊 **{name}**({', '.join(f'{k}={repr(v)}' for k,v in args.items())})"
                steps.append(step)
                if status_callback:
                    status_callback(step)
                try:
                    collected[name] = future.result()
                except Exception as e:
                    log.error("Parallel trend job failed: %s args=%r error=%s", name, args, e)
                    collected[name] = f"Error: {e}"

        # Build a compact summary for the LLM — keep only key scalars, not full arrays
        compact = {}
        for tool_name, raw in collected.items():
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                if tool_name == "keyword_frequency_over_pages":
                    compact[tool_name] = {"page_count": parsed.get("page_count", 0),
                                          "keywords_tracked": list(parsed.get("keywords", {}).keys())}
                elif tool_name == "sentiment_arc":
                    compact[tool_name] = {"avg_sentiment": parsed.get("avg_sentiment", 0)}
                elif tool_name == "top_topics":
                    compact[tool_name] = {"top_5": parsed[:5] if isinstance(parsed, list) else []}
                elif tool_name == "word_count_stats":
                    compact[tool_name] = {
                        k: parsed.get(k) for k in ("min", "max", "avg", "total")
                    }
                elif tool_name == "entity_timeline":
                    total_dates  = sum(len(p.get("dates",  [])) for p in parsed) if isinstance(parsed, list) else 0
                    total_money  = sum(len(p.get("money",  [])) for p in parsed) if isinstance(parsed, list) else 0
                    compact[tool_name] = {"total_dates": total_dates, "total_money_refs": total_money}
                else:
                    compact[tool_name] = str(raw)[:300]
            except Exception:
                compact[tool_name] = str(raw)[:300]

        compact_str = json.dumps(compact, indent=None)[:1500]
        try:
            insights = self._execute_tool(
                "generate_insight_summary",
                {"data_description": compact_str},
            )
            steps.append("📊 **generate_insight_summary**(compact=True)")
            if status_callback:
                status_callback(steps[-1])
        except Exception as e:
            log.error("Insight summary failed: %s", e)
            insights = "Analysis complete. See charts above for trends."

        log.info("parallel analyse() done — %d charts, %d steps", len(self.charts), len(steps))
        return {"charts": self.charts, "insights": insights, "steps": steps}
