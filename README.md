---
title: ForgeBI Demo App
emoji: 📊
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# ForgeBI Demo Platform

An anonymized and isolated demo version of the **ForgeBI** enterprise business intelligence platform.

## Setup & Running

This app runs inside a standalone Docker container using a local SQLite database and pre-packaged anonymized Parquet data snapshots.

### Local Running

To run the dashboard locally:
```bash
pip install -r requirements.txt
python app/app.py
```

### Credentials

Access the demo dashboard using the following credentials:
- **Email**: `demo@forgebi.com`
- **Password**: `demo123`
