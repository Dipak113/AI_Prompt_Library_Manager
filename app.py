import html
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import prompt_library as lib

st.set_page_config(
    page_title="AI Prompt Library Manager",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    css_path = Path(__file__).parent / "style.css"
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

if "prompts" not in st.session_state:
    st.session_state.prompts = lib.load_prompts()
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "surprise_id" not in st.session_state:
    st.session_state.surprise_id = None

prompts = st.session_state.prompts


def esc(text):
    return html.escape(str(text))


def rating_class(rating):
    if rating >= 4.5:
        return "rating-good"
    if rating >= 3.5:
        return "rating-mid"
    return "rating-low"


def to_df(rows):
    if not rows:
        return pd.DataFrame(
            columns=["id", "title", "category", "ai_tool", "rating", "favorite", "date_added", "text"]
        )
    return pd.DataFrame(rows)[
        ["id", "title", "category", "ai_tool", "rating", "favorite", "date_added", "text"]
    ]


def static_bar_chart(labels, values, color, horizontal=False):
    """A fully static (no-animation) bar chart rendered as a PNG via matplotlib."""
    fig, ax = plt.subplots(figsize=(6, 3.0))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    if horizontal:
        ax.barh(labels, values, color=color, edgecolor="none")
        ax.invert_yaxis()
        ax.grid(axis="x", color="#9fb0d0", alpha=0.15, linewidth=0.6)
    else:
        ax.bar(labels, values, color=color, edgecolor="none")
        ax.grid(axis="y", color="#9fb0d0", alpha=0.15, linewidth=0.6)

    ax.set_axisbelow(True)
    ax.tick_params(colors="#9fb0d0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_hero():
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-title">🧠 AI PROMPT LIBRARY</div>
            <div class="hero-sub">Neural-grade prompt management &amp; discovery console</div>
            <div class="status-pill"><span class="status-dot"></span>SYSTEM ONLINE &middot; {len(prompts)} PROMPTS INDEXED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_tile(col, number, label):
    col.markdown(
        f"""<div class="stat-tile"><div class="stat-num">{esc(number)}</div>
        <div class="stat-label">{esc(label)}</div></div>""",
        unsafe_allow_html=True,
    )


def render_prompt_card(p):
    with st.container(border=True):
        if st.session_state.editing_id == p["id"]:
            render_edit_form(p)
            return

        fav_badge = '<span class="badge badge-fav">★ FAVORITE</span>' if p.get("favorite") else ""
        st.markdown(
            f"""
            <div class="card-title">{esc(p['title'])}</div>
            <span class="badge badge-cat">{esc(p['category'])}</span>
            <span class="badge badge-tool">{esc(p['ai_tool'])}</span>
            {fav_badge}
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<span class="rating-pill {rating_class(p['rating'])}">★ {p['rating']:.1f}</span>
            &nbsp;<span style="color:var(--text-dim);font-size:0.78rem;">added {esc(p['date_added'])}</span>""",
            unsafe_allow_html=True,
        )
        st.code(p["text"], language=None)

        if st.session_state.confirm_delete_id == p["id"]:
            st.warning(f"Delete '{p['title']}' permanently?")
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirm delete", key=f"confirm_del_{p['id']}", use_container_width=True):
                lib.delete_prompt(st.session_state.prompts, p["id"])
                lib.save_prompts(st.session_state.prompts)
                st.session_state.confirm_delete_id = None
                st.rerun()
            if c2.button("✖ Cancel", key=f"cancel_del_{p['id']}", use_container_width=True):
                st.session_state.confirm_delete_id = None
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            fav_label = "★ Unfavorite" if p.get("favorite") else "☆ Favorite"
            if c1.button(fav_label, key=f"fav_{p['id']}", use_container_width=True):
                lib.toggle_favorite(st.session_state.prompts, p["id"])
                lib.save_prompts(st.session_state.prompts)
                st.rerun()
            if c2.button("✏ Edit", key=f"edit_{p['id']}", use_container_width=True):
                st.session_state.editing_id = p["id"]
                st.rerun()
            if c3.button("🗑 Delete", key=f"del_{p['id']}", use_container_width=True):
                st.session_state.confirm_delete_id = p["id"]
                st.rerun()


def render_edit_form(p):
    st.markdown('<div class="section-tag">Editing prompt</div>', unsafe_allow_html=True)
    with st.form(f"edit_form_{p['id']}"):
        title = st.text_input("Title", value=p["title"])
        text = st.text_area("Prompt Text", value=p["text"], height=110)
        col1, col2 = st.columns(2)
        category = col1.text_input("Category", value=p["category"])
        ai_tool = col2.text_input("AI Tool", value=p["ai_tool"])
        rating = st.slider("Rating", 0.0, 5.0, float(p["rating"]), 0.1)
        c1, c2 = st.columns(2)
        save_clicked = c1.form_submit_button("💾 Save changes", use_container_width=True)
        cancel_clicked = c2.form_submit_button("✖ Cancel", use_container_width=True)

    if save_clicked:
        lib.update_prompt(
            st.session_state.prompts, p["id"],
            title=title, text=text, category=category, ai_tool=ai_tool, rating=rating,
        )
        lib.save_prompts(st.session_state.prompts)
        st.session_state.editing_id = None
        st.rerun()
    if cancel_clicked:
        st.session_state.editing_id = None
        st.rerun()


render_hero()

with st.sidebar:
    st.markdown('<div class="section-tag">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        [
            "🏠 Dashboard",
            "📚 View Prompts",
            "🔍 Search",
            "➕ Add Prompt",
            "🏆 Highest Rated",
            "📊 Category Insights",
            "📈 Summary & Export",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown('<div class="section-tag">Quick Stats</div>', unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    stat_tile(s1, len(prompts), "Prompts")
    stat_tile(s2, sum(1 for p in prompts if p.get("favorite")), "Favorites")

if page == "🏠 Dashboard":
    summary = lib.library_summary(prompts)
    c1, c2, c3, c4, c5 = st.columns(5)
    stat_tile(c1, summary["total_prompts"], "Total Prompts")
    stat_tile(c2, summary["total_categories"], "Categories")
    stat_tile(c3, summary["total_ai_tools"], "AI Tools")
    stat_tile(c4, summary["total_favorites"], "Favorites")
    stat_tile(c5, summary["average_rating"], "Avg Rating")

    st.write("")
    left, right = st.columns([1.3, 1])

    with left:
        st.markdown('<div class="section-tag">Rating distribution</div>', unsafe_allow_html=True)
        with st.container(border=True):
            dist = lib.rating_distribution(prompts)
            labels = [f"{k}★" for k in dist.keys()]
            static_bar_chart(labels, list(dist.values()), color="#00e5ff")

    with right:
        st.markdown('<div class="section-tag">Prompt-of-the-moment</div>', unsafe_allow_html=True)
        with st.container(border=True):
            if st.button("🎲 Surprise Me", use_container_width=True):
                pick = lib.random_prompt(prompts)
                st.session_state.surprise_id = pick["id"] if pick else None
            surprise = None
            if st.session_state.surprise_id is not None:
                surprise = lib.find_prompt(prompts, st.session_state.surprise_id)
            if not surprise and prompts:
                surprise = prompts[0]
            if surprise:
                st.markdown(f"**{esc(surprise['title'])}**")
                st.markdown(
                    f'<span class="badge badge-cat">{esc(surprise["category"])}</span>'
                    f'<span class="badge badge-tool">{esc(surprise["ai_tool"])}</span>',
                    unsafe_allow_html=True,
                )
                st.code(surprise["text"], language=None)
            else:
                st.info("Add a prompt to see it featured here.")

elif page == "📚 View Prompts":
    st.markdown('<div class="section-tag">All prompts</div>', unsafe_allow_html=True)
    sort_by = st.selectbox("Sort by", ["rating", "date", "title"], index=0)
    ordered = lib.sort_prompts(prompts, by=sort_by, descending=(sort_by != "title"))

    if not ordered:
        st.info("No prompts yet. Add one from the 'Add Prompt' page.")
    else:
        cols = st.columns(2)
        for i, p in enumerate(ordered):
            with cols[i % 2]:
                render_prompt_card(p)

elif page == "🔍 Search":
    st.markdown('<div class="section-tag">Search &amp; filter</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", ["Any"] + lib.categories(prompts))
        ai_tool = c2.selectbox("AI Tool", ["Any"] + lib.ai_tools(prompts))
        keyword = st.text_input("Keyword (title or prompt text)")
        favorites_only = st.checkbox("Favorites only")

    results = lib.search_prompts(
        prompts,
        category=None if category == "Any" else category,
        ai_tool=None if ai_tool == "Any" else ai_tool,
        keyword=keyword or None,
        favorites_only=favorites_only,
    )
    st.write(f"**{len(results)}** matching prompt(s)")
    if results:
        st.dataframe(to_df(results), use_container_width=True, hide_index=True)

elif page == "➕ Add Prompt":
    st.markdown('<div class="section-tag">Register a new prompt</div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.form("add_prompt_form", clear_on_submit=True):
            title = st.text_input("Title")
            text = st.text_area("Prompt Text", height=120)
            col1, col2 = st.columns(2)
            category = col1.text_input("Category (e.g. Writing, Coding)")
            ai_tool = col2.text_input("AI Tool (e.g. ChatGPT, Claude)")
            rating = st.slider("Rating", 0.0, 5.0, 4.0, 0.1)
            favorite = st.checkbox("Mark as favorite")
            submitted = st.form_submit_button("🚀 Add Prompt", use_container_width=True)

        if submitted:
            if not title or not text or not category or not ai_tool:
                st.error("Please fill in all fields before submitting.")
            else:
                new_prompt = lib.add_prompt(
                    st.session_state.prompts, title, text, category, ai_tool, rating, favorite=favorite
                )
                lib.save_prompts(st.session_state.prompts)
                st.success(f"Added prompt '{new_prompt['title']}' (id {new_prompt['id']}).")

elif page == "🏆 Highest Rated":
    st.markdown('<div class="section-tag">Top performer</div>', unsafe_allow_html=True)
    top = lib.highest_rated_prompt(prompts)
    if not top:
        st.info("No prompts available yet.")
    else:
        with st.container(border=True):
            st.markdown(f"### {esc(top['title'])}")
            st.markdown(
                f'<span class="badge badge-cat">{esc(top["category"])}</span>'
                f'<span class="badge badge-tool">{esc(top["ai_tool"])}</span>'
                f'<span class="rating-pill {rating_class(top["rating"])}">★ {top["rating"]:.1f}</span>',
                unsafe_allow_html=True,
            )
            st.code(top["text"], language=None)

        st.write("")
        st.markdown('<div class="section-tag">Leaderboard (top 5)</div>', unsafe_allow_html=True)
        with st.container(border=True):
            leaderboard = lib.top_rated(prompts, n=5)
            st.dataframe(
                to_df(leaderboard)[["title", "category", "ai_tool", "rating"]],
                use_container_width=True,
                hide_index=True,
            )

elif page == "📊 Category Insights":
    st.markdown('<div class="section-tag">Prompts per category</div>', unsafe_allow_html=True)
    counts = lib.count_by_category(prompts)
    if not counts:
        st.info("No prompts available yet.")
    else:
        with st.container(border=True):
            static_bar_chart(list(counts.keys()), list(counts.values()), color="#7c5cff", horizontal=True)
            counts_df = pd.DataFrame({"category": list(counts.keys()), "count": list(counts.values())})
            st.dataframe(counts_df, use_container_width=True, hide_index=True)

        st.write("")
        st.markdown('<div class="section-tag">Prompts per AI tool</div>', unsafe_allow_html=True)
        with st.container(border=True):
            tool_counts = lib.count_by_tool(prompts)
            static_bar_chart(list(tool_counts.keys()), list(tool_counts.values()), color="#00e5ff", horizontal=True)
            tool_df = pd.DataFrame({"ai_tool": list(tool_counts.keys()), "count": list(tool_counts.values())})
            st.dataframe(tool_df, use_container_width=True, hide_index=True)

elif page == "📈 Summary & Export":
    st.markdown('<div class="section-tag">Library summary</div>', unsafe_allow_html=True)
    summary = lib.library_summary(prompts)
    c1, c2, c3, c4 = st.columns(4)
    stat_tile(c1, summary["total_prompts"], "Total Prompts")
    stat_tile(c2, summary["total_categories"], "Categories")
    stat_tile(c3, summary["total_ai_tools"], "AI Tools")
    stat_tile(c4, summary["average_rating"], "Avg Rating")
    if summary["highest_rated"]:
        st.write("")
        st.write(f"🏆 Highest-rated prompt: **{summary['highest_rated']}**")

    st.write("")
    st.markdown('<div class="section-tag">Import / export</div>', unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇ Export library as JSON",
                data=lib.prompts_to_json(prompts),
                file_name="prompts_export.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            uploaded = st.file_uploader("⬆ Import prompts (JSON)", type="json")
            if uploaded is not None:
                import json as _json
                try:
                    imported_list = _json.load(uploaded)
                    added = lib.merge_imported(st.session_state.prompts, imported_list)
                    lib.save_prompts(st.session_state.prompts)
                    st.success(f"Imported {added} prompt(s).")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not import file: {exc}")
