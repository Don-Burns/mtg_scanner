#!/bin/bash
# Start the development server

# fastapi dev mode
# fastapi dev src/mtg_scanner/web_server/main.py

# for hot reloading of the server on change to html/css files
uvicorn mtg_scanner.web_server.main:app --reload --reload-include *.html --reload-include *.css
