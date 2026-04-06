# services/api

Backend-ul API pentru price-watch-ro / Chilipir.

Acest folder conține aplicația FastAPI folosită pentru:
- endpoint-uri API locale
- watchlists și produse
- refresh-uri locale
- health check
- logica backend pentru workflow-ul actual al proiectului

## Cerințe

Pentru rulare locală ai nevoie de:
- Python 3.12 sau mai nou
- pip
- virtual environment (venv)
- fișierul requirements.txt din acest folder

Pentru anumite flow-uri locale poate fi necesar și:
- Playwright
- Chromium instalat prin Playwright

## Instalare locală

Din acest folder:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\requirements.txt
python -m playwright install chromium

## Pornire locală

Din acest folder:

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

API-ul pornește implicit la:

http://127.0.0.1:8000

## Test rapid

Health check:

http://127.0.0.1:8000/health

Exemplu în PowerShell:

curl.exe http://127.0.0.1:8000/health

Răspuns așteptat:

{"status":"ok"}

## Pornire pe alt port

Dacă portul 8000 este deja ocupat, poți porni temporar pe alt port:

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010

Exemplu health check:

curl.exe http://127.0.0.1:8010/health

## Ce conține acest folder

În services/api se află partea de backend a proiectului:
- aplicația FastAPI
- routere și endpoint-uri
- logică backend pentru produse și watchlists
- refresh local și integrare cu workflow-ul proiectului
- fișiere auxiliare pentru fluxurile locale

## Observații

- backend-ul este gândit în primul rând pentru rulare locală
- workflow-ul actual este orientat pe dezvoltare și testare locală
- unele flow-uri pot depinde de Chrome remote debugging sau Playwright, în funcție de scenariul testat
- pentru contextul complet al proiectului, vezi README.md din rădăcina repository-ului

## Scope

Acest folder conține doar backend-ul API.

Pentru frontend, scripturi locale și informații generale despre proiect, vezi fișierul README.md din rădăcina repository-ului.
