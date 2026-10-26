-- Create a separate database for Airflow's own metadata.
-- Airflow needs this database to store DAG runs, task instances, logs etc.
-- This script runs automatically when the postgres container starts for the first time.
CREATE DATABASE airflow;
