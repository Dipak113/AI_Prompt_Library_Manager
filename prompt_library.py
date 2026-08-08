"""Core logic for the AI Prompt Library Manager.

Kept independent of Streamlit so it can be reused from a script,
a notebook, or a UI.
"""

import json
import os
import random
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "prompts.json")


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

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


def find_prompt(prompts, prompt_id):
    for p in prompts:
        if p["id"] == prompt_id:
            return p
    return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_prompt(prompts, title, text, category, ai_tool, rating, favorite=False, date_added=None):
    prompt = {
        "id": next_id(prompts),
        "title": title.strip(),
        "text": text.strip(),
        "category": category.strip(),
        "ai_tool": ai_tool.strip(),
        "rating": round(float(rating), 1),
        "favorite": bool(favorite),
        "date_added": date_added or date.today().isoformat(),
    }
    prompts.append(prompt)
    return prompt


def update_prompt(prompts, prompt_id, title=None, text=None, category=None, ai_tool=None, rating=None):
    p = find_prompt(prompts, prompt_id)
    if not p:
        return None
    if title is not None:
        p["title"] = title.strip()
    if text is not None:
        p["text"] = text.strip()
    if category is not None:
        p["category"] = category.strip()
    if ai_tool is not None:
        p["ai_tool"] = ai_tool.strip()
    if rating is not None:
        p["rating"] = round(float(rating), 1)
    return p


def delete_prompt(prompts, prompt_id):
    idx = next((i for i, p in enumerate(prompts) if p["id"] == prompt_id), None)
    if idx is None:
        return False
    prompts.pop(idx)
    return True


def toggle_favorite(prompts, prompt_id):
    p = find_prompt(prompts, prompt_id)
    if p:
        p["favorite"] = not p.get("favorite", False)
    return p


# ---------------------------------------------------------------------------
# Search / filter / sort
# ---------------------------------------------------------------------------

def search_prompts(prompts, category=None, ai_tool=None, keyword=None, favorites_only=False):
    results = prompts
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if ai_tool:
        results = [p for p in results if p["ai_tool"].lower() == ai_tool.lower()]
    if keyword:
        kw = keyword.lower()
        results = [
            p for p in results
            if kw in p["title"].lower() or kw in p["text"].lower()
        ]
    if favorites_only:
        results = [p for p in results if p.get("favorite")]
    return results


def sort_prompts(prompts, by="rating", descending=True):
    key_fns = {
        "rating": lambda p: p["rating"],
        "date": lambda p: p["date_added"],
        "title": lambda p: p["title"].lower(),
    }
    key_fn = key_fns.get(by, key_fns["rating"])
    return sorted(prompts, key=key_fn, reverse=descending)


def random_prompt(prompts):
    return random.choice(prompts) if prompts else None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def highest_rated_prompt(prompts):
    if not prompts:
        return None
    return max(prompts, key=lambda p: p["rating"])


def top_rated(prompts, n=5):
    return sort_prompts(prompts, by="rating", descending=True)[:n]


def _count_by(prompts, field):
    counts = {}
    for p in prompts:
        counts[p[field]] = counts.get(p[field], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def count_by_category(prompts):
    return _count_by(prompts, "category")


def count_by_tool(prompts):
    return _count_by(prompts, "ai_tool")


def rating_distribution(prompts):
    buckets = {str(i): 0 for i in range(1, 6)}
    for p in prompts:
        star = min(5, max(1, round(p["rating"])))
        buckets[str(star)] += 1
    return buckets


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
            "total_favorites": 0,
            "average_rating": 0.0,
            "highest_rated": None,
        }
    top = highest_rated_prompt(prompts)
    return {
        "total_prompts": len(prompts),
        "total_categories": len(categories(prompts)),
        "total_ai_tools": len(ai_tools(prompts)),
        "total_favorites": sum(1 for p in prompts if p.get("favorite")),
        "average_rating": round(sum(p["rating"] for p in prompts) / len(prompts), 2),
        "highest_rated": top["title"] if top else None,
    }


# ---------------------------------------------------------------------------
# Import / export
# ---------------------------------------------------------------------------

def prompts_to_json(prompts):
    return json.dumps(prompts, indent=2)


def merge_imported(prompts, imported_list):
    start_id = next_id(prompts)
    added = 0
    for offset, item in enumerate(imported_list):
        prompts.append({
            "id": start_id + offset,
            "title": str(item.get("title", "Untitled")).strip(),
            "text": str(item.get("text", "")).strip(),
            "category": str(item.get("category", "Uncategorized")).strip(),
            "ai_tool": str(item.get("ai_tool", "Unknown")).strip(),
            "rating": round(float(item.get("rating", 0)), 1),
            "favorite": bool(item.get("favorite", False)),
            "date_added": item.get("date_added") or date.today().isoformat(),
        })
        added += 1
    return added
