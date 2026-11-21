"""Local abstractive summarization with a Hugging Face model."""
from transformers import pipeline

MODELS = {
    "DistilBART (fast)": "sshleifer/distilbart-cnn-12-6",
    "BART Large (best quality, slower)": "facebook/bart-large-cnn",
}


def load_summarizer(model_name):
    return pipeline("summarization", model=model_name)


def _chunk(text, max_words=600):
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def _run(summarizer, text, max_len, min_len):
    n_words = len(text.split())
    max_len = min(max_len, max(20, int(n_words * 0.7)))
    min_len = min(min_len, max_len - 5)
    out = summarizer(text, max_length=max_len, min_length=min_len,
                     do_sample=False, truncation=True)
    return out[0]["summary_text"]


def summarize(summarizer, text, max_len=130, min_len=40):
    """Summarize text of any length by chunking, then condensing the chunk summaries."""
    text = " ".join(text.split())
    if len(text.split()) < 50:
        return text  # too short to summarize

    parts = [_run(summarizer, c, max_len, min_len) for c in _chunk(text)]
    combined = " ".join(parts)
    if len(parts) > 1:
        combined = _run(summarizer, combined, max_len, min_len)
    return combined
