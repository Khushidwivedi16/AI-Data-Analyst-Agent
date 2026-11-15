import time

from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq

from config import MAX_RETRIES, MODEL_NAME
from prompts import SYSTEM_PREFIX


def build_agent(db_path, api_key):
    db = SQLDatabase.from_uri(f"sqlite:///file:{db_path}?mode=ro&uri=true")
    llm = ChatGroq(groq_api_key=api_key, model=MODEL_NAME, temperature=0)
    return create_sql_agent(
        llm=llm,
        db=db,
        agent_type="tool-calling",
        prefix=SYSTEM_PREFIX,
        verbose=False,
        agent_executor_kwargs={"return_intermediate_steps": True},
    )


def extract_sql_queries(steps):
    queries = []
    for action, _observation in steps:
        if getattr(action, "tool", "") == "sql_db_query":
            tool_input = action.tool_input
            query = tool_input.get("query") if isinstance(tool_input, dict) else str(tool_input)
            if query:
                queries.append(query.strip())
    return queries


def ask_agent(agent, question):
    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = agent.invoke({"input": question})
            answer = response.get("output", "")
            if isinstance(answer, list):
                answer = " ".join(str(part) for part in answer)
            return {
                "answer": str(answer).strip(),
                "sql_queries": extract_sql_queries(response.get("intermediate_steps", [])),
                "error": False,
                "rate_limited": False,
            }
        except Exception as exc:
            last_error = str(exc)
            if "429" in last_error or "rate limit" in last_error.lower():
                return {
                    "answer": "The Groq free-tier token limit has been reached. Please wait a few minutes and try again.",
                    "sql_queries": [],
                    "error": True,
                    "rate_limited": True,
                }
            if attempt < MAX_RETRIES:
                time.sleep(2)
    return {
        "answer": f"The agent could not complete this request. Details: {last_error[:200]}",
        "sql_queries": [],
        "error": True,
        "rate_limited": False,
    }


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    from config import GROQ_API_KEY
    from data_loader import load_dataframe
    from db import new_db_path, remove_db, save_to_db

    df, _, _ = load_dataframe("datasets/superstore.csv")
    path = new_db_path()
    save_to_db(df, path)
    agent = build_agent(path, GROQ_API_KEY)
    result = ask_agent(agent, "Which region has the highest total sales?")
    print("ANSWER:", result["answer"])
    print("SQL:", result["sql_queries"])
    remove_db(path)