# price-watch-ro / Chilipir

Aplicație local-first pentru liste și alerte de preț, construită în jurul ideii de monitorizare simplă a produselor și a variațiilor de preț.

Chilipir este brandingul folosit pentru MVP-ul orientat pe liste, watchlists și refresh local al datelor.

## Status

Proiectul este în stadiu beta / MVP.

Repository-ul public reflectă structura reală a proiectului și workflow-ul local folosit în dezvoltare. În forma actuală, focusul este pe rulare locală, testare manuală și iterație rapidă.

## Scope curent

În starea actuală, proiectul include:
- frontend web în Next.js
- backend API în FastAPI
- watchlists și refresh-uri pentru produse
- scripturi locale pentru pornire și oprire rapidă
- workflow local pentru dezvoltare și testare

## Stack

- Frontend: Next.js
- Backend: FastAPI
- Limbaj principal backend: Python
- Limbaj principal frontend: TypeScript / React
- Bază de date: workflow local, orientat pe rulare standalone
- Tooling local: PowerShell, Chrome remote debugging

## Repository structure

apps/
  web/               frontend-ul web

services/
  api/               backend-ul FastAPI

scripts/
  dev/               scripturi locale pentru start/stop

README.md
LICENSE
.env.example

## Quick start

### Workflow recomandat (Windows PowerShell)

Din rădăcina repository-ului:

.\scripts\dev\start-local.ps1

Scriptul încearcă să:
- pornească Google Chrome cu remote debugging pe portul 9222
- pornească API-ul local la http://127.0.0.1:8000
- pornească frontend-ul local la http://localhost:3000

Pentru oprire:

.\scripts\dev\stop-local.ps1

## Frontend only

Pentru pornirea doar a frontend-ului:

cd .\apps\web
npm install
$env:NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000"
npm run dev

Frontend-ul pornește implicit la:

http://localhost:3000

## Chrome pentru rendered refresh

În anumite flow-uri locale poate fi necesar Chrome cu remote debugging activ.

Pornire manuală exemplu:

& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:TEMP\price-watch-ro-chrome"

## Variabile de mediu

Repository-ul conține un fișier .env.example.

Exemplu de variabilă folosită de frontend:

NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

## Important note about backend bootstrap

Repository-ul public păstrează backend-ul și structura reală a proiectului, dar în forma actuală nu publică încă un manifest dedicat de dependențe pentru un bootstrap complet, de la zero, al backend-ului într-un clone nou.

Asta înseamnă:
- codul backend este prezent în repository
- workflow-ul local existent este documentat
- documentația pentru instalarea standalone complet reproductibilă a backend-ului trebuie aliniată într-un commit separat, odată cu publicarea manifestului de dependențe corespunzător

Cu alte cuvinte, repo-ul este public și util ca structură, context, cod și workflow local, dar onboarding-ul backend pentru un mediu complet nou nu este încă finalizat la nivel de packaging.

## Notes

- proiectul este gândit în primul rând pentru rulare locală
- unele flow-uri depind de un mediu local deja pregătit
- scripturile din scripts/dev sunt orientate pe workflow-ul curent de dezvoltare
- stop-local.ps1 poate opri procese care folosesc porturile locale relevante proiectului

## Limitări

În starea actuală:
- proiectul este orientat spre uz local și testare beta
- documentația de bootstrap complet pentru backend nu este încă finalizată
- pot exista zone în curs de refactorizare sau polish
- unele funcționalități sunt optimizate pentru mediul local al dezvoltatorului

## Legal

Acest proiect este distribuit sub licența MIT. Vezi fișierul LICENSE pentru detalii.

## Disclaimer

Acest proiect este un proiect independent și experimental.

Nu este afiliat oficial cu magazine, platforme comerciale sau servicii terțe care pot apărea în logica aplicației, în exemple sau în fluxurile de testare.

Utilizarea proiectului și adaptarea lui pentru alte surse, fluxuri sau scopuri rămân responsabilitatea utilizatorului.

## AI assistance disclosure

Ideea, direcția produsului și deciziile de selecție aparțin autorului proiectului.

Arhitectura, implementarea și documentația au fost realizate cu asistență AI, în diferite etape ale dezvoltării. Codul publicat a fost selectat, ajustat și integrat în proiect de autor.

## Author

Laurentiu Iulian Iancu
a.k.a. CyberXecure