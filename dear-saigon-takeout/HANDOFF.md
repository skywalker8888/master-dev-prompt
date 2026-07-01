# Dear Saigon Takeout — Project Handoff
**Client:** Dear Saigon Burlington  
**Address:** 2405 Fairview St, Burlington, ON L7M 1B3  
**Delivered by:** UseZest / Sky Walker  
**Last updated:** July 1, 2026

---

## What Was Built

A complete **AI phone ordering system** for Dear Saigon Takeout, consisting of:

| File | Purpose |
|---|---|
| `TakeOut AI System.dc.html` | Production takeout menu page — deploy this |
| `index.html` | Simpler version of the menu page (fallback) |
| `menu-data.json` | Full menu in structured JSON — import into Zest/Clover |
| `ai-phone-integration.js` | Webhook handler: Zest → Clover POS + SMS + Notion log |
| `branding-guide.md` | Colours, fonts, voice & tone, QR tent copy |
| `deployment-checklist.md` | Step-by-step launch tasks with status tracking |
| `staff-training-script.md` | 15-min staff training + kitchen quick-reference card |

---

## How It Works

```
Customer scans QR code on table
        ↓
Browses menu on TakeOut AI System.dc.html
        ↓
Calls (647) 932-2932 — Zest AI answers 24/7
        ↓
AI takes order by item code or name
        ↓
Zest fires webhook → ai-phone-integration.js
        ↓
   ┌────┴────┐
   ↓         ↓
Clover    SMS to customer
POS       (order confirmation)
   ↓
Notion log (optional)
```

---

## Credentials & Accounts

| Service | URL | Notes |
|---|---|---|
| Zest dashboard | usezest.ca/settings | AI phone config |
| Zest call logs | usezest.ca/calls | Review all calls |
| Clover POS | clover.com | Receives AI orders |
| Notion workspace | app.notion.com | Source of truth |
| Instagram | @dearsaigonburlington | Content calendar ready |

---

## Critical Open Items Before Go-Live

1. **Replace fake transfer number** — `+12125559876` in Zest settings is non-functional
2. **Verify all menu prices** — current prices in HTML/JSON are estimates
3. **Reconcile hours** — Zest shows Thu–Sun; Notion shows Mon–Sun open
4. **Provision local 905/289 number** — only after integration test passes
5. **Load menu into Zest Knowledge tab** — so AI can answer menu questions

---

## Key Phone Numbers

| Purpose | Number |
|---|---|
| AI ordering line (Zest) | +1 (647) 932-2932 |
| Human line (reservations) | +1 (647) 394-2518 |
| Yelp alternate (unverified) | (905) 633-8388 |

---

## Contacts

- **Owner/Admin:** Confirm with Sky Walker
- **Zest support:** support@usezest.ca
- **Clover support:** 1-855-853-8340

---

## Deployment (5 minutes)

1. Go to **netlify.com/drop**
2. Drag the `dear-saigon-takeout/` folder onto the page
3. Netlify gives you a live URL instantly
4. Share the URL with the client — done

For a custom domain (e.g. `order.dearsaigon.com`), use Vercel:
```bash
npx vercel dear-saigon-takeout/
```
Then add a CNAME record in your DNS.

---

## Project History

- **Apr 2026** — UseZest name research & positioning
- **May 2026** — Dear Saigon source-of-truth Notion databases built
- **Jun 2026** — Zest AI phone set up, Dear Saigon call diagnostic
- **Jun 27** — Voice call diagnostic session
- **Jun 29** — Dear Saigon dashboard audit (Tony's Pizza → Dear Saigon)
- **Jul 1** — Full takeout page + integration package delivered ← *you are here*
