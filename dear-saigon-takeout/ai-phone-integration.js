/**
 * Dear Saigon Takeout — Zest AI Phone Integration
 * Deploy as a Node.js webhook handler or paste into your Zest custom-code panel.
 *
 * Responsibilities:
 *  - Validate inbound Zest webhook calls
 *  - Parse order payloads and apply upsell logic
 *  - Forward confirmed orders to Clover POS
 *  - Send SMS order confirmation to caller
 *  - Log every transaction to Notion
 */

'use strict';

const ZEST_WEBHOOK_SECRET = process.env.ZEST_WEBHOOK_SECRET;
const CLOVER_API_TOKEN    = process.env.CLOVER_API_TOKEN;
const CLOVER_MERCHANT_ID  = process.env.CLOVER_MERCHANT_ID;
const NOTION_TOKEN        = process.env.NOTION_TOKEN;
const NOTION_DB_ID        = process.env.NOTION_ORDERS_DB_ID;
const TWILIO_SID          = process.env.TWILIO_ACCOUNT_SID;
const TWILIO_TOKEN        = process.env.TWILIO_AUTH_TOKEN;
const TWILIO_FROM         = process.env.TWILIO_FROM_NUMBER; // e.g. "+16479322932"

// ── MENU (mirrors menu-data.json — keep in sync) ──────────────────────────────
const MENU_INDEX = {
  A1:  { name: 'Crispy Spring Rolls',        price: 8.00  },
  A2:  { name: 'Fresh Rolls',                price: 9.00  },
  A3:  { name: 'Satay Chicken Skewers',      price: 10.00 },
  P1:  { name: 'Rare Beef Pho',              price: 17.00 },
  P2:  { name: 'Beef Brisket Pho',           price: 17.00 },
  P3:  { name: 'Rare Beef & Brisket Pho',    price: 18.00 },
  P4:  { name: 'Beef Meatball Pho',          price: 17.00 },
  P5:  { name: 'Chicken Pho',                price: 16.00 },
  P6:  { name: 'Vegetarian Pho',             price: 15.00 },
  P8:  { name: 'House Special Pho',          price: 20.00 },
  P9:  { name: 'Dear Saigon Pho',            price: 21.00 },
  P10: { name: 'Bún Bò Huế',                price: 18.00 },
  P11: { name: 'Big Beef Bone Add-On',       price: 4.00  },
  S1:  { name: 'Beef Satay Noodle Soup',     price: 18.00 },
  S2:  { name: 'Chicken Satay Noodle Soup',  price: 17.00 },
  S3:  { name: 'Shrimp Satay Noodle Soup',   price: 18.00 },
  S4:  { name: 'Mixed Satay Noodle Soup',    price: 20.00 },
  T1:  { name: 'Shrimp Tom Yum',             price: 18.00 },
  T2:  { name: 'Chicken Tom Yum',            price: 17.00 },
  T3:  { name: 'Mixed Seafood Tom Yum',      price: 20.00 },
  PT1: { name: 'Chicken Pad Thai',           price: 17.00 },
  PT2: { name: 'Shrimp Pad Thai',            price: 18.00 },
  PT3: { name: 'Beef Pad Thai',              price: 18.00 },
  PT4: { name: 'Vegetarian Pad Thai',        price: 15.00 },
  V1:  { name: 'Grilled Chicken Bún',        price: 16.00 },
  V2:  { name: 'Grilled Pork Bún',           price: 16.00 },
  V3:  { name: 'Shrimp & Pork Bún',          price: 17.00 },
  V4:  { name: 'Spring Roll Bún',            price: 16.00 },
  R1:  { name: 'Grilled Chicken Rice',       price: 16.00 },
  R2:  { name: 'Grilled Pork Chop Rice',     price: 16.00 },
  R3:  { name: 'Lemongrass Beef Rice',       price: 17.00 },
  R4:  { name: 'Shrimp Fried Rice',          price: 17.00 },
  SP1: { name: 'Lemongrass Beef Stir-Fry',   price: 18.00 },
  SP2: { name: 'Caramelized Ginger Fish',    price: 19.00 },
  SP3: { name: 'Crispy Tofu Bowl',           price: 15.00 },
  SP4: { name: 'Bánh Xèo',                  price: 17.00 },
  D1:  { name: 'Vietnamese Iced Coffee',     price: 5.00  },
  D2:  { name: 'Egg Coffee',                 price: 6.00  },
  D3:  { name: 'Fresh Lemonade',             price: 4.00  },
  D4:  { name: 'Thai Iced Tea',              price: 5.00  },
  D5:  { name: 'Soft Drink',                 price: 3.00  },
  D6:  { name: 'Bottled Water',              price: 2.00  },
};

const UPSELL_RULES = {
  P1: 'P11', P2: 'P11', P3: 'P11', P8: 'P11', P9: 'P11',
  A1: 'D1',
  SP4: 'D2',
};

// ── HELPERS ───────────────────────────────────────────────────────────────────

function computeTotal(items) {
  return items.reduce((sum, i) => {
    const entry = MENU_INDEX[i.code];
    return sum + (entry ? entry.price * (i.qty || 1) : 0);
  }, 0);
}

function applyUpsells(items) {
  const codes = new Set(items.map(i => i.code));
  const suggestions = [];
  for (const [trigger, suggest] of Object.entries(UPSELL_RULES)) {
    if (codes.has(trigger) && !codes.has(suggest)) {
      suggestions.push(suggest);
      if (suggestions.length >= 2) break; // max 2 per Zest config
    }
  }
  return suggestions.map(code => ({ code, item: MENU_INDEX[code] }));
}

function generateOrderId() {
  return `DS-${Date.now()}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
}

function estimatePickupMinutes(itemCount) {
  // Base 10 min + 2 min per item, capped at 30
  return Math.min(10 + itemCount * 2, 30);
}

// ── CLOVER POS ────────────────────────────────────────────────────────────────

async function sendToClover(order) {
  const lineItems = order.items.map(i => ({
    item: { id: i.clover_id || i.code },
    name: MENU_INDEX[i.code]?.name || i.code,
    price: Math.round((MENU_INDEX[i.code]?.price || 0) * 100), // cents
    unitQty: (i.qty || 1) * 1000,
  }));

  const res = await fetch(
    `https://api.clover.com/v3/merchants/${CLOVER_MERCHANT_ID}/orders`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CLOVER_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: `TAKEOUT — ${order.caller_name || order.caller_phone}`,
        note: `Order ID: ${order.id} | Via Zest AI Phone`,
        lineItems,
      }),
    }
  );

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Clover API error ${res.status}: ${err}`);
  }
  return res.json();
}

// ── SMS CONFIRMATION (Twilio) ─────────────────────────────────────────────────

async function sendSmsConfirmation(order) {
  if (!TWILIO_SID || !order.caller_phone) return;

  const itemList = order.items
    .map(i => `• ${i.qty || 1}x ${MENU_INDEX[i.code]?.name || i.code}`)
    .join('\n');

  const body = [
    `Dear Saigon Takeout — Order Confirmed! 🍜`,
    `Order #: ${order.id}`,
    itemList,
    `Total: $${order.total.toFixed(2)} (pay at pickup)`,
    `Ready in ~${order.pickup_eta} min`,
    `2405 Fairview St, Burlington`,
    `Questions? Call (647) 394-2518`,
  ].join('\n');

  const params = new URLSearchParams({ From: TWILIO_FROM, To: order.caller_phone, Body: body });

  await fetch(`https://api.twilio.com/2010-04-01/Accounts/${TWILIO_SID}/Messages.json`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${Buffer.from(`${TWILIO_SID}:${TWILIO_TOKEN}`).toString('base64')}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params,
  });
}

// ── NOTION LOGGING ────────────────────────────────────────────────────────────

async function logToNotion(order, cloverResult) {
  if (!NOTION_TOKEN || !NOTION_DB_ID) return;

  await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${NOTION_TOKEN}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      parent: { database_id: NOTION_DB_ID },
      properties: {
        'Order ID':    { title: [{ text: { content: order.id } }] },
        'Caller':      { rich_text: [{ text: { content: order.caller_phone || '' } }] },
        'Total':       { number: order.total },
        'Items':       { rich_text: [{ text: { content: order.items.map(i => `${i.qty||1}x ${i.code}`).join(', ') } }] },
        'ETA (min)':   { number: order.pickup_eta },
        'Clover ID':   { rich_text: [{ text: { content: cloverResult?.id || '' } }] },
        'Status':      { select: { name: 'Received' } },
        'Timestamp':   { date: { start: new Date().toISOString() } },
      },
    }),
  });
}

// ── MAIN WEBHOOK HANDLER ──────────────────────────────────────────────────────

/**
 * Express-style handler. Wire up as:
 *   app.post('/zest/webhook', webhookHandler);
 *
 * Or export as a serverless function (Vercel, Netlify, Cloudflare Workers).
 */
async function webhookHandler(req, res) {
  // 1. Validate Zest signature
  const sig = req.headers['x-zest-signature'];
  if (ZEST_WEBHOOK_SECRET && sig !== ZEST_WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const payload = req.body;
  if (!payload || !Array.isArray(payload.items) || payload.items.length === 0) {
    return res.status(400).json({ error: 'No items in order' });
  }

  // 2. Build order object
  const order = {
    id:           generateOrderId(),
    caller_phone: payload.caller_phone || null,
    caller_name:  payload.caller_name  || null,
    items:        payload.items,
    total:        computeTotal(payload.items),
    pickup_eta:   estimatePickupMinutes(payload.items.reduce((s, i) => s + (i.qty || 1), 0)),
    upsells:      applyUpsells(payload.items),
    received_at:  new Date().toISOString(),
  };

  // 3. Forward to Clover POS
  let cloverResult;
  try {
    cloverResult = await sendToClover(order);
  } catch (err) {
    console.error('[Clover]', err.message);
    return res.status(502).json({ error: 'POS unavailable', detail: err.message });
  }

  // 4. Send SMS + log to Notion (non-blocking — failures don't fail the order)
  await Promise.allSettled([
    sendSmsConfirmation(order),
    logToNotion(order, cloverResult),
  ]);

  // 5. Return response to Zest (used to read back to caller)
  return res.status(200).json({
    order_id:    order.id,
    total:       order.total,
    pickup_eta:  order.pickup_eta,
    upsells:     order.upsells,
    clover_id:   cloverResult?.id,
    message:     `Order confirmed! Your total is $${order.total.toFixed(2)}. Ready in about ${order.pickup_eta} minutes. See you at 2405 Fairview Street!`,
  });
}

module.exports = { webhookHandler, computeTotal, applyUpsells, MENU_INDEX };
