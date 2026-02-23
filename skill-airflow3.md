# Airflow 3 DAGs
## Syntax
- `schedule_interval` → `schedule`
- `execution_date` → `logical_date`
- `from airflow import DAG` / `from airflow.decorators import task` → `from airflow.sdk import dag, task`
- `from airflow.models import Variable` → `from airflow.sdk import Variable`
- `SubDagOperator` → `TaskGroup`
## Convention
- Use `@dag`, `@task`
- XCom via function args: `def my_task(xcom_value): ...`