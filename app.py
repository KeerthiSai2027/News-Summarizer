"""News Summarizer: Streamlit UI."""
import os
import streamlit as st
from dotenv import load_dotenv

import news
from summarizer import MODELS, load_summarizer, summarize

load_dotenv()
st.set_page_config(page_title="News Summarizer", page_icon="📰", layout="wide")


@st.cache_resource(show_spinner="Loading summarization model (first run downloads it)...")
def get_model(name):
    return load_summarizer(name)


@st.cache_data(ttl=600, show_spinner="Fetching news...")
def get_news(provider, key, query, category, country, count):
    if provider == "GNews":
        return news.fetch_gnews(key, query or None, category, country, max_results=count)
    return news.fetch_newsapi(key, query or None, category, country, max_results=count)


@st.cache_data(show_spinner=False)
def get_text(article_url, title, description, content):
    return news.get_full_text(
        {"url": article_url, "title": title, "description": description, "content": content})


# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    provider = st.radio("News provider", ["GNews", "NewsAPI"])
    env_key = os.getenv("GNEWS_API_KEY" if provider == "GNews" else "NEWSAPI_KEY", "")
    api_key = st.text_input("API key", value=env_key, type="password")

    query = st.text_input("Search topic (optional)", placeholder="e.g. AI, cricket, startups")
    category = st.selectbox(
        "Category", ["general", "business", "technology", "science", "health", "sports", "entertainment"])
    country = st.selectbox("Country", ["in", "us", "gb", "au", "ca"])
    count = st.slider("Number of articles", 3, 10, 5)

    st.divider()
    model_label = st.selectbox("Summarization model", list(MODELS))
    max_len = st.slider("Summary length (max tokens)", 60, 250, 130, step=10)

st.title("📰 News Summarizer")
st.caption("Fetches live headlines and summarizes them with a local Hugging Face model.")

if not api_key:
    st.info("Add your API key in the sidebar (or in a `.env` file) to get started.")
    st.stop()

try:
    articles = get_news(provider, api_key, query, category, country, count)
except Exception as e:
    st.error(f"Could not fetch news: {e}")
    st.stop()

if not articles:
    st.warning("No articles found. Try a different topic or category.")
    st.stop()

if "summaries" not in st.session_state:
    st.session_state.summaries = {}

# ---------- Articles ----------
for i, a in enumerate(articles):
    with st.container(border=True):
        img_col, text_col = st.columns([1, 3])
        if a["image"]:
            img_col.image(a["image"], use_container_width=True)
        text_col.subheader(a["title"])
        text_col.caption(f"{a['source']} · {a['published_at'][:10]}")
        text_col.write(a["description"])

        key = f"{a['url']}|{model_label}|{max_len}"
        b1, b2 = text_col.columns([1, 1])
        if b1.button("✨ Summarize", key=f"btn{i}"):
            with st.spinner("Reading and summarizing..."):
                text, full = get_text(a["url"], a["title"], a["description"], a["content"])
                if len(text.split()) < 30:
                    st.session_state.summaries[key] = ("Not enough article text available.", False)
                else:
                    model = get_model(MODELS[model_label])
                    st.session_state.summaries[key] = (
                        summarize(model, text, max_len=max_len, min_len=max_len // 3), full)
        b2.link_button("Read original ↗", a["url"])

        if key in st.session_state.summaries:
            summary, full = st.session_state.summaries[key]
            st.success(summary)
            if not full:
                st.caption("⚠️ Full article couldn't be scraped (paywall/blocked); summarized from the API snippet.")
