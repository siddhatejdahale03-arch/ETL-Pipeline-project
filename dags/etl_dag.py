"""
Airflow DAG: runs the whole ETL pipeline once a day at 02:00 UTC.

It is ONE task that calls run_pipeline(). Extract, transform and load all
happen inside that function (load = Rohan's DBLoader).
If the task fails, Airflow retries it 2 times, then alert_on_failure()
sends a Slack + email message.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Let Airflow find our "config" and "src" folders (project root = one level up)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_pipeline  # noqa: E402
from src.utils.alerts import alert_on_failure  # noqa: E402

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": alert_on_failure,
}

with DAG(
    dag_id="etl_synchronizer_daily",
    description="Daily ETL: Stripe + Salesforce -> Data Warehouse",
    default_args=default_args,
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "stripe", "salesforce", "warehouse"],
) as dag:
    run_etl = PythonOperator(
        task_id="run_etl_pipeline",
        python_callable=run_pipeline,
        op_kwargs={"incremental": True},
    )
