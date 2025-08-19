
# Subscription Workflow Orchestration with Apache Airflow (Portfolio Demo)

This project simulates a real-world **subscription lifecycle** using **Apache Airflow**. The DAG demonstrates
**branching workflows**, **ETL-style tasks**, **upgrade/downgrade pricing logic**, and **user notifications** using
**mocked data** (no confidential company code or secrets). Perfect for showcasing **Data Engineer / Business Systems Analyst** skills.

## ✨ What it shows
- Intent routing: `create`, `change`, `cancel`, `view`
- Branching with `BranchPythonOperator`
- Reading/writing JSON as stand-in for APIs/DBs
- Upgrade/downgrade price difference calculation
- Simulated payment + notifications (no external calls)
- XCom usage and clear task dependencies

## 🧱 Project structure
```
airflow-subscription-etl/
├─ dags/
│  └─ subscription_flow.py
├─ data/
│  ├─ plans.json
│  └─ user_subscriptions.json
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 🚀 How to run locally (quick demo)
> Airflow is usually run via Docker or a managed environment. For a quick portfolio, you can simply show the code,
> graph view screenshots, and README. If you want to run it:

### Option A: Docker Compose (recommended if you already use Docker)
Use the official Airflow docker-compose template and mount this repo's `dags/` into the container.
Docs: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

### Option B: Local install (advanced users)
Airflow requires constraints. Example (Linux/macOS):

```bash
python -m venv .venv && source .venv/bin/activate
export AIRFLOW_VERSION=2.9.2
export PYTHON_VERSION=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install -r requirements.txt
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --role Admin --username admin --password admin --firstname Admin --lastname User --email admin@example.com
airflow webserver --port 8080 &
airflow scheduler
```

Then copy this repo into `$AIRFLOW_HOME/dags` or set `dags_folder` to this repo's `dags/`.

## 🔐 No secrets policy
This repo uses **mock JSON files** and **environment variables** (see `.env.example`). Do **not** commit real API keys or credentials.

## 📝 Notes for recruiters
This is a **simulated** but realistic orchestration project based on common subscription flows (create/change/cancel/view),
implemented in Airflow to demonstrate data engineering and business-systems thinking.
