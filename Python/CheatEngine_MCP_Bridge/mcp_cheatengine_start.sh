#!/bin/bash

CE_MCP_TRANSPORT=tcp CE_MCP_HOST=127.0.0.1 CE_MCP_PORT=9876 \
./venv/bin/python ./MCP_Server/mcp_cheatengine.py
