# price-watch-ro — Beta local  
  
Aplicație locală pentru liste și alerte de preț pentru Freshful.  
  
## Stare beta curentă  
  
Funcțional:  
- watchlists  
- dashboard  
- items detailed  
- edit target price  
- activ / inactiv  
- refresh static din UI  
- refresh promo / rendered prin script local PowerShell + Chrome CDP  
  
## Stack  
  
- FastAPI  
- Next.js  
- SQLite  
- Playwright + Chrome CDP pentru refresh promo  
  
## Cerințe  
  
- Windows  
- PowerShell  
- Python cu virtualenv configurat în `services/api/.venv`  
- Node.js pentru frontend  
- Google Chrome instalat  
  
## Pornire rapidă  
  
### 1. Pornește mediul local  
  
```powershell  
cd D:\dev\projects\price-watch-ro  
.\start-dev.ps1  
