import html
import json

import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = "http://127.0.0.1:8000"
MAX_CHARS = 5000
AUTO = "Auto Detect"

st.set_page_config(page_title="Language Translator", page_icon="🌐", layout="centered")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; max-width: 900px; }
    .hero {
        text-align: center;
        padding: 1.8rem 1rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        margin-bottom: 1.6rem;
    }
    .hero h1 { margin: 0; font-size: 2.1rem; color: white; }
    .hero p { margin: 0.4rem 0 0; color: rgba(255, 255, 255, 0.9); }
    div.stButton > button { border-radius: 12px; font-weight: 600; height: 3rem; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5, #06b6d4);
        border: none;
        color: white;
    }
    .result-box {
        padding: 1rem 1.2rem;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.35);
        background: rgba(128, 128, 128, 0.08);
        font-size: 1.15rem;
        line-height: 1.7;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin-bottom: 0.8rem;
    }
    textarea { font-size: 1.05rem !important; }
    </style>
    <div class="hero">
        <h1>🌐 Language Translator</h1>
        <p>Translate text, copy it, and listen to it.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_languages():
    response = requests.get(f"{API_URL}/languages", timeout=15)
    response.raise_for_status()
    return response.json()["languages"]


def error_detail(response):
    try:
        return str(response.json().get("detail", "Unknown error"))
    except ValueError:
        return f"Unexpected response ({response.status_code})"


def call_translate(text, source, target):
    response = requests.post(
        f"{API_URL}/translate",
        json={"text": text, "source": source, "target": target},
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(error_detail(response))
    return response.json()["translated_text"]


def call_tts(text, lang):
    response = requests.post(
        f"{API_URL}/tts", json={"text": text, "lang": lang}, timeout=30
    )
    if response.status_code != 200:
        raise RuntimeError(error_detail(response))
    return response.content


def swap_languages():
    source = st.session_state.source_lang
    target = st.session_state.target_lang
    if source == AUTO:
        return
    st.session_state.source_lang = target
    st.session_state.target_lang = source


def copy_button(text):
    payload = json.dumps(text).replace("</", "<\\/")
    components.html(
        f"""
        <style>
        html, body {{ margin: 0; padding: 0; background: transparent; }}
        button {{
            width: 100%;
            height: 48px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            font-family: "Source Sans Pro", sans-serif;
            color: white;
            cursor: pointer;
            background: linear-gradient(135deg, #4f46e5, #06b6d4);
        }}
        button:hover {{ opacity: 0.9; }}
        </style>
        <button id="copy">📋 Copy</button>
        <script>
        const text = {payload};
        const btn = document.getElementById("copy");
        btn.addEventListener("click", async () => {{
            let ok = false;
            try {{
                await navigator.clipboard.writeText(text);
                ok = true;
            }} catch (e) {{
                const area = document.createElement("textarea");
                area.value = text;
                document.body.appendChild(area);
                area.select();
                try {{ ok = document.execCommand("copy"); }} catch (e2) {{}}
                document.body.removeChild(area);
            }}
            btn.textContent = ok ? "✅ Copied!" : "❌ Copy failed";
            setTimeout(() => {{ btn.textContent = "📋 Copy"; }}, 1500);
        }});
        </script>
        """,
        height=50,
    )


try:
    languages = load_languages()
except requests.exceptions.RequestException:
    st.error(
        "Backend is not reachable. Start it with: uvicorn backend.main:app --reload"
    )
    st.stop()

name_to_code = {name.title(): code for name, code in languages.items()}
names = sorted(name_to_code)

if "source_lang" not in st.session_state:
    st.session_state.source_lang = AUTO
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "Bengali" if "Bengali" in name_to_code else names[0]
st.session_state.setdefault("result", None)
st.session_state.setdefault("audio", None)

col_from, col_swap, col_to = st.columns([5, 1, 5])
with col_from:
    st.selectbox("From", [AUTO] + names, key="source_lang")
with col_swap:
    st.markdown("<div style='height: 1.9rem'></div>", unsafe_allow_html=True)
    st.button(
        "⇄",
        on_click=swap_languages,
        disabled=st.session_state.source_lang == AUTO,
        use_container_width=True,
        help="Swap languages",
    )
with col_to:
    st.selectbox("To", names, key="target_lang")

text = st.text_area(
    "Enter text",
    height=200,
    max_chars=MAX_CHARS,
    placeholder="Type or paste your text here...",
    key="input_text",
)
st.caption(f"{len(text)} / {MAX_CHARS} characters")

translate_clicked = st.button("Translate", type="primary", use_container_width=True)

if translate_clicked:
    source = st.session_state.source_lang
    target = st.session_state.target_lang
    source_code = "auto" if source == AUTO else name_to_code[source]
    target_code = name_to_code[target]

    if not text.strip():
        st.warning("Please enter some text first.")
    elif source_code == target_code:
        st.warning("Source and target languages must be different.")
    else:
        with st.spinner("Translating..."):
            try:
                translated = call_translate(text, source_code, target_code)
                st.session_state.result = {"text": translated, "lang": target_code}
                st.session_state.audio = None
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
            except RuntimeError as e:
                st.error(str(e))

result = st.session_state.result
if result:
    st.markdown("#### Translation")
    st.markdown(
        f"<div class='result-box'>{html.escape(result['text'])}</div>",
        unsafe_allow_html=True,
    )

    col_copy, col_listen = st.columns(2)
    with col_copy:
        copy_button(result["text"])
    with col_listen:
        listen_clicked = st.button("🔊 Listen", use_container_width=True)

    if listen_clicked:
        with st.spinner("Generating audio..."):
            try:
                st.session_state.audio = call_tts(result["text"], result["lang"])
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
            except RuntimeError as e:
                st.error(str(e))

    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mpeg")