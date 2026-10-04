-- Runs once when the Postgres container is first created.
-- Airflow needs its own database to store DAG runs.
CREATE DATABASE airflow;
