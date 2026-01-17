#!/usr/bin/env python3
"""
Airflow MCP Server - Model Context Protocol server for Apache Airflow 3
Provides tools for DAG management, monitoring, debugging, and connection testing.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Load environment variables
load_dotenv()

# Airflow API configuration
AIRFLOW_API_URL = os.getenv("airflow_api_url", "http://localhost:8080/api/v2")
AIRFLOW_BASE_URL = os.getenv("airflow_baseurl", "http://localhost:8080")
AIRFLOW_USERNAME = os.getenv("airflow_username", "airflow")
AIRFLOW_PASSWORD = os.getenv("airflow_password", "airflow")
AIRFLOW_JWT_TOKEN = os.getenv("airflow_jwt_token")

# Initialize MCP server
app = Server("airflow-mcp-server")


def get_auth_headers() -> dict[str, str]:
    """Get authentication headers for Airflow API requests."""
    if AIRFLOW_JWT_TOKEN:
        return {
            "Authorization": f"Bearer {AIRFLOW_JWT_TOKEN}",
            "Content-Type": "application/json",
        }
    else:
        # Basic auth fallback
        import base64
        credentials = f"{AIRFLOW_USERNAME}:{AIRFLOW_PASSWORD}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }


async def make_api_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Make an API request to Airflow with proper error handling.
    
    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        endpoint: API endpoint path (without base URL)
        params: Query parameters
        json_data: JSON body for POST/PATCH requests
        
    Returns:
        API response as dictionary
    """
    url = f"{AIRFLOW_API_URL}/{endpoint.lstrip('/')}"
    headers = get_auth_headers()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        try:
            error_json = e.response.json()
            error_detail = error_json.get("detail", error_detail)
        except:
            pass
        raise Exception(f"API request failed ({e.response.status_code}): {error_detail}")
    except httpx.RequestError as e:
        raise Exception(f"Connection error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        # DAG Management Tools
        Tool(
            name="get_dags",
            description="List all DAGs in Airflow with optional filtering by paused status",
            inputSchema={
                "type": "object",
                "properties": {
                    "only_active": {
                        "type": "boolean",
                        "description": "If true, only return active (unpaused) DAGs",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of DAGs to return (default: 100)",
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_dag_tasks",
            description="Get all tasks in a specific DAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                },
                "required": ["dag_id"],
            },
        ),
        Tool(
            name="trigger_dag_run",
            description="Trigger a new DAG run",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG to trigger",
                    },
                    "conf": {
                        "type": "object",
                        "description": "Optional configuration JSON to pass to the DAG run",
                    },
                    "logical_date": {
                        "type": "string",
                        "description": "Optional logical date for the DAG run (ISO format)",
                    },
                },
                "required": ["dag_id"],
            },
        ),
        Tool(
            name="clear_dag_run",
            description="Clear/retry a DAG run (resets failed tasks)",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                    "dag_run_id": {
                        "type": "string",
                        "description": "The ID of the DAG run to clear",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only show what would be cleared without actually clearing",
                        "default": False,
                    },
                },
                "required": ["dag_id", "dag_run_id"],
            },
        ),
        Tool(
            name="set_dag_state",
            description="Pause or unpause a DAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                    "is_paused": {
                        "type": "boolean",
                        "description": "True to pause the DAG, False to unpause it",
                    },
                },
                "required": ["dag_id", "is_paused"],
            },
        ),
        
        # Monitoring & Status Tools
        Tool(
            name="get_dag_runs",
            description="Get DAG run history with optional status filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state (success, failed, running, queued)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of runs to return (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["dag_id"],
            },
        ),
        Tool(
            name="get_task_instances",
            description="Get task instances for a specific DAG run",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                    "dag_run_id": {
                        "type": "string",
                        "description": "The ID of the DAG run",
                    },
                },
                "required": ["dag_id", "dag_run_id"],
            },
        ),
        Tool(
            name="get_dag_stats",
            description="Get aggregate statistics for all DAGs",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        
        # Debugging & Logs Tools
        Tool(
            name="get_task_logs",
            description="Get execution logs for a specific task instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "dag_id": {
                        "type": "string",
                        "description": "The ID of the DAG",
                    },
                    "dag_run_id": {
                        "type": "string",
                        "description": "The ID of the DAG run",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task",
                    },
                    "try_number": {
                        "type": "integer",
                        "description": "The try number of the task (default: 1)",
                        "default": 1,
                    },
                },
                "required": ["dag_id", "dag_run_id", "task_id"],
            },
        ),
        Tool(
            name="get_import_errors",
            description="Get DAG import/parsing errors",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        
        # Connection Management Tools
        Tool(
            name="get_connections",
            description="List all Airflow connections",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of connections to return (default: 100)",
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_connection",
            description="Get details of a specific connection",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "The ID of the connection",
                    },
                },
                "required": ["connection_id"],
            },
        ),
        Tool(
            name="test_connection",
            description="Test a connection to verify it works",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "The ID of the connection to test",
                    },
                },
                "required": ["connection_id"],
            },
        ),
        
        # Health Check Tool
        Tool(
            name="check_health",
            description="Check Airflow system health (scheduler and database status)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    try:
        # DAG Management Tools
        if name == "get_dags":
            only_active = arguments.get("only_active", False)
            limit = arguments.get("limit", 100)
            
            params = {"limit": limit}
            if only_active:
                params["only_active"] = "true"
            
            result = await make_api_request("GET", "dags", params=params)
            dags = result.get("dags", [])
            
            summary = f"Found {len(dags)} DAGs:\n\n"
            for dag in dags:
                status = "⏸️ Paused" if dag.get("is_paused") else "▶️ Active"
                summary += f"- **{dag['dag_id']}** ({status})\n"
                summary += f"  - Description: {dag.get('description', 'N/A')}\n"
                summary += f"  - Schedule: {dag.get('schedule_interval', 'N/A')}\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "get_dag_tasks":
            dag_id = arguments["dag_id"]
            result = await make_api_request("GET", f"dags/{dag_id}/tasks")
            tasks = result.get("tasks", [])
            
            summary = f"Tasks in DAG '{dag_id}' ({len(tasks)} tasks):\n\n"
            for task in tasks:
                summary += f"- **{task['task_id']}**\n"
                summary += f"  - Type: {task.get('operator_name', 'N/A')}\n"
                summary += f"  - Downstream: {', '.join(task.get('downstream_task_ids', []))}\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "trigger_dag_run":
            dag_id = arguments["dag_id"]
            conf = arguments.get("conf", {})
            logical_date = arguments.get("logical_date")
            
            body = {}
            if conf:
                body["conf"] = conf
            if logical_date:
                body["logical_date"] = logical_date
            
            result = await make_api_request("POST", f"dags/{dag_id}/dagRuns", json_data=body)
            
            summary = f"✅ DAG run triggered successfully!\n\n"
            summary += f"- **DAG ID**: {result['dag_id']}\n"
            summary += f"- **Run ID**: {result['dag_run_id']}\n"
            summary += f"- **State**: {result['state']}\n"
            summary += f"- **Execution Date**: {result.get('execution_date', 'N/A')}\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "clear_dag_run":
            dag_id = arguments["dag_id"]
            dag_run_id = arguments["dag_run_id"]
            dry_run = arguments.get("dry_run", False)
            
            body = {"dry_run": dry_run}
            result = await make_api_request("POST", f"dags/{dag_id}/dagRuns/{dag_run_id}/clear", json_data=body)
            
            if dry_run:
                summary = "🔍 Dry run - Tasks that would be cleared:\n\n"
            else:
                summary = "✅ DAG run cleared successfully!\n\n"
            
            task_instances = result.get("task_instances", [])
            for ti in task_instances:
                summary += f"- {ti['task_id']} (Try: {ti.get('try_number', 'N/A')})\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "set_dag_state":
            dag_id = arguments["dag_id"]
            is_paused = arguments["is_paused"]
            
            body = {"is_paused": is_paused}
            result = await make_api_request("PATCH", f"dags/{dag_id}", json_data=body)
            
            state_str = "⏸️ PAUSED" if is_paused else "▶️ ACTIVE"
            summary = f"✅ DAG '{dag_id}' is now {state_str}\n\n"
            summary += f"- **Description**: {result.get('description', 'N/A')}\n"
            summary += f"- **Schedule**: {result.get('schedule_interval', 'N/A')}\n"
            
            return [TextContent(type="text", text=summary)]
        
        # Monitoring & Status Tools
        elif name == "get_dag_runs":
            dag_id = arguments["dag_id"]
            state = arguments.get("state")
            limit = arguments.get("limit", 25)
            
            params = {"limit": limit}
            if state:
                params["state"] = state
            
            result = await make_api_request("GET", f"dags/{dag_id}/dagRuns", params=params)
            dag_runs = result.get("dag_runs", [])
            
            summary = f"DAG runs for '{dag_id}' ({len(dag_runs)} runs):\n\n"
            for run in dag_runs:
                state_emoji = {
                    "success": "✅",
                    "failed": "❌",
                    "running": "🔄",
                    "queued": "⏳",
                }.get(run.get("state", "").lower(), "❓")
                
                summary += f"{state_emoji} **{run['dag_run_id']}**\n"
                summary += f"  - State: {run.get('state', 'N/A')}\n"
                summary += f"  - Start: {run.get('start_date', 'N/A')}\n"
                summary += f"  - End: {run.get('end_date', 'N/A')}\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "get_task_instances":
            dag_id = arguments["dag_id"]
            dag_run_id = arguments["dag_run_id"]
            
            result = await make_api_request("GET", f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances")
            task_instances = result.get("task_instances", [])
            
            summary = f"Task instances for '{dag_id}' run '{dag_run_id}':\n\n"
            for ti in task_instances:
                state_emoji = {
                    "success": "✅",
                    "failed": "❌",
                    "running": "🔄",
                    "queued": "⏳",
                    "skipped": "⏭️",
                }.get(ti.get("state", "").lower(), "❓")
                
                summary += f"{state_emoji} **{ti['task_id']}**\n"
                summary += f"  - State: {ti.get('state', 'N/A')}\n"
                summary += f"  - Try Number: {ti.get('try_number', 'N/A')}\n"
                summary += f"  - Duration: {ti.get('duration', 'N/A')}s\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "get_dag_stats":
            result = await make_api_request("GET", "dagStats")
            stats = result.get("dags", [])
            
            summary = "📊 DAG Statistics:\n\n"
            for dag_stat in stats:
                summary += f"**{dag_stat['dag_id']}**:\n"
                for state_stat in dag_stat.get("stats", []):
                    summary += f"  - {state_stat['state']}: {state_stat['count']}\n"
                summary += "\n"
            
            return [TextContent(type="text", text=summary)]
        
        # Debugging & Logs Tools
        elif name == "get_task_logs":
            dag_id = arguments["dag_id"]
            dag_run_id = arguments["dag_run_id"]
            task_id = arguments["task_id"]
            try_number = arguments.get("try_number", 1)
            
            # Note: Airflow API v2 doesn't have a direct log endpoint, we need to construct it
            # The endpoint follows this pattern for log retrieval
            endpoint = f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
            
            try:
                result = await make_api_request("GET", endpoint)
                
                if isinstance(result, dict):
                    log_content = result.get("content", str(result))
                else:
                    log_content = str(result)
                
                summary = f"📝 Logs for task '{task_id}' (Try #{try_number}):\n\n"
                summary += "```\n"
                summary += log_content
                summary += "\n```"
                
                return [TextContent(type="text", text=summary)]
            except Exception as e:
                # If logs endpoint fails, try to get task instance info
                ti_result = await make_api_request("GET", f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}")
                
                summary = f"ℹ️ Task Instance Info for '{task_id}':\n\n"
                summary += f"- State: {ti_result.get('state', 'N/A')}\n"
                summary += f"- Try Number: {ti_result.get('try_number', 'N/A')}\n"
                summary += f"- Start Date: {ti_result.get('start_date', 'N/A')}\n"
                summary += f"- End Date: {ti_result.get('end_date', 'N/A')}\n\n"
                summary += f"⚠️ Note: Direct log retrieval failed. You may need to access logs through the Airflow UI at:\n"
                summary += f"{AIRFLOW_BASE_URL}/dags/{dag_id}/grid?dag_run_id={dag_run_id}&task_id={task_id}\n\n"
                summary += f"Error: {str(e)}"
                
                return [TextContent(type="text", text=summary)]
        
        elif name == "get_import_errors":
            result = await make_api_request("GET", "importErrors")
            errors = result.get("import_errors", [])
            
            if not errors:
                summary = "✅ No DAG import errors found!"
            else:
                summary = f"⚠️ Found {len(errors)} DAG import errors:\n\n"
                for error in errors:
                    summary += f"**{error.get('filename', 'Unknown file')}**:\n"
                    summary += f"```\n{error.get('stack_trace', 'No error details')}\n```\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        # Connection Management Tools
        elif name == "get_connections":
            limit = arguments.get("limit", 100)
            result = await make_api_request("GET", "connections", params={"limit": limit})
            connections = result.get("connections", [])
            
            summary = f"🔌 Airflow Connections ({len(connections)} connections):\n\n"
            for conn in connections:
                summary += f"- **{conn['connection_id']}**\n"
                summary += f"  - Type: {conn.get('conn_type', 'N/A')}\n"
                summary += f"  - Host: {conn.get('host', 'N/A')}\n"
                summary += f"  - Schema: {conn.get('schema', 'N/A')}\n\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "get_connection":
            connection_id = arguments["connection_id"]
            result = await make_api_request("GET", f"connections/{connection_id}")
            
            summary = f"🔌 Connection Details: **{connection_id}**\n\n"
            summary += f"- **Type**: {result.get('conn_type', 'N/A')}\n"
            summary += f"- **Host**: {result.get('host', 'N/A')}\n"
            summary += f"- **Schema**: {result.get('schema', 'N/A')}\n"
            summary += f"- **Login**: {result.get('login', 'N/A')}\n"
            summary += f"- **Port**: {result.get('port', 'N/A')}\n"
            summary += f"- **Extra**: {result.get('extra', 'N/A')}\n"
            
            return [TextContent(type="text", text=summary)]
        
        elif name == "test_connection":
            connection_id = arguments["connection_id"]
            
            # Try to get the connection - if it exists and is retrievable, it's "working" at the API level
            try:
                result = await make_api_request("GET", f"connections/{connection_id}")
                
                summary = f"✅ Connection '{connection_id}' is accessible!\n\n"
                summary += f"- **Type**: {result.get('conn_type', 'N/A')}\n"
                summary += f"- **Host**: {result.get('host', 'N/A')}\n\n"
                summary += "ℹ️ Note: This tests API accessibility. To test actual connectivity to the external service, "
                summary += "you'll need to trigger a DAG that uses this connection.\n"
                
                return [TextContent(type="text", text=summary)]
            except Exception as e:
                summary = f"❌ Connection test failed for '{connection_id}':\n\n"
                summary += f"Error: {str(e)}\n"
                
                return [TextContent(type="text", text=summary)]
        
        # Health Check Tool
        elif name == "check_health":
            result = await make_api_request("GET", "health")
            
            summary = "🏥 Airflow Health Status:\n\n"
            
            metadatabase = result.get("metadatabase", {})
            scheduler = result.get("scheduler", {})
            
            db_status = metadatabase.get("status", "unknown")
            scheduler_status = scheduler.get("status", "unknown")
            
            db_emoji = "✅" if db_status == "healthy" else "❌"
            scheduler_emoji = "✅" if scheduler_status == "healthy" else "❌"
            
            summary += f"{db_emoji} **Metadatabase**: {db_status}\n"
            summary += f"{scheduler_emoji} **Scheduler**: {scheduler_status}\n"
            
            if scheduler.get("latest_scheduler_heartbeat"):
                summary += f"\n📅 Latest Scheduler Heartbeat: {scheduler['latest_scheduler_heartbeat']}\n"
            
            return [TextContent(type="text", text=summary)]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        error_msg = f"❌ Error executing '{name}':\n\n{str(e)}"
        return [TextContent(type="text", text=error_msg)]


def auto_update_check():
    """Check for updates on startup"""
    if os.getenv("GIT_AUTO_UPDATE") != "true":
        print('GIT_AUTO_UPDATE is false, skipping the update.')
        return  # Skip if not enabled
    
    try:
        repo_path = Path(__file__).parent
        
        # Fetch latest from remote
        result = subprocess.run(
            ["git", "fetch"], 
            cwd=repo_path, 
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Warning: git fetch failed: {result.stderr.decode()}")
            return
        
        # Check if behind remote
        result = subprocess.run(
            ["git", "status", "-uno", "-sb"], 
            cwd=repo_path, 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print(f"Warning: git status check failed")
            return
        
        # Look for "behind" indicator
        if "behind" in result.stdout.lower():
            print("📥 Update available, pulling latest version...")
            
            pull_result = subprocess.run(
                ["git", "pull", "--ff-only"],  # Only fast-forward to be safe
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if pull_result.returncode == 0:
                print("✅ Successfully updated to latest version!")
                print("⚠️  Please restart Claude Desktop to use the new version")
            else:
                print(f"❌ Update failed: {pull_result.stderr}")
        else:
            print("✅ Already up to date")
                
    except subprocess.TimeoutExpired:
        print("⚠️  Update check timed out")
    except FileNotFoundError:
        print("⚠️  Git not found - skipping auto-update")
    except Exception as e:
        # Don't crash the server if update fails
        print(f"⚠️  Auto-update check failed: {str(e)}")



async def main():
    """Run the MCP server."""
    print('checking the update..')
    # update the code
    auto_update_check()

    print('the server is running..')
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
