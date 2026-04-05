# price-watch-ro

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Chilipir** — aplicație local-first pentru liste și alerte de preț pentru Freshful, construită cu **FastAPI**, **Next.js** și **SQLite**.

> Status: beta locală freeze-ready, curățată pentru open-source. Repository-ul nu urmărește reluarea debugging-ului beta.

## Overview

`price-watch-ro` este un proiect local-first pentru urmărirea produselor Freshful într-o formă simplă și practică.

Stare funcțională actuală:

- import Freshful funcțional
- refresh static funcțional
- refresh promo/rendered funcțional cu Chrome remote debugging pe portul `9222`
- target price funcțional
- filtre funcționale: active / ascunse / toate
- stocare locală în SQLite

Scopul actual este un MVP curat, simplu și reproductibil pentru rulare locală.

## Current scope

Scope-ul actual al proiectului este:

- **Freshful only**
- **local-first**
- **FastAPI + Next.js + SQLite**
- fără infrastructură cloud obligatorie
- fără complexitate inutilă
- refresh rendered bazat pe o sesiune locală Chrome expusă pe `9222`

## Tech stack

- **Backend:** FastAPI
- **Frontend:** Next.js
- **Database:** SQLite
- **Rendered refresh:** Chrome / Chromium remote debugging
- **Primary target:** rulare locală

## Repository structure

```text
price-watch-ro/
├─ apps/
│  └─ web/
├─ services/
│  └─ api/
├─ scripts/
│  └─ dev/
│     ├─ start-local.ps1
│     └─ stop-local.ps1
├─ .env.example
├─ .gitignore
├─ LICENSE
└─ README.md
```

## Requirements

Pentru rulare locală:

- Python 3.12+
- Node.js 20+
- npm
- Google Chrome sau Chromium
- Windows PowerShell

## Quick start

### 1. Backend

```powershell
cd services/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API-ul pornește implicit la:

```text
http://127.0.0.1:8000
```

### 2. Frontend

```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000"
npm run dev
```

Frontend-ul pornește implicit la:

```text
http://localhost:3000
```

### 3. Chrome pentru rendered refresh

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:TEMP\price-watch-ro-chrome"
```

### 4. Scripturi helper

Din rădăcina repo-ului:

```powershell
.\scripts\dev\start-local.ps1
.\scripts\dev\stop-local.ps1
```

## Notes

- proiectul folosește **SQLite** pentru simplitate și portabilitate locală
- fișierele locale de bază de date nu trebuie comise în Git
- refresh-ul rendered depinde de o sesiune locală Chrome disponibilă pe `9222`
- repository-ul urmărește o structură minimă și clară

## What is intentionally not included

În forma actuală, repository-ul nu urmărește:

- deploy cloud
- multi-store production support
- infrastructură complexă
- documentarea etapelor vechi de debugging beta

## Legal

Acest proiect este:

- **neoficial**
- **neafiliat** cu Freshful sau cu proprietarii mărcilor asociate
- publicat exclusiv în scop de dezvoltare software, testare locală și studiu tehnic

Toate mărcile, denumirile comerciale și numele produselor aparțin proprietarilor lor legitimi.

Utilizarea proiectului trebuie făcută responsabil și în conformitate cu termenii aplicabili platformelor terțe folosite.

## AI assistance disclaimer

Ideea proiectului, direcția produsului și deciziile funcționale aparțin autorului repository-ului.

Părți din arhitectură, implementare, refactorizare și documentație au fost generate sau accelerate cu ajutor AI. Tot conținutul trebuie revizuit și validat de autor înainte de utilizare în medii reale sau publice.

## License

Acest proiect este licențiat sub **MIT License**. Vezi fișierul [LICENSE](LICENSE).
