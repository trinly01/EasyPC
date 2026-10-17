"""Extend easypc_track_lookup: accept WO + customer phone (full or last-4)
as the lookup key, keeping the random tracking_token working too.

Rule: digits-only key -> phone match (suffix on normalized contact_no);
alnum key -> tracking_token exact match.
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')
FLOW = 'eedd97d4-5c26-4e47-a26f-040806686d70'

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json',
                 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

# --- new validate code: emits {wo, token, phone} -------------------------
code_validate = r'''module.exports = async function(data){
  const b = (data.$trigger && data.$trigger.body) || {};
  const wo = String(b.wo || "").trim().toUpperCase();
  // accept legacy `token` body field as well as new `key`
  const key = String(b.key || b.token || "").trim().toLowerCase();
  if (!/^WO-\d{4}-\d{4}$/.test(wo)) throw new Error("bad wo");
  if (!key) throw new Error("missing key");

  let token = "", phone = "";
  if (/^\d{4,15}$/.test(key)) {
    // phone: normalize +63/63 prefix to trunk 0 (e.g. 639171234567 -> 09171234567)
    phone = /^63\d{10}$/.test(key) ? "0" + key.slice(2) : key;
  } else if (/^[a-z0-9]{8,32}$/.test(key)) {
    token = key;
  } else {
    throw new Error("bad key");
  }
  return { wo: wo, token: token, phone: phone };
}'''

# --- shared auth clause for every SQL query ------------------------------
# Stored phone normalized the same way: 63XXXXXXXXXX -> 0XXXXXXXXXX
NORM = ("right(CASE WHEN regexp_replace(c.contact_no,'[^0-9]','','g') ~ '^63[0-9]{10}$' "
        "THEN '0' || substring(regexp_replace(c.contact_no,'[^0-9]','','g') from 3) "
        "ELSE regexp_replace(c.contact_no,'[^0-9]','','g') END, "
        "char_length('{{validate.phone}}')) = '{{validate.phone}}'")
AUTH = ("AND (w.tracking_token = '{{validate.token}}' "
        "OR ('{{validate.phone}}' <> '' AND " + NORM + "))")

sql_fetch = '''SELECT w.id, w.work_order_number, w.status, w.date_time_in::text AS date_time_in,
       w.released_at::text AS released_at,
       w.service_warranty_until::text AS service_warranty_until,
       w.video_call_link, w.unit_type, w.unit_brand_model,
       w.test_result, s.name AS store_name, s.code AS store_code
FROM easypc_work_orders w
LEFT JOIN easypc_stores s ON s.id = w.store
LEFT JOIN easypc_customers c ON c.id = w.customer
WHERE w.work_order_number = '{{validate.wo}}'
''' + AUTH + '''
LIMIT 1;'''

sql_updates = '''SELECT u.milestone, u.message, u.date_created::text AS date_created
FROM easypc_work_order_updates u
JOIN easypc_work_orders w ON w.id = u.work_order
LEFT JOIN easypc_customers c ON c.id = w.customer
WHERE w.work_order_number = '{{validate.wo}}'
''' + AUTH + '''
ORDER BY u.date_created ASC;'''

sql_services = '''SELECT sv.name, js.charged_price
FROM easypc_work_orders_services js
JOIN easypc_work_orders w ON w.id = js.easypc_work_orders_id
LEFT JOIN easypc_customers c ON c.id = w.customer
JOIN easypc_services sv ON sv.id = js.easypc_services_id
WHERE w.work_order_number = '{{validate.wo}}'
''' + AUTH + ';'

# op ids from earlier fetch
OPS = {
    'validate': '08664764-db65-4046-8882-71c465563553',
    'fetch': '8a3660e8-c756-4f5e-b228-f5e6652979e3',
    'fetch_updates': 'e91ce3d7-b18f-4de2-b54d-72c1cf28a854',
    'fetch_services': '14ae511e-b0da-436a-99ee-f309d03b5a43',
}

for key, opts in [
    ('validate', {'code': code_validate}),
    ('fetch', {'sql': sql_fetch}),
    ('fetch_updates', {'sql': sql_updates}),
    ('fetch_services', {'sql': sql_services}),
]:
    st, res = api('PATCH', '/operations/' + OPS[key], {'options': opts})
    print(key, st, '' if st == 200 else res)

# clear cache so new op code is picked up
st, res = api('POST', '/utils/cache/clear')
print('cache clear:', st)
