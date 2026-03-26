#!/bin/bash
echo "================================================"
echo "  CIE Manager - DFC/CIE"
echo "================================================"
cd "$(dirname "$0")"
source venv/bin/activate
python run_server.py --host 0.0.0.0 --port 8000
