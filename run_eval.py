import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from ai_agent import ask_agent, build_agent
from config import GROQ_API_KEY
from data_loader import load_dataframe
from db import new_db_path, remove_db, save_to_db

DATASET = "datasets/superstore.csv"
QUESTIONS_FILE = "eval/test_questions.txt"
REPORT_FILE = "eval/eval_report.md"
DELAY_SECONDS = 6


def parse_questions(path):
    items = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = re.match(r"^\d+\.\s*\[(.+?)\]\s*(.+)$", line.strip())
            if match:
                items.append((match.group(1), match.group(2)))
    return items


def main():
    df, _, _ = load_dataframe(DATASET)
    db_path = new_db_path()
    save_to_db(df, db_path)
    agent = build_agent(db_path, GROQ_API_KEY)

    questions = parse_questions(QUESTIONS_FILE)
    results = []
    for number, (tier, question) in enumerate(questions, 1):
        print(f"[{number}/{len(questions)}] ({tier}) {question}")
        result = ask_agent(agent, question)
        if result["rate_limited"]:
            print("Groq rate limit reached. Stopping early. Run again later.")
            break
        results.append((number, tier, question, result))
        print("  ->", result["answer"], "\n")
        time.sleep(DELAY_SECONDS)

    with open(REPORT_FILE, "w", encoding="utf-8") as handle:
        handle.write(f"# Evaluation Report\n\nDataset: `{DATASET}`\n\n")
        handle.write(f"Questions completed: {len(results)} of {len(questions)}\n\n---\n\n")
        for number, tier, question, result in results:
            handle.write(f"### Q{number} [{tier}] {question}\n\n")
            handle.write(f"**Agent answer:** {result['answer']}\n\n")
            if result["sql_queries"]:
                handle.write("**SQL:**\n```sql\n" + result["sql_queries"][-1] + "\n```\n\n")
            handle.write("**Verdict (fill in manually):** [ ] Correct  [ ] Wrong  [ ] Guardrail OK  [ ] Hallucinated\n\n---\n\n")
    remove_db(db_path)
    print(f"Done. Report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()