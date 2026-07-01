# Dear Saigon Takeout — Deployment Checklist

## Status Key
- [ ] Not started
- [x] Complete
- [~] In progress

---

## PHASE 1 — Zest Dashboard (usezest.ca/settings)

- [ ] **Business name** → `Dear Saigon Takeout`
- [ ] **Address** → `2405 Fairview St, Burlington, ON L7M 1B3` ✓ already set
- [ ] **Timezone** → `America/Toronto (New York)` ✓ already set
- [ ] **Hours** → Confirm with client:
  - Thu–Sun 11 AM – 8 PM (currently in Zest)
  - Canonical from Notion: Mon–Thu 11–9, Fri–Sat 11–10, Sun 11–9
  - **ACTION:** Update Zest hours to match Notion source of truth
- [ ] **Transfer phone number** → Replace `+12125559876` (fake!) with real owner number
- [ ] **Greeting script** → `Thank you for calling Dear Saigon Takeout! How can I help you today — are you looking to place a takeout order, ask about our menu, or make a reservation?`
- [ ] **Upsell rules** → Add from `menu-data.json` → `upsell_rules` (7 rules)
- [ ] **Save all changes**

---

## PHASE 2 — Menu Verification

- [ ] Confirm **all prices** with client (current prices are estimates)
- [ ] Confirm **P7 item** exists or skip (gap between P6 and P8 in Notion notes)
- [ ] Confirm **Mon–Wed hours** — currently Closed in Zest, open in Notion data
- [ ] Confirm **Yelp number** (905) 633-8388 — valid secondary or outdated?
- [ ] Load full menu into Zest **Knowledge / Menu tab**
- [ ] Test AI can answer: "What's the difference between P8 and P9?"

---

## PHASE 3 — Integration Test Calls

- [ ] Call `+1 (647) 932-2932`
- [ ] Confirm greeting says **"Dear Saigon Takeout"** (not "Dear Saigon" or "Tony's Pizza")
- [ ] Place test order: *"I'd like a P9 Dear Saigon Pho and a side of spring rolls"*
- [ ] Confirm order appears in **Clover POS**
- [ ] Confirm **SMS confirmation** received (if Twilio configured)
- [ ] Confirm **Notion order log** entry created (if configured)
- [ ] Test upsell: order P1, confirm AI offers P11 add-on

---

## PHASE 4 — Deploy Takeout Page

- [ ] Verify prices in `TakeOut AI System.dc.html` match confirmed menu
- [ ] Deploy HTML file to one of:
  - **Netlify Drop** → drag-and-drop at netlify.com/drop (free, instant)
  - **Vercel** → `npx vercel dear-saigon-takeout/` (free, custom domain support)
  - **Dear Saigon website** → Add as `/takeout` page on dearsaigon.com
- [ ] Test on mobile (iPhone + Android)
- [ ] Test OPEN/CLOSED badge shows correct status
- [ ] Test all 9 category nav links scroll correctly
- [ ] Tap phone number — confirm it dials on mobile

---

## PHASE 5 — Local Number (905/289)

> **Do this LAST — only after Phase 3 passes completely**

- [ ] In Zest dashboard → Phone Settings → provision local `905` or `289` number
- [ ] Update Google Business Profile phone number
- [ ] Update Yelp listing
- [ ] Update Facebook page
- [ ] Update website (dearsaigon.com)
- [ ] Update QR code table tents with new number
- [ ] Print and place new table tents

---

## PHASE 6 — Staff Training

- [ ] Owner briefed on what the AI handles (orders, menu Qs, hours)
- [ ] Owner briefed on what AI does NOT do (reservations → transfers to real number)
- [ ] Staff know to check Clover for AI-placed orders
- [ ] Staff know to watch for SMS-confirmed order names at pickup
- [ ] AI can be paused at: usezest.ca/settings → Danger Zone → Pause AI

---

## PHASE 7 — Marketing Launch

- [ ] Instagram @dearsaigonburlington — activate content calendar
- [ ] First post: "You can now order by phone with our AI! Call (local number)"
- [ ] QR code table tents printed and placed on all tables
- [ ] Google Business Profile updated with ordering phone number
- [ ] Ask first 10 AI-order customers for a Google review

---

## Emergency Contacts

| Issue | Action |
|---|---|
| AI not answering | usezest.ca/settings → check AI status |
| Wrong orders to Clover | Check Zest call logs at usezest.ca/calls |
| Greeting wrong name | Update greeting script, click Save |
| POS not receiving | Check Clover integration at usezest.ca/settings |
| Client complaint | Transfer to owner at real number (update first!) |
