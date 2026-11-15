import logging
from datetime import datetime


def get_logger(name="ai_data_analyst"):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger(name)


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def history_to_markdown(history, dataset_name):
    lines = [f"# Analysis session: {dataset_name}", f"_Exported {timestamp()}_", ""]
    for i, item in enumerate(history, 1):
        lines.append(f"## Q{i}. {item['question']}")
        lines.append(item["answer"])
        if item["sql_queries"]:
            lines.append("")
            lines.append("```sql")
            lines.append(item["sql_queries"][-1])
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _nice(column):
    return column.replace("_", " ")


def suggest_questions(df):
    skip_tokens = {"id", "code", "zip", "postal", "index", "row"}
    numeric = [
        c for c in df.select_dtypes(include="number").columns
        if not (set(c.split("_")) & skip_tokens)
    ]
    categorical = [
        c for c in df.select_dtypes(include="object").columns
        if 2 <= df[c].nunique() <= 30
    ]
    questions = ["How many rows are in the dataset?"]
    if numeric:
        questions.append(f"What is the total {_nice(numeric[0])}?")
    if numeric and categorical:
        questions.append(f"Which {_nice(categorical[0])} has the highest total {_nice(numeric[0])}?")
        second = numeric[1] if len(numeric) > 1 else numeric[0]
        questions.append(f"What is the average {_nice(second)} for each {_nice(categorical[0])}?")
    return questions[:4]