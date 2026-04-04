# price-watch-ro — README beta local  
  
## Scop  
  
`price-watch-ro` este o aplicație locală beta pentru urmărirea prețurilor produselor Freshful.  
  
În stadiul actual, proiectul este orientat pe:  
- liste de produse urmărite  
- import de produse Freshful  
- preț actual, preț vechi, promo și preț unitar  
- preț țintă per produs  
- refresh static  
- refresh promo / rendered  
- status de preț: `Chilipir`, `Preț cinstit`, `Răsfăț`  
  
Această versiune este destinată testării locale, validării fluxurilor principale și pregătirii pentru o etapă ulterioară de packaging / open-source.  
  
---  
  
## Stare beta validată  
  
Stare validă curentă:  
  
- FastAPI + Next.js + SQLite  
- Watchlists funcționează  
- Dashboard funcționează  
- Items detailed funcționează  
- Edit target price funcționează  
- Activ / Inactiv funcționează  
- Import produse Freshful funcționează  
- Refresh static funcționează din UI  
- Refresh promo / rendered funcționează  
- Chrome trebuie pornit cu remote debugging pe `9222` pentru promo refresh  
- Produsele inactive sunt ascunse implicit din lista principală  
- Fișiere beta finale există:  
  - `README-beta.md`  
  - `BETA-CHECKLIST.md`  
  - `start-dev.ps1`  
  - `stop-dev.ps1`  
  - `refresh-rendered-item.ps1`  
  
---  
  
## Structură proiect  
  
```text  
D:\dev\projects\price-watch-ro  
│  
├─ apps  
│  └─ web  
│  
├─ services  
│  └─ api  
│  
├─ docs  
│  └─ price-watch-ro-beta-docs.docx  
│  
├─ README-beta.md  
├─ BETA-CHECKLIST.md  
├─ start-dev.ps1  
├─ stop-dev.ps1  
├─ refresh-rendered-item.ps1  
├─ .env.example  
└─ .gitignore  
