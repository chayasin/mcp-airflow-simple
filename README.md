# Airflow MCP Server

A **Model Context Protocol (MCP) server** for Apache Airflow 3 that provides essential tools for DAG management, monitoring, debugging, and connection testing through the Airflow REST API v2.

## Quick Start

### 1. Create '.env' file
```bash
cp .env.example .env
```

### 2. Get the airflow token
make sure your airflow is running and accessible at the configured URL

```bash
curl -X POST "{your_ariflow_url}/auth/token" -H "Content-Type: application/json" -d '{"username":"{your_airflow_username}","password":"{your_airflow_password}"}'
```

Example:

```bash
curl -X POST "http://localhost:8080/auth/token" -H "Content-Type: application/json" -d '{"username":"airflow","password":"airflow"}'
```

it will return a token, copy the token and paste it to the .env file

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. config the MCP server

```json
{
  "mcpServers": {
    "airflow": {
      "command": "python",
      "args": ["c:\\{spath_to_your_folder}\\mcp-airflow-simple\\server.py"],
      "env": {
        "GIT_AUTO_UPDATE": "true"
      }
    }
  }
}
```


## Features

### 🚀 DAG Management
- List all DAGs with filtering options
- Get tasks within a specific DAG
- Trigger DAG runs with optional configuration
- Clear/retry failed DAG runs

### 🔍 Monitoring & Status
- Check DAG run history and status
- View task instances for specific runs
- Get aggregate DAG statistics

### 🐛 Debugging & Logs
- Retrieve task execution logs
- Check DAG import/parsing errors

### 🔌 Connection Management
- List all Airflow connections
- Get connection details
- Test connection accessibility

### 🏥 Health Checks
- Monitor Airflow Scheduler, Metadatabase, Triggerer, and DagProcessor status

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd c:\Users\ChayasinSaetia\chayasin-laptop\mcp-airflow
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Edit the `.env` file with your Airflow instance details:
   ```env
   airflow_baseurl=http://localhost:8080
   airflow_api_url=http://localhost:8080/api/v2
   airflow_username=airflow
   airflow_password=airflow
   airflow_jwt_token=your_jwt_token_here
   ```

## Configuration

The server supports two authentication methods:

1. **JWT Token (Preferred)**: Set `airflow_jwt_token` in `.env`
2. **Basic Auth (Fallback)**: Uses `airflow_username` and `airflow_password`

The server will automatically use JWT if available, otherwise fall back to basic authentication.

## Available MCP Tools

### DAG Management

#### `get_dags`
List all DAGs in Airflow.
```json
{
  "only_active": false,
  "limit": 100
}
```

#### `get_dag_tasks`
Get all tasks in a specific DAG.
```json
{
  "dag_id": "example_dag"
}
```

#### `trigger_dag_run`
Trigger a new DAG run.
```json
{
  "dag_id": "example_dag",
  "conf": {"key": "value"},
  "logical_date": "2026-01-05T00:00:00Z"
}
```

#### `clear_dag_run`
Clear/retry a DAG run (resets failed tasks).
```json
{
  "dag_id": "example_dag",
  "dag_run_id": "manual__2026-01-05T00:00:00+00:00",
  "dry_run": false
}
```

#### `set_dag_state`
Pause or unpause a DAG.
```json
{
  "dag_id": "example_dag",
  "is_paused": true
}
```

### Monitoring & Status

#### `get_dag_runs`
Get DAG run history with optional state filtering.
```json
{
  "dag_id": "example_dag",
  "state": "failed",
  "limit": 25
}
```

#### `get_task_instances`
Get task instances for a specific DAG run.
```json
{
  "dag_id": "example_dag",
  "dag_run_id": "manual__2026-01-05T00:00:00+00:00"
}
```

#### `get_dag_stats`
Get aggregate statistics for all DAGs.
```json
{}
```

### Debugging & Logs

#### `get_task_logs`
Get execution logs for a specific task instance.
```json
{
  "dag_id": "example_dag",
  "dag_run_id": "manual__2026-01-05T00:00:00+00:00",
  "task_id": "example_task",
  "try_number": 1
}
```

#### `get_import_errors`
Get DAG import/parsing errors.
```json
{}
```

### Connection Management

#### `get_connections`
List all Airflow connections.
```json
{
  "limit": 100
}
```

#### `get_connection`
Get details of a specific connection.
```json
{
  "connection_id": "postgres_default"
}
```

#### `test_connection`
Test connection accessibility.
```json
{
  "connection_id": "postgres_default"
}
```

### Health Check

#### `check_health`
Check Airflow system health (includes Metadatabase, Scheduler, Triggerer, and DagProcessor).
```json
{}
```

## Running the Server

### As an MCP Server (Stdio)

The server runs as a stdio-based MCP server:

```bash
python server.py
```

### Integration with MCP Clients

To use this server with MCP clients like Claude Desktop, add to your MCP configuration:

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "airflow": {
      "command": "python",
      "args": ["c:\\Users\\ChayasinSaetia\\chayasin-laptop\\mcp-airflow\\server.py"],
      "env": {
        "airflow_api_url": "http://localhost:8080/api/v2",
        "airflow_jwt_token": "your_token_here"
      }
    }
  }
}
```

**macOS/Linux** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "airflow": {
      "command": "python3",
      "args": ["/path/to/mcp-airflow/server.py"]
    }
  }
}
```

## Troubleshooting

### Connection Issues
- Verify Airflow is running and accessible at the configured URL
- Check authentication credentials (JWT token or username/password)
- Ensure the Airflow REST API is enabled

### Authentication Errors
- Confirm JWT token is valid and not expired
- Verify username and password are correct
- Check that the user has necessary permissions in Airflow

### Tool Errors
- Ensure DAG IDs and run IDs are correct
- Check that the requested resources exist in Airflow
- Review Airflow logs for additional context

## API Reference

This MCP server uses the **Airflow REST API v2**. For detailed API documentation, see:
- [Airflow REST API Documentation](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html)
- Local OpenAPI spec: `openapi.json`

## Requirements

- Python 3.8+
- Apache Airflow 3.x with REST API enabled
- Network access to Airflow instance

## License

MIT License - feel free to use and modify as needed.
