# apps/web

Frontend-ul web pentru price-watch-ro / Chilipir.

Acest folder conține aplicația Next.js folosită ca interfață locală pentru:
- liste de produse
- watchlists
- refresh și status UI
- afișare prețuri, promoții și comparații

## Cerințe

Pentru rulare locală ai nevoie de:
- Node.js 20 sau mai nou
- npm
- API-ul local disponibil la http://127.0.0.1:8000

## Rulare locală

Din acest folder:

npm install
$env:NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000"
npm run dev

Frontend-ul pornește implicit la:

http://localhost:3000

## Variabile de mediu

Aplicația folosește variabila:

NEXT_PUBLIC_API_BASE

Exemplu:

$env:NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000"

Această variabilă indică URL-ul backend-ului local folosit de interfața web.

## Workflow recomandat

Pentru workflow-ul complet din rădăcina repository-ului pot fi folosite scripturile:

.\scripts\dev\start-local.ps1
.\scripts\dev\stop-local.ps1

Aceste scripturi sunt utile pentru pornirea și oprirea rapidă a mediului local de dezvoltare.

## Ce conține acest folder

În apps/web se află partea de frontend a proiectului:
- pagini și rute Next.js
- componente UI
- logică client pentru interacțiunea cu API-ul
- configurarea aplicației web locale

## Observații

- frontend-ul este gândit pentru utilizare locală în workflow-ul actual al proiectului
- backend-ul rulează în mod normal pe 127.0.0.1:8000
- aplicația web rulează în mod normal pe localhost:3000
- pentru contextul complet al proiectului, vezi README.md din rădăcina repository-ului

## Scope

Acest folder conține doar frontend-ul web.

Pentru arhitectura completă, backend, scripturi locale și informații generale despre proiect, vezi fișierul README.md din rădăcina repository-ului.
