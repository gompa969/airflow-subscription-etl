from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import json, os

# This is a sanitized, portfolio-friendly DAG that uses local JSON files
# instead of real company APIs or credentials.

DEFAULT_ARGS = {
    "owner": "portfolio_demo",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PLANS_PATH = os.path.join(DATA_DIR, "plans.json")
USER_SUBS_PATH = os.path.join(DATA_DIR, "user_subscriptions.json")


def _load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


with DAG(
    dag_id="subscription_flow_demo",
    default_args=DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    tags=["subscription", "demo", "airflow"],
    description="Sanitized demo of a subscription workflow with branching and mocked IO.",
) as dag:

    def validate_user_intent(**kwargs):
        # In production this comes from dag_run.conf; here we simulate defaults
        dag_conf = kwargs.get("dag_run").conf or {}
        ti = kwargs["ti"]

        user_id = int(dag_conf.get("user_id", 101))
        intent = dag_conf.get("intent", "create")  # create | change | cancel | view

        if intent not in ("create", "change", "cancel", "view"):
            raise ValueError("intent must be one of: create, change, cancel, view")

        ti.xcom_push(key="user_id", value=user_id)
        ti.xcom_push(key="intent", value=intent)

        if intent == "create":
            return "fetch_subscription_plans"
        elif intent == "change":
            return "fetch_available_subscription_plans"
        elif intent == "view":
            return "fetch_current_subscription"
        else:
            return "fetch_latest_active_subscription"

    def fetch_subscription_plans(**kwargs):
        plans = _load_json(PLANS_PATH)
        simplified = [{"subscription_plan_name": p["subscription_plan_name"], "subscription_plan_id": p["subscription_plan_id"]} for p in plans]
        ti = kwargs["ti"]
        ti.xcom_push(key="all_plans", value=plans)
        ti.xcom_push(key="plan_names_for_bot", value=simplified)
        ti.xcom_push(
    key="plan_names_with_price",
    value=[f"{p['subscription_plan_name']} - ${p['subscription_price']}" for p in plans],
)

    def fetch_user_current_plan(user_id: int):
        subs = _load_json(USER_SUBS_PATH)
        user_subs = [s for s in subs if int(s.get("user_id", 0)) == int(user_id)]
        active = [s for s in user_subs if s.get("subscription_status") == "active"]
        if not active:
            raise ValueError(f"No active subscription for user_id {user_id}")
        latest = max(active, key=lambda x: x.get("start_date", ""))
        return latest

    def fetch_available_subscription_plans(**kwargs):
        ti = kwargs["ti"]
        dag_conf = kwargs.get("dag_run").conf or {}
        user_id = int(ti.xcom_pull(key="user_id", task_ids="validate_user_intent") or dag_conf.get("user_id", 101))

        current = fetch_user_current_plan(user_id)
        plans = _load_json(PLANS_PATH)
        ti.xcom_push(key="all_plans", value=plans)
        ti.xcom_push(key="current_plan_name", value=str(next(p["subscription_plan_name"] for p in plans if p["subscription_plan_id"] == current["subscription_plan_id"])))
        ti.xcom_push(key="current_plan_price", value=float(next(p["subscription_price"] for p in plans if p["subscription_plan_id"] == current["subscription_plan_id"])))
        ti.xcom_push(key="current_plan_end_date", value=current.get("end_date"))
        ti.xcom_push(key="plan_names_for_bot", value=[{"subscription_plan_name": p["subscription_plan_name"], "subscription_plan_id": p["subscription_plan_id"]} for p in plans])
        ti.xcom_push(key="plan_names_with_price", value=[f"{p['subscription_plan_name']} - ${p['subscription_price']}" for p in plans])

    def fetch_current_subscription(**kwargs):
        ti = kwargs["ti"]
        dag_conf = kwargs.get("dag_run").conf or {}
        user_id = int(ti.xcom_pull(key="user_id", task_ids="validate_user_intent") or dag_conf.get("user_id", 101))
        current = fetch_user_current_plan(user_id)
        ti.xcom_push(key="active_subscription", value=current)

    def fetch_latest_active_subscription(**kwargs):
        # Same as fetch_current_subscription but kept separate for clarity/branch similarity
        return fetch_current_subscription(**kwargs)

    def send_plans_to_bot(**kwargs):
        # Demo: just log selected plan (if any) and push a default selection for the demo
        ti = kwargs["ti"]
        dag_conf = kwargs.get("dag_run").conf or {}
        intent = ti.xcom_pull(key="intent", task_ids="validate_user_intent") or dag_conf.get("intent", "create")

        selected_name = dag_conf.get("selected_plan_name") or "Pro"  # default pick
        ti.xcom_push(key="selected_plan_name", value=selected_name)

        # For "change" flow, we also expose current plan info for display
        if intent == "change":
            ti.xcom_push(key="current_plan_name_for_display", value=ti.xcom_pull(key="current_plan_name", task_ids="fetch_available_subscription_plans"))
            ti.xcom_push(key="current_plan_end_date_for_display", value=ti.xcom_pull(key="current_plan_end_date", task_ids="fetch_available_subscription_plans"))

    def calculate_price_difference(**kwargs):
        ti = kwargs["ti"]
        selected = ti.xcom_pull(key="selected_plan_name", task_ids="send_plans_to_bot")
        plans = ti.xcom_pull(key="all_plans", task_ids="fetch_available_subscription_plans")
        current_price = float(ti.xcom_pull(key="current_plan_price", task_ids="fetch_available_subscription_plans"))
        chosen = next((p for p in plans if p["subscription_plan_name"] == selected), None)
        if not chosen:
            raise ValueError(f"Selected plan not found: {selected}")
        price_diff = float(chosen["subscription_price"]) - current_price
        ti.xcom_push(key="price_difference", value=price_diff)

    def create_payment_for_create(**kwargs):
        # Simulate success
        kwargs["ti"].xcom_push(key="payment_status", value="Success")

    def create_payment_for_upgrade(**kwargs):
        kwargs["ti"].xcom_push(key="payment_status", value="Success")

    def process_subscription_selection(**kwargs):
        ti = kwargs["ti"]
        dag_conf = kwargs.get("dag_run").conf or {}
        intent = ti.xcom_pull(key="intent", task_ids="validate_user_intent") or dag_conf.get("intent", "create")
        user_id = int(ti.xcom_pull(key="user_id", task_ids="validate_user_intent") or dag_conf.get("user_id", 101))

        selected_name = ti.xcom_pull(key="selected_plan_name", task_ids="send_plans_to_bot")
        all_plans = ti.xcom_pull(key="all_plans", task_ids="fetch_subscription_plans") or ti.xcom_pull(key="all_plans", task_ids="fetch_available_subscription_plans")

        chosen = next((p for p in all_plans if p["subscription_plan_name"] == selected_name), None)
        if not chosen:
            raise ValueError("Selected plan not found")

        # Read subscriptions
        subs = _load_json(USER_SUBS_PATH)

        if intent == "create":
            # Create new subscription entry
            new_id = max([s["subscription_id"] for s in subs] + [1000]) + 1
            new_sub = {
                "subscription_id": new_id,
                "user_id": user_id,
                "subscription_plan_id": chosen["subscription_plan_id"],
                "subscription_status": "active",
                "start_date": chosen["subscription_plan_start_date"],
                "end_date": chosen["subscription_plan_end_date"],
                "payment_status": "Paid" if chosen["subscription_price"] > 0 else "Free",
            }
            subs.append(new_sub)
            _save_json(USER_SUBS_PATH, subs)
            ti.xcom_push(key="subscription_result", value=new_sub)

        elif intent == "change":
            # Update latest active subscription
            current = fetch_user_current_plan(user_id)
            current["subscription_plan_id"] = chosen["subscription_plan_id"]
            _save_json(USER_SUBS_PATH, subs)
            ti.xcom_push(key="subscription_result", value=current)

        elif intent == "cancel":
            current = fetch_user_current_plan(user_id)
            current["subscription_status"] = "inactive"
            _save_json(USER_SUBS_PATH, subs)
            ti.xcom_push(key="subscription_result", value=current)

        else:  # view
            current = fetch_user_current_plan(user_id)
            ti.xcom_push(key="subscription_result", value=current)

    def notify_user(**kwargs):
        ti = kwargs["ti"]
        intent = ti.xcom_pull(key="intent", task_ids="validate_user_intent")
        res = ti.xcom_pull(key="subscription_result", task_ids="process_subscription_selection") or \
              ti.xcom_pull(key="active_subscription", task_ids="fetch_current_subscription")
        print(f"[NOTIFY] Intent={intent} → Result: {json.dumps(res, indent=2)}")

    def route_after_bot(**kwargs):
        ti = kwargs["ti"]
        intent = ti.xcom_pull(key="intent", task_ids="validate_user_intent")
        if intent == "create":
            return "create_payment_for_create"
        elif intent == "change":
            return "calculate_price_difference"
        else:
            return "process_subscription_selection"

    validate_intent = BranchPythonOperator(task_id="validate_user_intent", python_callable=validate_user_intent)

    # Branch targets
    fetch_create = PythonOperator(task_id="fetch_subscription_plans", python_callable=fetch_subscription_plans)
    fetch_change = PythonOperator(task_id="fetch_available_subscription_plans", python_callable=fetch_available_subscription_plans)
    fetch_view   = PythonOperator(task_id="fetch_current_subscription", python_callable=fetch_current_subscription)
    fetch_cancel = PythonOperator(task_id="fetch_latest_active_subscription", python_callable=fetch_latest_active_subscription)

    send_to_bot  = PythonOperator(task_id="send_plans_to_bot", python_callable=send_plans_to_bot, trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    route_bot    = BranchPythonOperator(task_id="route_after_send_to_bot", python_callable=route_after_bot)
    calc_diff    = PythonOperator(task_id="calculate_price_difference", python_callable=calculate_price_difference, trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    pay_create   = PythonOperator(task_id="create_payment_for_create", python_callable=create_payment_for_create, trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    pay_upgrade  = PythonOperator(task_id="create_payment_for_upgrade", python_callable=create_payment_for_upgrade, trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    process_sel  = PythonOperator(task_id="process_subscription_selection", python_callable=process_subscription_selection, trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    notify       = PythonOperator(task_id="notify_user", python_callable=notify_user)

    # Graph
    validate_intent >> fetch_create >> send_to_bot
    validate_intent >> fetch_change >> send_to_bot
    validate_intent >> fetch_view >> notify
    validate_intent >> fetch_cancel >> process_sel >> notify

    send_to_bot >> route_bot
    route_bot >> pay_create >> process_sel >> notify
    route_bot >> calc_diff >> pay_upgrade >> process_sel
    route_bot >> process_sel
