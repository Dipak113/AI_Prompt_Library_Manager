"""Core logic for the AI Prompt Library Manager.

Kept independent of Streamlit so it can be reused from a script,
a notebook, or a UI.
"""

import json
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "prompts.json")


def load_prompts(path=DATA_FILE):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prompts(prompts, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2)


def next_id(prompts):
    return max((p["id"] for p in prompts), default=0) + 1


def add_prompt(prompts, title, text, category, ai_tool, rating, date_added=None):
    prompt = {
        "id": next_id(prompts),
        "title": title.strip(),
        "text": text.strip(),
        "category": category.strip(),
        "ai_tool": ai_tool.strip(),
        "rating": round(float(rating), 1),
        "date_added": date_added or date.today().isoformat(),
    }
    prompts.append(prompt)
    return prompt


def search_prompts(prompts, category=None, ai_tool=None):
    results = prompts
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if ai_tool:
        results = [p for p in results if p["ai_tool"].lower() == ai_tool.lower()]
    return results


def highest_rated_prompt(prompts):
    if not prompts:
        return None
    return max(prompts, key=lambda p: p["rating"])


def count_by_category(prompts):
    counts = {}
    for p in prompts:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def categories(prompts):
    return sorted({p["category"] for p in prompts})


def ai_tools(prompts):
    return sorted({p["ai_tool"] for p in prompts})


def library_summary(prompts):
    if not prompts:
        return {
            "total_prompts": 0,
            "total_categories": 0,
            "total_ai_tools": 0,
            "average_rating": 0.0,
            "highest_rated": None,
        }
    top = highest_rated_prompt(prompts)
    return {
        "total_prompts": len(prompts),
        "total_categories": len(categories(prompts)),
        "total_ai_tools": len(ai_tools(prompts)),
        "average_rating": round(sum(p["rating"] for p in prompts) / len(prompts), 2),
        "highest_rated": top["title"] if top else None,
    }
