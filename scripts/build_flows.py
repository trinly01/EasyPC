"""Create EasyPC Directus flows + operations (idempotent).

Flows:
  easypc_generate_wo_number  — items.create on work_orders -> assign WO-YYYY-NNNN
  easypc_status_milestone    — items.update status change -> create update row
  easypc_notify_on_update    — items.create on updates (notify=true) -> email
  easypc_warranty_stamp      — items.update status=released -> service_warranty_until
  easypc_unclaimed_reminder  — disabled placeholder (needs batch design)

NOTE: PATCH /relations crashes this instance; flows/ops are unaffected.
"""

import json
import os
import sys
import urllib.request
import urllib.error

BASE = "https://likha-playground.zyberlab.com"
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")
if not TOKEN:
    sys.exit("Set DIRECTUS_TOKEN env var")


def api(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "curl/8.5.0"},
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def flow_id(name):
    st, res = api("GET", f"/flows?filter%5Bname%5D%5B_eq%5D={name}")
    return res["data"][0]["id"] if st == 200 and res.get("data") else None


def create_flow(name, icon, trigger, options, status="active", accountability="all"):
    fid = flow_id(name)
    if fid:
        print(f"  = flow {name} exists")
        return fid
    st, res = api("POST", "/flows", {
        "name": name, "icon": icon, "trigger": trigger, "options": options,
        "status": status, "accountability": accountability})
    if st != 200:
        print(f"  ! flow {name} FAILED {st}: {json.dumps(res)[:300]}")
        return None
    print(f"  + flow {name}")
    return res["data"]["id"]


def create_op(fid, key, name, type_, options, x, y):
    st, res = api("GET", f"/operations?filter%5Bflow%5D%5B_eq%5D={fid}&filter%5Bkey%5D%5B_eq%5D={key}")
    if st == 200 and res.get("data"):
        return res["data"][0]["id"]
    st, res = api("POST", "/operations", {
        "flow": fid, "key": key, "name": name, "type": type_,
        "position_x": x, "position_y": y, "options": options})
    if st != 200:
        print(f"  ! op {name} FAILED {st}: {json.dumps(res)[:300]}")
        return None
    return res["data"]["id"]


def link_op(opid, resolve=None, reject=None):
    api("PATCH", f"/operations/{opid}", {"resolve": resolve, "reject": reject})


def set_entry(fid, first_op_id):
    api("PATCH", f"/flows/{fid}", {"operation": first_op_id})


# ============================================================
# FLOW 1: easypc_generate_wo_number
# items.create easypc_work_orders -> count -> format -> update
# ============================================================
fid = create_flow("easypc_generate_wo_number", "tag", "event",
                  {"type": "action", "scope": ["items.create"], "collections": ["easypc_work_orders"]})
if fid:
    o1 = create_op(fid, "count", "Count work orders", "item-read",
                   {"collection": "easypc_work_orders",
                    "query": {"aggregate": {"count": "id"}}, "permissions": "$full"}, 0, 0)
    o2 = create_op(fid, "format", "Format WO number", "exec",
                   {"code": (
                       "module.exports = async function(data){\n"
                       "  const c = data.$last;\n"
                       "  let n = Array.isArray(c) ? (c[0] && c[0].count) : (c && c.count);\n"
                       "  if (n && typeof n === 'object') n = n.id;\n"
                       "  n = parseInt(n) || 1;\n"
                       "  const t = data.$trigger || {};\n"
                       "  const key = t.key || (t.payload && (t.payload.key || (t.payload.keys||[])[0])) || (t.keys||[])[0];\n"
                       "  const yr = new Date().getFullYear();\n"
                       "  return { key: key, num: 'WO-' + yr + '-' + String(n).padStart(4,'0') };\n"
                       "}")}, 0, 120)
    o3 = create_op(fid, "setnum", "Set work_order_number", "item-update",
                   {"collection": "easypc_work_orders",
                    "key": "{{$last.key}}",
                    "payload": {"work_order_number": "{{$last.num}}"},
                    "permissions": "$full"}, 0, 240)
    if o1 and o2 and o3:
        link_op(o1, resolve=o2); link_op(o2, resolve=o3); set_entry(fid, o1)
        print("    chained count -> format -> setnum")

# ============================================================
# FLOW 2: easypc_status_milestone
# items.update easypc_work_orders -> check notifiable -> create update row
# ============================================================
NOTIFIABLE = ["testing", "awaiting_approval", "ready_for_release", "released"]
MSGS = {
    "testing": "Repair work on your unit is complete and it is now in final testing.",
    "awaiting_approval": "Our technician has findings for your approval. Please check the assessment.",
    "ready_for_release": "Your unit passed final testing and is ready for pickup. Please bring your Job Order No. and a valid ID.",
    "released": "Your unit has been released. Thank you for choosing EasyPC!",
}
fid = create_flow("easypc_status_milestone", "flag", "event",
                  {"type": "action", "scope": ["items.update"], "collections": ["easypc_work_orders"]})
if fid:
    msgs_js = json.dumps(MSGS)
    o1 = create_op(fid, "check", "Check status change", "exec",
                   {"code": (
                       "module.exports = async function(data){\n"
                       "  const t = data.$trigger || {};\n"
                       "  const p = t.payload || {};\n"
                       f"  const msgs = {msgs_js};\n"
                       "  const st = p.status;\n"
                       "  const key = (t.keys||[])[0] || (p.keys||[])[0] || p.key || t.key;\n"
                       "  if (!st || !msgs[st]) return { go: false };\n"
                       "  return { go: true, key: key, status: st, msg: msgs[st] };\n"
                       "}")}, 0, 0)
    o2 = create_op(fid, "gate", "Notifiable?", "condition",
                   {"filter": {"go": {"_eq": True}}}, 0, 120)
    o3 = create_op(fid, "mkupdate", "Create update row", "item-create",
                   {"collection": "easypc_work_order_updates",
                    "payload": {
                        "work_order": "{{$last.key}}",
                        "update_type": "milestone",
                        "milestone": "{{$last.status}}",
                        "message": "{{$last.msg}}",
                        "notify_customer": True},
                    "permissions": "$full"}, 0, 240)
    if o1 and o2 and o3:
        link_op(o1, resolve=o2)
        # condition op resolve data is the $last from o1; reject chain ends
        link_op(o2, resolve=o3); set_entry(fid, o1)
        print("    chained check -> gate -> mkupdate")

# ============================================================
# FLOW 3: easypc_notify_on_update
# items.create easypc_work_order_updates (notify=true) -> email
# Requires EMAIL_* env configured on the server.
# ============================================================
fid = create_flow("easypc_notify_on_update", "mail", "event",
                  {"type": "action", "scope": ["items.create"], "collections": ["easypc_work_order_updates"]})
if fid:
    o1 = create_op(fid, "check", "Notify flag set?", "exec",
                   {"code": (
                       "module.exports = async function(data){\n"
                       "  const t = data.$trigger || {};\n"
                       "  const p = t.payload || {};\n"
                       "  const key = t.key || p.key || (t.keys||[])[0] || (p.keys||[])[0];\n"
                       "  return { go: p.notify_customer !== false && p.notify_customer !== 0, key: key };\n"
                       "}")}, 0, 0)
    o2 = create_op(fid, "gate", "Should notify?", "condition",
                   {"filter": {"go": {"_eq": True}}}, 0, 120)
    o3 = create_op(fid, "readupd", "Read update", "item-read",
                   {"collection": "easypc_work_order_updates",
                    "key": "{{$last.key}}",
                    "query": {"fields": ["message", "work_order.work_order_number",
                                          "work_order.customer.email", "work_order.customer.name"]},
                    "permissions": "$full"}, 0, 240)
    o4 = create_op(fid, "buildmail", "Build email", "exec",
                   {"code": (
                       "module.exports = async function(data){\n"
                       "  const u = data.$last || {};\n"
                       "  const wo = u.work_order || {};\n"
                       "  const cust = wo.customer || {};\n"
                       "  return {\n"
                       "    to: cust.email || '',\n"
                       "    subject: 'EasyPC update — ' + (wo.work_order_number || 'your work order'),\n"
                       "    body: '<p>Hi ' + (cust.name || 'customer') + ',</p><p>' + (u.message || '') + '</p><p>Work Order: <b>' + (wo.work_order_number || '') + '</b></p><p>— EasyPC / Tech It Easy</p>'\n"
                       "  };\n"
                       "}")}, 0, 360)
    o5 = create_op(fid, "sendmail", "Send email", "mail",
                   {"to": "{{$last.to}}", "subject": "{{$last.subject}}",
                    "body": "{{$last.body}}", "type": "html"}, 0, 480)
    o6 = create_op(fid, "stampsent", "Stamp sent_at", "item-update",
                   {"collection": "easypc_work_order_updates",
                    "key": "{{$trigger.key}}",
                    "payload": {"notification_sent_at": "{{$timestamp}}"},
                    "permissions": "$full"}, 0, 600)
    if all([o1, o2, o3, o4, o5, o6]):
        link_op(o1, resolve=o2); link_op(o2, resolve=o3); link_op(o3, resolve=o4)
        link_op(o4, resolve=o5); link_op(o5, resolve=o6); set_entry(fid, o1)
        print("    chained check -> gate -> readupd -> buildmail -> sendmail -> stampsent")

# ============================================================
# FLOW 4: easypc_warranty_stamp
# items.update status=released -> service_warranty_until (+30d)
# ============================================================
fid = create_flow("easypc_warranty_stamp", "verified", "event",
                  {"type": "action", "scope": ["items.update"], "collections": ["easypc_work_orders"]})
if fid:
    o1 = create_op(fid, "check", "Released?", "exec",
                   {"code": (
                       "module.exports = async function(data){\n"
                       "  const t = data.$trigger || {};\n"
                       "  const p = t.payload || {};\n"
                       "  if (p.status !== 'released') return { go: false };\n"
                       "  const key = (t.keys||[])[0] || (p.keys||[])[0] || p.key || t.key;\n"
                       "  const rel = p.released_at ? new Date(p.released_at) : new Date();\n"
                       "  const DAYS = 30; // labor warranty — adjust per shop policy\n"
                       "  const until = new Date(rel.getTime() + DAYS*86400000).toISOString().slice(0,10);\n"
                       "  return { go: true, key: key, until: until };\n"
                       "}")}, 0, 0)
    o2 = create_op(fid, "gate", "Should stamp?", "condition",
                   {"filter": {"go": {"_eq": True}}}, 0, 120)
    o3 = create_op(fid, "stamp", "Set service_warranty_until", "item-update",
                   {"collection": "easypc_work_orders",
                    "key": "{{$last.key}}",
                    "payload": {"service_warranty_until": "{{$last.until}}"},
                    "permissions": "$full"}, 0, 240)
    if o1 and o2 and o3:
        link_op(o1, resolve=o2); link_op(o2, resolve=o3); set_entry(fid, o1)
        print("    chained check -> gate -> stamp")

# ============================================================
# FLOW 5: easypc_unclaimed_reminder — disabled placeholder
# ============================================================
fid = create_flow("easypc_unclaimed_reminder", "schedule", "schedule",
                  {"cron": "0 9 * * *"}, status="inactive")
if fid:
    o1 = create_op(fid, "note", "Design note", "log",
                   {"message": "TODO: batch-iterate ready_for_release WOs older than N days -> reminder emails; >30d -> status unclaimed. Per-item loops need request-op batching or a custom endpoint."},
                   0, 0)
    if o1:
        set_entry(fid, o1)

print("\nFlows done.")
