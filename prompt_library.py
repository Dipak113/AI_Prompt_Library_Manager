"""Core logic for the AI Prompt Library Manager.

Kept independent of Streamlit so it can be reused from a script,
a notebook, or a UI.
"""

import json
import os
import random
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "prompts.json")  # default JSON "database" file


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def load_prompts(path=DATA_FILE):
    # Read the whole prompt list from disk; empty list if the file doesn't exist yet
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prompts(prompts, path=DATA_FILE):
    # Overwrite the JSON file with the current in-memory list
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2)


def next_id(prompts):
    # Next free id = highest existing id + 1 (1 if the library is empty)
    return max((p["id"] for p in prompts), default=0) + 1


def find_prompt(prompts, prompt_id):
    # Linear lookup by id; returns None if not found
    for p in prompts:
        if p["id"] == prompt_id:
            return p
    return None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_prompt(prompts, title, text, category, ai_tool, rating, favorite=False, date_added=None):
    # Build a new prompt dict, append it in place, and return it
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
    # Only overwrite fields that were actually passed in (None = "leave unchanged")
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
    # Remove the prompt with this id from the list in place; False if it wasn't found
    idx = next((i for i, p in enumerate(prompts) if p["id"] == prompt_id), None)
    if idx is None:
        return False
    prompts.pop(idx)
    return True


def toggle_favorite(prompts, prompt_id):
    # Flip the favorite flag on/off for one prompt
    p = find_prompt(prompts, prompt_id)
    if p:
        p["favorite"] = not p.get("favorite", False)
    return p


# ---------------------------------------------------------------------------
# Search / filter / sort
# ---------------------------------------------------------------------------

def search_prompts(prompts, category=None, ai_tool=None, keyword=None, favorites_only=False):
    # Apply each filter only if it was given, narrowing the result set step by step
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
    # Look up the sort key function by name, defaulting to rating
    key_fns = {
        "rating": lambda p: p["rating"],
        "date": lambda p: p["date_added"],
        "title": lambda p: p["title"].lower(),
    }
    key_fn = key_fns.get(by, key_fns["rating"])
    return sorted(prompts, key=key_fn, reverse=descending)


def random_prompt(prompts):
    # Used by the Dashboard's "Surprise Me" button
    return random.choice(prompts) if prompts else None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def highest_rated_prompt(prompts):
    # Single prompt with the max rating (ties broken by list order)
    if not prompts:
        return None
    return max(prompts, key=lambda p: p["rating"])


def top_rated(prompts, n=5):
    # Leaderboard: top n prompts by rating, highest first
    return sort_prompts(prompts, by="rating", descending=True)[:n]


def _count_by(prompts, field):
    # Generic tally helper shared by count_by_category / count_by_tool
    counts = {}
    for p in prompts:
        counts[p[field]] = counts.get(p[field], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def count_by_category(prompts):
    return _count_by(prompts, "category")


def count_by_tool(prompts):
    return _count_by(prompts, "ai_tool")


def rating_distribution(prompts):
    # Bucket every prompt into a 1-5 star bucket for the histogram chart
    buckets = {str(i): 0 for i in range(1, 6)}
    for p in prompts:
        star = min(5, max(1, round(p["rating"])))
        buckets[str(star)] += 1
    return buckets


def categories(prompts):
    # Unique, alphabetically sorted category list (used to populate filter dropdowns)
    return sorted({p["category"] for p in prompts})


def ai_tools(prompts):
    # Unique, alphabetically sorted AI tool list (used to populate filter dropdowns)
    return sorted({p["ai_tool"] for p in prompts})


def library_summary(prompts):
    # Aggregate headline numbers shown on the Dashboard / Summary pages
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
    # Serialize the whole library for the download button
    return json.dumps(prompts, indent=2)


def merge_imported(prompts, imported_list):
    # Append externally-imported prompts with freshly assigned ids so they never collide with existing ones
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
