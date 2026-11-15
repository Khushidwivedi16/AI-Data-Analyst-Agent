AI Data Analyst Agent



An LLM-powered data analytics application that allows users to ask questions about structured CSV and Excel datasets in plain English and receive data-driven answers using SQL.



Live Demo: Coming soon — add your Streamlit deployment link here.



Project Overview



The AI Data Analyst Agent converts natural-language questions into SQL queries using a Groq-powered LLM and LangChain.



It loads structured datasets, creates a SQLite database, generates SQL queries, executes them, and presents the results through an interactive Streamlit interface.



Architecture



flowchart TD

&#x20;   A\[CSV / Excel Dataset] --> B\[data\_loader.py]

&#x20;   B --> C\[Data Cleaning]

&#x20;   C --> D\[SQLite Database]

&#x20;   E\[User Question in Plain English] --> F\[AI Agent]

&#x20;   F --> G\[Groq LLM + LangChain]

&#x20;   D --> F

&#x20;   G --> H\[SQL Query Generation]

&#x20;   H --> I\[SQL Validation]

&#x20;   I --> J\[Query Execution]

&#x20;   J --> K\[Results and Visualization]

&#x20;   K --> L\[Streamlit Dashboard]



Key Features



\- Upload and analyze structured datasets.

\- Ask questions using natural language.

\- Automatically generate SQL queries.

\- Execute queries using SQLite.

\- Integrate Groq LLM with LangChain.

\- Display generated SQL queries and analytical results.

\- Interactive data visualization.

\- SQL validation and query safety mechanisms.



Technology Stack



Technology| Purpose

Python| Core programming

Pandas| Data processing

SQLite| Database management

LangChain| AI agent framework

Groq API| LLM integration

Streamlit| Web application

Plotly| Data visualization



Project Structure



AI-Data-Analyst-Agent/

│

├── app.py

├── ai\_agent.py

├── config.py

├── data\_loader.py

├── db.py

├── prompts.py

├── utils.py

├── visualization.py

├── requirements.txt

│

├── Streamlit/

│   └── config.toml

│

├── datasets/

│   └── Sample - Superstore.csv

│

└── eval/

&#x20;   └── test\_questions.txt



How to Run Locally



1\. Clone the repository



git clone https://github.com/YOUR\_USERNAME/ai-data-analyst-agent.git



2\. Navigate to the project folder



cd ai-data-analyst-agent



3\. Install dependencies



pip install -r requirements.txt



4\. Configure the Groq API key



Create a ".env" file in the project root:



GROQ\_API\_KEY=your\_actual\_api\_key



Never upload your ".env" file or API key to GitHub.



5\. Run the application



streamlit run app.py



Dataset



The project currently uses the Sample Superstore dataset for testing and data analysis.



Evaluation



The project includes an evaluation module and test questions to assess natural-language-to-SQL performance.



Detailed evaluation results will be added after verification.



Limitations



\- Designed for structured, tabular datasets.

\- LLM API usage is subject to Groq rate limits.

\- Generated SQL and analytical results should be validated for critical business decisions.

\- Performance depends on dataset quality and complexity.



Future Enhancements



\- Support for additional file formats.

\- Improved SQL generation and error handling.

\- Advanced interactive visualizations.

\- More comprehensive evaluation and testing.



Author



Khushi Dwivedi



B.Tech Computer Science and Engineering



Project: AI Data Analyst Agent — Natural Language to SQL Analytics Platform

