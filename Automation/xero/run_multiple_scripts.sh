#!/bin/bash
cd /home/ubuntu_admin/xero

echo "All Journals"
python3 AllJournals.py
sleep 10

echo "All Other Tables"
python3 xero.py
sleep 10

echo "Upload"
python3 xero_upload.py
sleep 10

echo "Upload"
python3 xerodataloadsnowflake.py
sleep 10

echo "Upload"
python3 refreshPBI.py
