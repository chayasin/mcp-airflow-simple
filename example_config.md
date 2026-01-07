# Example MCP Client Configuration

This directory contains example configuration for integrating the Airflow MCP server with MCP clients.

## Claude Desktop Configuration

### Windows

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "airflow": {
      "command": "python",
      "args": ["path_to_the_file\\mcp-airflow-simple\\server.py"]
    }
  }
}
```

### macOS/Linux

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "airflow": {
      "command": "python3",
      "args": ["/path_to_the_file/mcp-airflow/server.py"]
    }
  }
}
```

## Testing the Server

You can test the server standalone by running:

```bash
python server.py
```

The server will start in stdio mode and wait for MCP protocol messages on stdin.

## Environment Variables

The server reads configuration from the `.env` file in the project directory. Make sure it's properly configured before starting the server.
