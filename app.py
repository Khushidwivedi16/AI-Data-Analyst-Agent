import os

import streamlit as st

st.set_page_config(page_title="AI Data Analyst Agent", page_icon="📊", layout="wide")
try:
    st.write(
        "DEBUG - GROQ_API_KEY exists in Streamlit Secrets:",
        "GROQ_API_KEY" in st.secrets
    )
except Exception as e:
    st.error(f"Secrets access error: {e}")

from ai_agent import ask_agent, build_agent
from config import DATASETS_DIR, GROQ_API_KEY
from data_loader import get_excel_sheets, load_dataframe, profile_report
from db import new_db_path, remove_db, run_query, save_to_db
from utils import df_to_csv_bytes, history_to_markdown, suggest_questions
from visualization import distribution_chart, result_chart, top_categories_chart

CSS = """
<style>
.hero {background: linear-gradient(135deg, #6C63FF 0%, #3F8EFC 100%); padding: 1.8rem 2.2rem;
       border-radius: 18px; margin-bottom: 1.2rem;}
.hero h1, .hero p {color: white !important; margin: 0;}
.hero h1 {font-size: 2.1rem;}
.hero p {margin-top: .4rem; font-size: 1.05rem; opacity: .95;}
.card {background: #F5F6FF; border: 1px solid #E3E5FF; border-radius: 14px; padding: 1rem 1.2rem; height: 100%;}
.card h4 {margin: 0 0 .3rem 0;}
.badge {display: inline-block; padding: .15rem .65rem; border-radius: 999px; background: #EEF0FF;
        color: #4B45D6; font-size: .82rem; margin-right: .4rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>📊 AI Data Analyst Agent</h1>'
    "<p>Upload any structured dataset and ask questions in plain English. "
    "The agent writes SQL, runs it on your data and shows its work.</p></div>",
    unsafe_allow_html=True,
)

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to your .env file (local) or to Streamlit secrets (deployed).")
    st.stop()


def fresh_state():
    return {
        "df": None, "profile": None, "clean_log": [], "db_path": None,
        "agent": None, "source_key": None, "source_name": "", "history": [],
    }


for key, value in fresh_state().items():
    st.session_state.setdefault(key, value)


def reset_state():
    remove_db(st.session_state.get("db_path"))
    for key, value in fresh_state().items():
        st.session_state[key] = value


def list_samples():
    if not os.path.isdir(DATASETS_DIR):
        return []
    return sorted(f for f in os.listdir(DATASETS_DIR) if f.lower().endswith((".csv", ".xlsx", ".xls")))


NO_SAMPLE = "-- none --"

with st.sidebar:
    st.header("1. Load your data")
    uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])
    sample_choice = st.selectbox("...or try a sample dataset", [NO_SAMPLE] + list_samples())
    st.divider()
    st.subheader("Built-in safeguards")
    st.markdown(
        "- Read-only database: the agent cannot change your data\n"
        "- Answers come from executed SQL, not guesses\n"
        "- Says so when the data cannot answer a question\n"
        "- Every generated SQL query is shown for checking"
    )

source, source_name, sheet = None, None, 0
if uploaded is not None:
    source, source_name = uploaded, uploaded.name
elif sample_choice != NO_SAMPLE:
    source, source_name = os.path.join(DATASETS_DIR, sample_choice), sample_choice

if source is not None:
    if source_name.lower().endswith((".xlsx", ".xls")):
        try:
            sheets = get_excel_sheets(source)
        except Exception as err:
            st.sidebar.error(f"Could not read this Excel file: {err}")
            sheets = [0]
        sheet = st.sidebar.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]

    full_key = f"{source_name}|{getattr(source, 'size', 0)}|{sheet}"
    if st.session_state.source_key != full_key:
        with st.spinner("Cleaning your data and building the database..."):
            try:
                df, clean_log, stats = load_dataframe(source, sheet_name=sheet)
                if df.empty or df.shape[1] == 0:
                    raise ValueError("The file has no usable rows.")
                remove_db(st.session_state.db_path)
                db_path = new_db_path()
                save_to_db(df, db_path)
                st.session_state.update({
                    "df": df, "profile": profile_report(df, stats), "clean_log": clean_log,
                    "db_path": db_path, "agent": build_agent(db_path, GROQ_API_KEY),
                    "source_key": full_key, "source_name": source_name, "history": [],
                })
            except Exception as err:
                st.sidebar.error(f"Could not load this file: {err}")
                reset_state()
elif st.session_state.df is not None:
    reset_state()

df = st.session_state.df

if df is None:
    st.info("👈 Upload a file or pick a sample dataset from the sidebar to begin.")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="card"><h4>1. Upload</h4>CSV or Excel. Column names are cleaned automatically and a data-quality report is generated.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="card"><h4>2. Ask</h4>Type a business question in plain English. No SQL knowledge needed.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="card"><h4>3. Verify</h4>See the exact SQL the agent ran, the result table and an auto-generated chart.</div>', unsafe_allow_html=True)
    st.stop()

profile = st.session_state.profile
st.markdown(
    f'<span class="badge">📁 {st.session_state.source_name}</span>'
    f'<span class="badge">{profile["rows"]:,} rows</span>'
    f'<span class="badge">{profile["columns"]} columns</span>',
    unsafe_allow_html=True,
)

tab_ask, tab_overview, tab_data = st.tabs(["💬 Ask the agent", "📈 Overview", "🗂️ Data preview"])


def handle_question(question):
    with st.spinner("The agent is inspecting the schema and writing SQL..."):
        result = ask_agent(st.session_state.agent, question)
    result_df = None
    if result["sql_queries"]:
        try:
            result_df = run_query(st.session_state.db_path, result["sql_queries"][-1])
        except Exception:
            result_df = None
    st.session_state.history.append({
        "question": question, "answer": result["answer"],
        "sql_queries": result["sql_queries"], "result_df": result_df, "error": result["error"],
    })


with tab_ask:
    question = None
    suggestions = suggest_questions(df)
    st.caption("Try a suggested question or type your own:")
    cols = st.columns(len(suggestions))
    for i, text in enumerate(suggestions):
        if cols[i].button(text, key=f"suggestion_{i}", use_container_width=True):
            question = text

    with st.form("ask_form", clear_on_submit=True):
        typed = st.text_input("Ask a question about your data", placeholder="e.g. Which category has the highest total sales?")
        submitted = st.form_submit_button("Ask", type="primary")
    if submitted and typed.strip():
        question = typed.strip()

    if question:
        handle_question(question)

    history = st.session_state.history
    for index, item in enumerate(reversed(history)):
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            if item["error"]:
                st.warning(item["answer"])
            else:
                st.write(item["answer"])
            if item["sql_queries"]:
                with st.expander("🔍 View the SQL the agent ran"):
                    st.code(item["sql_queries"][-1], language="sql")
            result_df = item["result_df"]
            if result_df is not None and not result_df.empty:
                st.dataframe(result_df, use_container_width=True, hide_index=True)
                fig = result_chart(result_df)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{index}")

    if history:
        st.download_button(
            "⬇️ Download this session (Markdown)",
            history_to_markdown(history, st.session_state.source_name),
            file_name="analysis_session.md",
        )

with tab_overview:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{profile['rows']:,}")
    m2.metric("Columns", profile["columns"])
    m3.metric("Missing cells", f"{profile['missing_pct']}%")
    m4.metric("Duplicates removed", f"{profile['duplicates_removed']:,}")

    with st.expander("🧹 Cleaning log (everything done to your data)", expanded=True):
        for line in st.session_state.clean_log:
            st.write("• " + line)

    st.subheader("Column profile")
    st.dataframe(profile["column_table"], use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    numeric_cols = profile["numeric_cols"]
    category_cols = [c for c in profile["categorical_cols"] if df[c].nunique() <= 200]
    if numeric_cols:
        with left:
            dist_col = st.selectbox("Numeric column", numeric_cols, key="dist_col")
            st.plotly_chart(distribution_chart(df, dist_col), use_container_width=True)
    if numeric_cols and category_cols:
        with right:
            cat_col = st.selectbox("Group by", category_cols, key="cat_col")
            val_col = st.selectbox("Sum of", numeric_cols, key="val_col")
            st.plotly_chart(top_categories_chart(df, cat_col, val_col), use_container_width=True)

with tab_data:
    st.dataframe(df.head(200), use_container_width=True)
    st.download_button("⬇️ Download cleaned data (CSV)", df_to_csv_bytes(df), file_name="cleaned_data.csv")

st.divider()
st.caption("Built with LangChain, Groq and Streamlit. A bounded agentic Text-to-SQL analytics prototype.")
