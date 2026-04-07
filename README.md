---
title: NutriAgent Backend
emoji: 🥑
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# NutriAgent_Backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

postgresql://postgres:[YOUR-PASSWORD]@db.twrgffggokcggcjsvhmd.supabase.co:5432/postgres

postgresql+asyncpg://postgres.twrgffggokcggcjsvhmd:ThisIsDatabsePassword@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres