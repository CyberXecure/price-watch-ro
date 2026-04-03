
---

## 2 `BETA-CHECKLIST.md`

Fișier:
`D:\dev\projects\price-watch-ro\BETA-CHECKLIST.md`

```md id="42102"
# Beta checklist

## Backend
- [ ] API pornește fără erori
- [ ] `http://127.0.0.1:8000/health` răspunde
- [ ] `http://127.0.0.1:8000/dashboard/summary` răspunde
- [ ] `http://127.0.0.1:8000/watchlists/1/items/detailed` răspunde

## Frontend
- [ ] frontend pornește fără erori
- [ ] `/lists` se încarcă
- [ ] `/lists/1` se încarcă
- [ ] target price se poate edita
- [ ] activ / inactiv funcționează
- [ ] refresh static funcționează

## Promo rendered flow
- [ ] Chrome CDP răspunde pe `9222`
- [ ] sesiunea Freshful este activă în Chrome debug
- [ ] `refresh-rendered-item.ps1` rulează fără erori
- [ ] itemul promo se actualizează în DB/API
- [ ] UI afișează snapshotul promo nou

## Validare minimă produs promo
- [ ] `latest_price_total` corect
- [ ] `latest_old_price` corect
- [ ] `latest_promo_label` corect
- [ ] `latest_discount_percent` corect
- [ ] `latest_captured_at` nou

## Oprire
- [ ] `stop-dev.ps1` oprește API
- [ ] `stop-dev.ps1` oprește frontend
- [ ] `stop-dev.ps1` oprește Chrome debug, dacă este cazul