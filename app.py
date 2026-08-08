import streamlit as st
import pandas as pd

import prompt_library as lib

st.set_page_config(page_title="AI Prompt Library Manager", page_icon="📚", layout="wide")

if "prompts" not in st.session_state:
    st.session_state.prompts = lib.load_prompts()


def to_df(prompts):
    return pd.DataFrame(prompts)[
        ["id", "title", "category", "ai_tool", "rating", "date_added", "text"]
    ]


st.title("📚 AI Prompt Library Manager")
st.caption("Manage, search, and explore a collection of AI prompts.")

page = st.sidebar.radio(
    "Navigate",
    [
        "View Prompts",
        "Search",
        "Add Prompt",
        "Highest Rated",
        "Category Counts",
        "Summary",
    ],
)

prompts = st.session_state.prompts

if page == "View Prompts":
    st.subheader("All Prompts")
    if not prompts:
        st.info("No prompts yet. Add one from the 'Add Prompt' page.")
    else:
        st.dataframe(to_df(prompts), use_container_width=True, hide_index=True)

elif page == "Search":
    st.subheader("Search Prompts")
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category", ["Any"] + lib.categories(prompts)
        )
    with col2:
        ai_tool = st.selectbox("AI Tool", ["Any"] + lib.ai_tools(prompts))

    results = lib.search_prompts(
        prompts,
        category=None if category == "Any" else category,
        ai_tool=None if ai_tool == "Any" else ai_tool,
    )
    st.write(f"**{len(results)}** matching prompt(s)")
    if results:
        st.dataframe(to_df(results), use_container_width=True, hide_index=True)

elif page == "Add Prompt":
    st.subheader("Add a New Prompt")
    with st.form("add_prompt_form", clear_on_submit=True):
        title = st.text_input("Title")
        text = st.text_area("Prompt Text", height=120)
        category = st.text_input("Category (e.g. Writing, Coding)")
        ai_tool = st.text_input("AI Tool (e.g. ChatGPT, Claude)")
        rating = st.slider("Rating", 0.0, 5.0, 4.0, 0.1)
        submitted = st.form_submit_button("Add Prompt")

    if submitted:
        if not title or not text or not category or not ai_tool:
            st.error("Please fill in all fields before submitting.")
        else:
            new_prompt = lib.add_prompt(
                st.session_state.prompts, title, text, category, ai_tool, rating
            )
            lib.save_prompts(st.session_state.prompts)
            st.success(f"Added prompt '{new_prompt['title']}' (id {new_prompt['id']}).")

elif page == "Highest Rated":
    st.subheader("Highest-Rated Prompt")
    top = lib.highest_rated_prompt(prompts)
    if not top:
        st.info("No prompts available yet.")
    else:
        st.metric("Rating", top["rating"])
        st.markdown(f"**{top['title']}** · {top['category']} · {top['ai_tool']}")
        st.code(top["text"])

elif page == "Category Counts":
    st.subheader("Prompts per Category")
    counts = lib.count_by_category(prompts)
    if not counts:
        st.info("No prompts available yet.")
    else:
        counts_df = pd.DataFrame(
            {"category": list(counts.keys()), "count": list(counts.values())}
        )
        st.bar_chart(counts_df.set_index("category"))
        st.dataframe(counts_df, use_container_width=True, hide_index=True)

elif page == "Summary":
    st.subheader("Library Summary")
    summary = lib.library_summary(prompts)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Prompts", summary["total_prompts"])
    c2.metric("Categories", summary["total_categories"])
    c3.metric("AI Tools", summary["total_ai_tools"])
    c4.metric("Avg Rating", summary["average_rating"])
    if summary["highest_rated"]:
        st.write(f"🏆 Highest-rated prompt: **{summary['highest_rated']}**")
