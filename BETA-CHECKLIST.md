---  
  
## `BETA-CHECKLIST.md`  
  
```md id="30893"  
# BETA CHECKLIST — price-watch-ro  
  
## Regula etapei curente  
  
Scop curent:  
- packaging beta  
- cleanup minim  
- polish final UI  
- fără reluarea debugging-ului vechi, în afara bugurilor reale blocate  
  
---  
  
## 1. Repo / structură  
  
- [ ] Repo Git inițializat  
- [ ] `apps/web` este folder normal în repo, nu embedded repo  
- [ ] `.gitignore` valid  
- [ ] `.env.example` valid  
- [ ] `docs/` există  
- [ ] `docs/price-watch-ro-beta-docs.docx` există  
- [ ] `README-beta.md` există  
- [ ] `BETA-CHECKLIST.md` există  
- [ ] `start-dev.ps1` există  
- [ ] `stop-dev.ps1` există  
- [ ] `refresh-rendered-item.ps1` există  
  
---  
  
## 2. Curățenie minimă  
  
- [ ] `.venv` este ignorat  
- [ ] baze SQLite locale sunt ignorate  
- [ ] `freshful_profile` / profilul Chrome local este ignorat  
- [ ] logurile și cache-urile nu intră în repo  
- [ ] nu există fișiere temporare inutile în root  
- [ ] nu există scripturi duplicate inutile în root  
  
---  
  
## 3. Pornire locală  
  
- [ ] `start-dev.ps1` rulează fără erori critice  
- [ ] API pornește pe `127.0.0.1:8000`  
- [ ] frontend pornește pe `localhost:3000`  
- [ ] `stop-dev.ps1` oprește procesele relevante  
- [ ] `GET /health` răspunde corect  
  
Test rapid:  
  
```powershell  
curl.exe http://127.0.0.1:8000/health  
