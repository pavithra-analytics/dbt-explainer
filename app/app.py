import streamlit as st
import requests
import yaml
import json
import toml
import os
from anthropic import Anthropic
from datetime import datetime

# ── Load config ────────────────────────────────────────────────────────────────

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.toml")
    try:
        return toml.load(config_path)
    except Exception as e:
        st.error(f"Could not load config.toml: {e}")
        st.stop()

def validate_config(config):
    required = ["name", "github_repo", "github_path"]
    missing = [k for k in required if not config.get("project", {}).get(k)]
    if missing:
        st.error(f"Missing required fields in config.toml: {', '.join(missing)}")
        st.stop()

# ── GitHub helpers ──────────────────────────────────────────────────────────────

def get_github_headers():
    token = st.secrets.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def get_file_sha(repo, path, headers):
    url = f"https://api.github.com/repos/{repo}/commits?path={path}&per_page=1"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and r.json():
            return r.json()[0]["sha"]
    except Exception:
        pass
    return None

def fetch_github_file(repo, path, headers):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            import base64
            return base64.b64decode(r.json()["content"]).decode("utf-8")
    except Exception:
        pass
    return None

def walk_repo_for_yamls(repo, base_path, headers):
    url = f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            tree = r.json().get("tree", [])
            return [
                f["path"] for f in tree
                if f["path"].startswith(base_path)
                and f["path"].endswith(".yml")
                and "models" in f["path"]
            ]
    except Exception:
        pass
    return []

# ── Context builder ─────────────────────────────────────────────────────────────

def build_context(repo, github_path, headers):
    context = {"models": {}, "sources": [], "mode": "full"}

    # Try manifest.json first
    manifest_path = f"{github_path}/target/manifest.json"
    manifest_raw = fetch_github_file(repo, manifest_path, headers)

    if manifest_raw:
        try:
            manifest = json.loads(manifest_raw)
            nodes = manifest.get("nodes", {})
            for node_id, node in nodes.items():
                if node.get("resource_type") == "model":
                    context["models"][node["name"]] = {
                        "name": node["name"],
                        "description": node.get("description", ""),
                        "columns": {
                            col: meta.get("description", "")
                            for col, meta in node.get("columns", {}).items()
                        },
                        "depends_on": node.get("depends_on", {}).get("nodes", []),
                        "tags": node.get("tags", []),
                    }
            return context
        except Exception:
            pass

    # Fallback — read schema yml files directly
    context["mode"] = "documentation-only"
    yaml_paths = walk_repo_for_yamls(repo, github_path, headers)

    for ypath in yaml_paths:
        raw = fetch_github_file(repo, ypath, headers)
        if not raw:
            continue
        try:
            parsed = yaml.safe_load(raw)
            if not parsed:
                continue
            for model in parsed.get("models", []):
                context["models"][model["name"]] = {
                    "name": model["name"],
                    "description": model.get("description", ""),
                    "columns": {
                        col["name"]: col.get("description", "")
                        for col in model.get("columns", [])
                    },
                    "depends_on": [],
                    "tags": [],
                }
            for source in parsed.get("sources", []):
                for tbl in source.get("tables", []):
                    context["sources"].append({
                        "source": source["name"],
                        "table": tbl["name"],
                        "description": tbl.get("description", ""),
                    })
        except Exception:
            continue

    return context

def extract_relevant_context(question, context):
    question_lower = question.lower()
    matched = {}

    for name, model in context["models"].items():
        if name.lower() in question_lower or any(
            word in question_lower
            for word in name.lower().replace("_", " ").split()
            if len(word) > 3
        ):
            matched[name] = model
            for dep in model.get("depends_on", []):
                dep_name = dep.split(".")[-1]
                if dep_name in context["models"]:
                    matched[dep_name] = context["models"][dep_name]

    if not matched:
        matched = context["models"]

    summary = []
    for name, model in matched.items():
        cols = "\n".join(
            f"    - {col}: {desc}" for col, desc in model["columns"].items()
        ) or "    (no column descriptions)"
        summary.append(
            f"Model: {name}\nDescription: {model['description'] or 'none'}\nColumns:\n{cols}"
        )

    if context["sources"]:
        for s in context["sources"]:
            summary.append(
                f"Source: {s['source']}.{s['table']}\nDescription: {s['description'] or 'none'}"
            )

    mode_note = ""
    if context["mode"] == "documentation-only":
        mode_note = "\n\nNote: Running in documentation-only mode (manifest.json not found). Answers are based on schema documentation only."

    return "\n\n".join(summary) + mode_note

# ── Cache with SHA check ────────────────────────────────────────────────────────

def load_project_context(repo, github_path, headers):
    current_sha = get_file_sha(repo, github_path, headers)

    if (
        "context" in st.session_state
        and "context_sha" in st.session_state
        and st.session_state["context_sha"] == current_sha
        and current_sha is not None
    ):
        return st.session_state["context"], False  # False = not refreshed

    context = build_context(repo, github_path, headers)
    st.session_state["context"] = context
    st.session_state["context_sha"] = current_sha
    return context, True  # True = freshly loaded

# ── Claude API ──────────────────────────────────────────────────────────────────

def ask_claude(question, context, conversation_history, project_name):
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not found in Streamlit secrets.")
        st.stop()

    client = Anthropic(api_key=api_key)
    relevant = extract_relevant_context(question, context)

    system_prompt = f"""You are a helpful data assistant for the {project_name} project built with dbt.
Your job is to answer questions from non-technical business users about the data — what it means, where numbers come from, how things are defined, and how models relate to each other.

Answer in plain English. Never use technical jargon unless the user asks for it. Be concise and direct.
If you are not sure about something, say so clearly rather than guessing.
Always ground your answers in the dbt project documentation provided below.

dbt project context:
{relevant}"""

    messages = conversation_history + [{"role": "user", "content": question}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Something went wrong when contacting the AI: {e}"

# ── Main app ────────────────────────────────────────────────────────────────────

def main():
    config = load_config()
    validate_config(config)

    project = config["project"]
    project_name = project["name"]
    github_repo = project["github_repo"]
    github_path = project["github_path"]

    st.set_page_config(
        page_title=project_name,
        page_icon="📊",
        layout="centered",
    )

    # Custom CSS
    st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { max-width: 780px; margin: 0 auto; }
    .stChatMessage { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

    headers = get_github_headers()

    # Load context with SHA check
    with st.spinner("Connecting to your dbt project..."):
        context, refreshed = load_project_context(github_repo, github_path, headers)

    model_count = len(context["models"])
    mode = context["mode"]

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {project_name}")
        if mode == "documentation-only":
            st.caption(f"{model_count} models · documentation mode · synced just now")
        else:
            st.caption(f"{model_count} models · fully synced · up to date")
    with col2:
        if st.button("New conversation", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()

    st.divider()

    # Init conversation
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Suggested questions on empty state
    if not st.session_state["messages"]:
        st.markdown("**What would you like to know?**")
        suggestions = [
            "What data is available in this project?",
            "Where does the revenue number come from?",
            "What does loyal customer mean?",
            "Is an order considered late if it arrives one day after the estimate?",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, use_container_width=True, key=f"sug_{i}"):
                st.session_state["pending_question"] = s
                st.rerun()

    # Render conversation history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle pending suggestion click
    if "pending_question" in st.session_state:
        question = st.session_state.pop("pending_question")
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state["messages"].append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            with st.spinner(""):
                answer = ask_claude(
                    question,
                    context,
                    [m for m in st.session_state["messages"][:-1]],
                    project_name,
                )
            st.markdown(answer)
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.rerun()

    # Chat input
    if question := st.chat_input("Ask anything about your data..."):
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state["messages"].append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            with st.spinner(""):
                answer = ask_claude(
                    question,
                    context,
                    [m for m in st.session_state["messages"][:-1]],
                    project_name,
                )
            st.markdown(answer)
        st.session_state["messages"].append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()