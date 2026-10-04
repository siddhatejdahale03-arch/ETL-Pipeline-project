"""Airflow DAG for the daily ETL run."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.pipeline import run_pipeline
from src.utils.alerts import alert_on_failure


default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": alert_on_failure,
}


with DAG(
    dag_id="etl_synchronizer_daily",
    description="Daily ETL: Stripe + Salesforce → Data Warehouse",
    default_args=default_args,
    schedule="0 2 * * *",           # 02:00 UTC daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "stripe", "salesforce", "warehouse"],
) as dag:

    run_etl = PythonOperator(
        task_id="run_etl_pipeline",
        python_callable=run_pipeline,
        op_kwargs={"incremental": True},
        doc_md="Extract → S3 → Transform → Upsert DW",
    )

    run_etl