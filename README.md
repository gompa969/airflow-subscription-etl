# Subscription Workflow Orchestration with Apache Airflow (Portfolio Demo)

This project simulates a real-world **subscription lifecycle** using **Apache Airflow**.  
It demonstrates **branching workflows**, **ETL-style tasks**, **upgrade/downgrade pricing logic**, and **user notifications** using **mocked JSON data** (no confidential code or secrets).  

✅ Perfect for showcasing **Data Engineer** and **Business Systems Analyst** skills in workflow orchestration.

---

## ✨ Highlights
- **Intent-based routing**: `create`, `change`, `cancel`, `view`
- **Branching** with `BranchPythonOperator`
- **ETL-style I/O**: JSON files as stand-ins for APIs/DBs
- **Upgrade/downgrade logic**: price difference calculation
- **Simulated payments** + notifications (no external calls)
- **XCom usage** for passing state between tasks
- **Clear dependency graph** for each subscription path

---

## 🧱 Project Structure
airflow-subscription-etl/
├─ dags/
│  └─ subscription_flow_demo.py   # Main DAG
├─ data/
│  ├─ plans.json                  # Mock plan catalog
│  └─ user_subscriptions.json     # Mock subscription records
├─ .gitignore
├─ requirements.txt
└─ README.md
---

## 🚀 How to Run

> Airflow is typically deployed via **Docker** or in a **managed service**.  
> For portfolio/demo purposes, you can either run it locally or just showcase the DAG code and screenshots.

### Option A: Docker Compose (recommended)
Use the official Airflow docker-compose template and mount this repo’s `dags/` folder.  
📖 Docs: [Airflow + Docker Compose](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)

### Option B: Local Install (advanced)
Airflow requires pinned constraints. Example setup (Linux/macOS):

```bash
# Create environment
python3 -m venv .venv && source .venv/bin/activate
export AIRFLOW_VERSION=2.10.3
export PYTHON_VERSION=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")

# Install Airflow with constraints
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Install extras
pip install -r requirements.txt

# Set Airflow home
export AIRFLOW_HOME=$(pwd)

# Initialize database & create user
airflow db migrate
airflow users create --role Admin --username admin --password 1431 \
  --firstname Admin --lastname User --email admin@example.com

# Start services
airflow webserver --port 8080 &
airflow scheduler