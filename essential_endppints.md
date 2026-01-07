# Airflow API v2: Essential Endpoints for Data Engineering

### 🚀 Data Engineering (Actions)
*Used for triggering jobs, fixing data, and managing credentials.*

- **POST** `/api/v2/dags/{dag_id}/dagRuns` 
  - *Trigger a DAG run immediately.*
- **POST** `/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/clear` 
  - *Reset/Retry a failed DAG run.*
- **POST** `/api/v2/backfills` 
  - *Run a historical backfill for a date range.*
- **POST** `/api/v2/assets/events` 
  - *Manually signal that a dataset/asset is ready to trigger downstream jobs.*
- **PATCH** `/api/v2/connections/{connection_id}` 
  - *Update database credentials or API keys.*
- **PATCH** `/api/v2/variables/{variable_key}` 
  - *Update global configuration values.*

---

### 🔍 Observation (Monitoring & Debugging)
*Used for checking pipeline health and finding errors.*

- **GET** `/api/v2/dags/{dag_id}/dagRuns` 
  - *Check the status (Success/Failed/Running) of recent runs.*
- **GET** `/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances` 
  - *See which specific tasks inside a DAG failed.*
- **GET** `/api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}` 
  - *Read the error logs for a specific failed task.*
- **GET** `/api/v2/importErrors` 
  - *Check if a DAG file has syntax errors preventing it from appearing in Airflow.*
- **GET** `/api/v2/dagStats` 
  - *Get a high-level summary of success vs. failure counts.*
- **GET** `/api/v2/monitor/health` 
  - *Verify if the Scheduler and Database are online.*