"""Build the EasyPC schema in Directus (idempotent).

Creates all easypc_* collections, fields, relations, M2M junctions,
tab layout, roles/permissions, and seed data. Safe to re-run: existing
objects are skipped.

Usage:  set DIRECTUS_TOKEN=... ; python build_schema.py
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
        BASE + path,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.5.0",  # CF blocks python/browser-spoof UAs
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")[:500]}


def exists(path):
    st, _ = api("GET", path)
    return st == 200


def create_collection(name, meta, fields):
    if exists(f"/collections/{name}"):
        print(f"  = collection {name} exists, skipping")
        return
    body = {"collection": name, "meta": meta, "schema": {"name": name}, "fields": fields}
    st, res = api("POST", "/collections", body)
    if st != 200:
        print(f"  ! create {name} FAILED {st}: {json.dumps(res)[:400]}")
    else:
        print(f"  + collection {name}")


def create_field(col, spec):
    if exists(f"/fields/{col}/{spec['field']}"):
        print(f"  = field {col}.{spec['field']} exists, skipping")
        return
    st, res = api("POST", f"/fields/{col}", spec)
    if st != 200:
        print(f"  ! field {col}.{spec['field']} FAILED {st}: {json.dumps(res)[:300]}")
    else:
        print(f"  + field {col}.{spec['field']}")


def patch_field(col, field, meta):
    st, res = api("PATCH", f"/fields/{col}/{field}", {"meta": meta})
    if st != 200:
        print(f"  ! patch {col}.{field} FAILED {st}: {json.dumps(res)[:300]}")
    else:
        print(f"  ~ patched {col}.{field}")


def create_relation(col, field, related, meta=None):
    if exists(f"/relations/{col}/{field}"):
        print(f"  = relation {col}.{field} exists, skipping")
        return
    body = {"collection": col, "field": field, "related_collection": related}
    if meta:
        body["meta"] = meta
    st, res = api("POST", "/relations", body)
    if st != 200:
        print(f"  ! relation {col}.{field} FAILED {st}: {json.dumps(res)[:300]}")
    else:
        print(f"  + relation {col}.{field} -> {related}")


# ---------- field builders ----------

def f(field, type_, meta=None, schema=None):
    d = {"field": field, "type": type_}
    d["meta"] = meta or {}
    d["schema"] = schema or {}
    return d


def pk():
    return f("id", "uuid", {"hidden": True, "readonly": True, "interface": "input", "special": ["uuid"]}, {"is_primary_key": True, "length": 36})


def int_pk():
    return f("id", "integer", {"hidden": True, "interface": "input"}, {"is_primary_key": True, "has_auto_increment": True})


def audit():
    return [
        f("user_created", "uuid", {"special": ["user-created"], "interface": "select-dropdown-m2o", "display": "user", "hidden": True, "readonly": True, "width": "half"}),
        f("date_created", "timestamp", {"special": ["date-created"], "interface": "datetime", "display": "datetime", "hidden": True, "readonly": True, "width": "half"}),
        f("user_updated", "uuid", {"special": ["user-updated"], "interface": "select-dropdown-m2o", "display": "user", "hidden": True, "readonly": True, "width": "half"}),
        f("date_updated", "timestamp", {"special": ["date-updated"], "interface": "datetime", "display": "datetime", "hidden": True, "readonly": True, "width": "half"}),
    ]


def inp(field, required=False, width="half", group=None, note=None, sort=None, schema=None):
    m = {"interface": "input", "width": width}
    if required:
        m["required"] = True
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "string", m, schema or {})


def txt(field, group=None, note=None, sort=None):
    m = {"interface": "input-multiline", "width": "full"}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "text", m)


def boolean(field, group=None, note=None, sort=None, default=None):
    m = {"interface": "toggle", "width": "half"}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    s = {"default_value": default} if default is not None else {}
    return f(field, "boolean", m, s)


def integer(field, group=None, note=None, sort=None, default=None, width="half"):
    m = {"interface": "input", "width": width}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    s = {"default_value": default} if default is not None else {}
    return f(field, "integer", m, s)


def dec(field, group=None, note=None, sort=None, width="half"):
    m = {"interface": "input", "width": width}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "decimal", m, {"numeric_precision": 10, "numeric_scale": 2})


def dt(field, group=None, note=None, sort=None, date_only=False):
    m = {"interface": "datetime", "display": "datetime", "width": "half"}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "date" if date_only else "dateTime", m)


def dropdown(field, choices, group=None, note=None, sort=None, default=None, width="half", required=False):
    m = {
        "interface": "select-dropdown",
        "display": "labels",
        "width": width,
        "options": {"choices": [{"text": t, "value": v} for t, v in choices]},
        "display_options": {"choices": [{"text": t, "value": v} for t, v in choices]},
    }
    if required:
        m["required"] = True
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    s = {"default_value": default} if default else {}
    return f(field, "string", m, s)


def m2o(field, group=None, note=None, sort=None, template=None, width="half", required=False):
    m = {"interface": "select-dropdown-m2o", "display": "related-values", "width": width}
    if template:
        m["display_options"] = {"template": template}
    if required:
        m["required"] = True
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "uuid", m)


def tags(field, group=None, note=None, sort=None):
    m = {"interface": "tags", "width": "full"}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "json", m)


def jsoncode(field, group=None, note=None, sort=None):
    m = {"interface": "input-code", "options": {"language": "json"}, "width": "full"}
    if group:
        m["group"] = group
    if note:
        m["note"] = note
    if sort:
        m["sort"] = sort
    return f(field, "json", m)


def sort_field():
    return f("sort", "integer", {"interface": "input", "hidden": True})


def group_field(field, interface, parent=None, label=None, sort=None):
    m = {"interface": interface, "special": ["alias", "group", "no-data"], "width": "full"}
    if parent:
        m["group"] = parent
    if sort:
        m["sort"] = sort
    if label:
        m["translations"] = [{"language": "en-US", "translation": label}]
    return f(field, "alias", m)


# ---------- shared option lists ----------

PART_TYPES = [
    ("CPU", "cpu"), ("Motherboard", "motherboard"), ("RAM", "ram"), ("GPU", "gpu"),
    ("SSD / HDD", "storage"), ("PSU", "psu"), ("CPU Cooler", "cpu_cooler"), ("Case / Others", "case_other"),
]

STATUSES = [
    ("Registered", "registered"), ("Awaiting Assessment", "awaiting_assessment"),
    ("Assessing", "assessing"), ("Awaiting Approval", "awaiting_approval"),
    ("Approved", "approved"), ("Declined", "declined"),
    ("In Repair", "in_repair"), ("Testing", "testing"),
    ("Ready for Release", "ready_for_release"), ("Released", "released"),
    ("Cancelled", "cancelled"), ("Unclaimed", "unclaimed"),
]

DIAG_AREAS = [
    ("CPU", "cpu"), ("Motherboard", "motherboard"), ("RAM", "ram"), ("GPU", "gpu"),
    ("SSD / HDD", "storage"), ("PSU", "psu"), ("Cooling / Fans", "cooling_fans"),
    ("Ports / Audio / Wi-Fi", "ports_audio_wifi"), ("Laptop: Screen / Battery", "laptop_screen_battery"),
    ("OS / Software", "os_software"),
]

USER_TEMPLATE = "{{first_name}} {{last_name}}"


# ============================================================
# 1. LOOKUP + CUSTOMER COLLECTIONS
# ============================================================
print("== lookups ==")

create_collection("easypc_stores",
    {"icon": "store", "display_template": "{{code}} — {{name}}", "sort_field": "sort"},
    [pk(), sort_field(),
     inp("name", required=True, sort=1, width="half"),
     inp("code", required=True, sort=2, width="half", note="Short code, e.g. SMDASMA"),
     boolean("active", default=True, sort=3)] + audit())

create_collection("easypc_services",
    {"icon": "build", "display_template": "{{name}}", "sort_field": "sort"},
    [pk(), sort_field(),
     inp("key", required=True, sort=1, width="half", note="Stable machine key"),
     inp("name", required=True, sort=2, width="half"),
     dec("price", sort=3, note="Current catalog price (₱)"),
     boolean("active", default=True, sort=4)] + audit())

create_collection("easypc_parts_catalog",
    {"icon": "memory", "display_template": "{{name}}", "sort_field": "sort"},
    [pk(), sort_field(),
     inp("sku", sort=1, width="half", note="Shop/Odoo SKU"),
     inp("name", required=True, sort=2, width="half"),
     dropdown("part_type", PART_TYPES, sort=3),
     inp("brand", sort=4), inp("spec", sort=5),
     dec("price", sort=6, note="Current sell price (₱)"),
     integer("warranty_days", sort=7, note="Shop default warranty, days"),
     boolean("active", default=True, sort=8)] + audit())

create_collection("easypc_customers",
    {"icon": "person", "display_template": "{{name}} — {{contact_no}}"},
    [pk(),
     inp("name", required=True, sort=1),
     inp("contact_no", sort=2, note="Primary match key at intake"),
     inp("email", sort=3, note="Required for email updates"),
     txt("notes", sort=4)] + audit())


# ============================================================
# 2. CORE: easypc_work_orders
# ============================================================
print("== easypc_work_orders ==")

wo_fields = [
    pk(),
    # top-level (always visible above tabs)
    inp("work_order_number", sort=1, width="half",
        note="Public reference. Confirms RECEIPT only — not diagnosis or repair acceptance.",
        schema={"is_unique": True}),
    dropdown("status", STATUSES, default="registered", sort=2, required=True),

    # tab container + tab groups
    group_field("grp_tabs", "group-tabs", sort=3),
    group_field("grp_intake", "group-raw", parent="grp_tabs", label="Intake", sort=1),
    group_field("grp_unit", "group-raw", parent="grp_tabs", label="Unit & Service", sort=2),
    group_field("grp_parts", "group-raw", parent="grp_tabs", label="Parts & Photos", sort=3),
    group_field("grp_assessment", "group-raw", parent="grp_tabs", label="Assessment", sort=4),
    group_field("grp_work", "group-raw", parent="grp_tabs", label="Work Done", sort=5),
    group_field("grp_releasing", "group-raw", parent="grp_tabs", label="Releasing", sort=6),
    group_field("grp_updates", "group-raw", parent="grp_tabs", label="Updates", sort=7),

    # intake tab
    inp("job_order_no", group="grp_intake", sort=1, note="Handwritten No. from the paper form"),
    inp("odoo_ticket", group="grp_intake", sort=2, note="Odoo cross-reference (free text)"),
    m2o("store", group="grp_intake", sort=3, template="{{code}} — {{name}}"),
    dt("date_time_in", group="grp_intake", sort=4),
    dropdown("intake_path", [("Wait for assessment", "wait_for_assessment"), ("Leave device", "leave_device")],
             group="grp_intake", sort=5, note="Journey step 01"),
    m2o("customer", group="grp_intake", sort=6, template="{{name}} — {{contact_no}}", required=True, width="half"),
    m2o("received_by", group="grp_intake", sort=7, template=USER_TEMPLATE, note="Received by (RA-TECH)"),
    m2o("warranty_claim_of", group="grp_intake", sort=8, template="{{work_order_number}}",
        note="Set when this WO is a warranty claim against an earlier one"),

    # unit tab
    dropdown("unit_type", [("Desktop", "desktop"), ("Laptop", "laptop"), ("Loose parts", "loose_parts")],
             group="grp_unit", sort=1),
    inp("unit_brand_model", group="grp_unit", sort=2, note="Brand / model"),
    dropdown("password_handling", [("Not needed", "not_needed"), ("Customer to enter", "customer_to_enter")],
             group="grp_unit", sort=3, note="Never store the password itself"),
    txt("customer_concern", group="grp_unit", sort=4),
    boolean("terms_accepted", group="grp_unit", sort=6, note="I agree / Sang-ayon ako — signature on printed form"),
    dt("terms_accepted_at", group="grp_unit", sort=7),
    inp("terms_version", group="grp_unit", sort=8, note="Which T&C text was shown"),

    # parts & photos tab
    boolean("cpu_socket_pins_photographed", group="grp_parts", sort=1),
    integer("photo_count", group="grp_parts", sort=2, note="No. of photos"),

    # assessment tab
    txt("diagnosis_findings", group="grp_assessment", sort=2, note="Diagnosis / Findings"),
    txt("recommended_solution", group="grp_assessment", sort=3, note="Recommended Solution"),
    txt("additional_findings", group="grp_assessment", sort=4, note="Additional findings (testing)"),
    m2o("assessed_by", group="grp_assessment", sort=5, template=USER_TEMPLATE),
    dt("assessed_at", group="grp_assessment", sort=6),

    # releasing tab
    dropdown("test_result", [("Passed", "passed"), ("Failed", "failed")],
             group="grp_releasing", sort=1, note="Test Run / Boot Test"),
    txt("test_remarks", group="grp_releasing", sort=2),
    inp("so_number", group="grp_releasing", sort=3, note="Sales Order #"),
    dec("amount", group="grp_releasing", sort=4, note="₱ — should equal services + parts totals"),
    dropdown("old_parts_disposition", [("Returned", "returned"), ("None", "none"), ("Dispose", "dispose")],
             group="grp_releasing", sort=5, note="Old parts returned"),
    m2o("released_by", group="grp_releasing", sort=6, template=USER_TEMPLATE),
    dt("released_at", group="grp_releasing", sort=7),
    inp("receiver_name", group="grp_releasing", sort=8, note="Signature is on the printed form"),
    inp("receiver_id", group="grp_releasing", sort=9, note="Valid ID presented (T&C clause 6)"),
    dt("service_warranty_until", group="grp_releasing", sort=10, date_only=True,
       note="Labor warranty end = released_at + shop policy days"),
] + audit()

create_collection("easypc_work_orders",
    {"icon": "handyman", "display_template": "{{work_order_number}}", "color": "#26A69A"},
    wo_fields)


# ============================================================
# 3. CHILD COLLECTIONS
# ============================================================
print("== child collections ==")

create_collection("easypc_work_order_parts",
    {"icon": "list_alt", "hidden": True, "display_template": "{{part_type}} — {{brand_model}}", "sort_field": "sort"},
    [pk(), sort_field(),
     f("work_order", "uuid", {"hidden": True}),
     dropdown("part_type", PART_TYPES, sort=1, required=True),
     boolean("provided", sort=2, note="Provided at intake"),
     inp("brand_model", sort=3), inp("serial_no", sort=4),
     dropdown("condition", [("Good", "good"), ("With damage", "with_damage")], sort=5),
     inp("damage_notes", sort=6, width="full", note="Describe damage if any")] + audit())

create_collection("easypc_work_order_parts_used",
    {"icon": "inventory_2", "hidden": True, "display_template": "{{description}} x{{qty}}", "sort_field": "sort"},
    [pk(), sort_field(),
     f("work_order", "uuid", {"hidden": True}),
     m2o("catalog_item", sort=1, template="{{name}}", note="Empty = manual entry"),
     dropdown("price_source", [("Catalog", "catalog"), ("Manual", "manual")], sort=2,
              note="Provenance of unit_price"),
     dropdown("part_type", PART_TYPES, sort=3),
     inp("description", required=True, sort=4, width="full", note="What was charged — copied or typed"),
     integer("qty", sort=5, default=1),
     dec("unit_price", sort=6, note="The price at that time — never synced back"),
     dropdown("source", [("EasyPC", "easypc"), ("Customer supplied", "customer_supplied")], sort=7,
              note="Customer-supplied = ₱0, seller warranty"),
     m2o("approval", sort=8, template="{{kind}} — {{decision}}",
         note="Approval that authorized this line"),
     dropdown("warranty_provider", [("EasyPC", "easypc"), ("Seller", "seller"), ("None", "none")], sort=9),
     integer("warranty_days", sort=10, note="Defaults from catalog item"),
     dt("warranty_until", sort=11, date_only=True, note="released_at + warranty_days"),
     inp("notes", sort=12, width="full", note="e.g. which intake part it replaced")] + audit())

create_collection("easypc_job_processes",
    {"icon": "engineering", "hidden": True, "display_template": "{{process_type}}", "sort_field": "sort"},
    [pk(), sort_field(),
     f("work_order", "uuid", {"hidden": True}),
     dropdown("process_type", [("Cleaning", "cleaning"), ("Install / Upgrade", "install_upgrade"), ("Troubleshooting", "troubleshooting")],
              sort=1, required=True),
     tags("coverage", note="Ticked coverage keys — see form §3"),
     inp("coverage_other", sort=3, width="full", note="Others: ___"),
     m2o("done_by", sort=4, template=USER_TEMPLATE),
     dt("done_at", sort=5)] + audit())

create_collection("easypc_diagnostics",
    {"icon": "monitor_heart", "hidden": True, "display_template": "{{area}} — {{result}}", "sort_field": "sort"},
    [pk(), sort_field(),
     f("work_order", "uuid", {"hidden": True}),
     dropdown("area", DIAG_AREAS, sort=1, required=True),
     tags("tests", note="Test keys per area — see form §3"),
     jsoncode("metrics", note='{"duration_minutes":..,"max_temp_c":..,"health_percent":..,"battery_percent":..,"passes":..}'),
     txt("issues", note="Issue / Observations"),
     dropdown("result", [("Pass", "pass"), ("Fail", "fail"), ("Observation", "observation")], sort=5),
     m2o("tested_by", sort=6, template=USER_TEMPLATE),
     dt("tested_at", sort=7)] + audit())

create_collection("easypc_approvals",
    {"icon": "how_to_reg", "hidden": True, "display_template": "{{kind}} — {{decision}}"},
    [pk(),
     f("work_order", "uuid", {"hidden": True}),
     dropdown("kind", [("Assessment", "assessment"), ("Additional work", "additional_work")], sort=1, required=True),
     dt("informed_at", sort=2, note="Customer informed date/time"),
     dropdown("decision", [("Pending", "pending"), ("Approved", "approved"), ("Declined", "declined")],
              sort=3, default="pending"),
     dropdown("channel", [("Messenger", "messenger"), ("SMS", "sms"), ("Call", "call"), ("In person", "in_person")], sort=4),
     dt("decided_at", sort=5),
     txt("notes", note="Scope & cost approved"),
     m2o("recorded_by", sort=7, template=USER_TEMPLATE)] + audit())

create_collection("easypc_work_order_updates",
    {"icon": "notifications", "hidden": True, "display_template": "{{update_type}} — {{date_created}}"},
    [pk(),
     f("work_order", "uuid", {"hidden": True}),
     dropdown("update_type", [("Milestone", "milestone"), ("Technician note", "technician_note")], sort=1, required=True),
     dropdown("milestone", STATUSES, sort=2, note="For milestone type"),
     txt("message", note="Customer-facing text"),
     boolean("notify_customer", default=True, sort=4),
     dt("notification_sent_at", sort=5, note="Set by flow"),
     m2o("created_by", sort=6, template=USER_TEMPLATE, note="Technician who wrote it")] + audit())


# ============================================================
# 4. JUNCTION COLLECTIONS (M2M)
# ============================================================
print("== junctions ==")

create_collection("easypc_work_orders_services",
    {"icon": "import_export", "hidden": True, "sort_field": "sort"},
    [int_pk(), sort_field(),
     f("easypc_work_orders_id", "uuid", {"hidden": True}),
     f("easypc_services_id", "uuid", {"hidden": True}),
     dec("charged_price", note="Price snapshot at charge time — editable per order")])

create_collection("easypc_work_orders_files",
    {"icon": "import_export", "hidden": True, "sort_field": "sort"},
    [int_pk(), sort_field(),
     f("easypc_work_orders_id", "uuid", {"hidden": True}),
     f("directus_files_id", "uuid", {"hidden": True}),
     dropdown("category", [("Intake photo", "intake_photo"), ("CPU socket pins", "cpu_socket_pins"),
                           ("Damage", "damage"), ("Other", "other")], width="full")])


# ============================================================
# 5. RELATIONS
# ============================================================
print("== relations ==")

# work_orders M2Os
create_relation("easypc_work_orders", "customer", "easypc_customers",
                {"one_field": "work_orders", "one_deselect_action": "nullify"})
create_relation("easypc_work_orders", "store", "easypc_stores",
                {"one_field": "work_orders", "one_deselect_action": "nullify"})
create_relation("easypc_work_orders", "received_by", "directus_users")
create_relation("easypc_work_orders", "assessed_by", "directus_users")
create_relation("easypc_work_orders", "released_by", "directus_users")
create_relation("easypc_work_orders", "warranty_claim_of", "easypc_work_orders",
                {"one_field": "warranty_claims", "one_deselect_action": "nullify"})

# child -> work_orders (one_field creates the O2M alias on the parent)
create_relation("easypc_work_order_parts", "work_order", "easypc_work_orders",
                {"one_field": "parts", "sort_field": "sort", "one_deselect_action": "delete"})
create_relation("easypc_work_order_parts_used", "work_order", "easypc_work_orders",
                {"one_field": "parts_used", "sort_field": "sort", "one_deselect_action": "delete"})
create_relation("easypc_job_processes", "work_order", "easypc_work_orders",
                {"one_field": "processes", "sort_field": "sort", "one_deselect_action": "delete"})
create_relation("easypc_diagnostics", "work_order", "easypc_work_orders",
                {"one_field": "diagnostics", "sort_field": "sort", "one_deselect_action": "delete"})
create_relation("easypc_approvals", "work_order", "easypc_work_orders",
                {"one_field": "approvals", "one_deselect_action": "delete"})
create_relation("easypc_work_order_updates", "work_order", "easypc_work_orders",
                {"one_field": "updates", "one_deselect_action": "delete"})

# parts_used M2Os
create_relation("easypc_work_order_parts_used", "catalog_item", "easypc_parts_catalog")
create_relation("easypc_work_order_parts_used", "approval", "easypc_approvals")

# other staff M2Os
create_relation("easypc_job_processes", "done_by", "directus_users")
create_relation("easypc_diagnostics", "tested_by", "directus_users")
create_relation("easypc_approvals", "recorded_by", "directus_users")
create_relation("easypc_work_order_updates", "created_by", "directus_users")

# M2M junctions
create_relation("easypc_work_orders_services", "easypc_work_orders_id", "easypc_work_orders",
                {"one_field": "services", "junction_field": "easypc_services_id", "sort_field": "sort"})
create_relation("easypc_work_orders_services", "easypc_services_id", "easypc_services")

create_relation("easypc_work_orders_files", "easypc_work_orders_id", "easypc_work_orders",
                {"one_field": "files", "junction_field": "directus_files_id", "sort_field": "sort"})
create_relation("easypc_work_orders_files", "directus_files_id", "directus_files")


# ============================================================
# 6. PATCH ALIAS FIELDS (interfaces, tab groups)
# ============================================================
print("== alias field meta ==")

patch_field("easypc_work_orders", "services", {
    "special": ["m2m"], "interface": "list-m2m", "display": "related-values",
    "options": {"template": "{{easypc_services_id.name}} — ₱{{charged_price}}"},
    "group": "grp_unit", "width": "full", "sort": 5})

patch_field("easypc_work_orders", "files", {
    "special": ["m2m"], "interface": "files",
    "options": {"template": "{{directus_files_id.filename_download}}"},
    "group": "grp_parts", "width": "full", "sort": 4})

patch_field("easypc_work_orders", "parts", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{part_type}} — {{brand_model}} ({{condition}})", "enableCreate": True, "enableSelect": True},
    "display": "related-values", "display_options": {"template": "{{part_type}}"},
    "group": "grp_parts", "width": "full", "sort": 3})

patch_field("easypc_work_orders", "parts_used", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{description}} x{{qty}} — ₱{{unit_price}}"},
    "group": "grp_work", "width": "full", "sort": 2})

patch_field("easypc_work_orders", "processes", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{process_type}} — {{done_at}}"},
    "group": "grp_work", "width": "full", "sort": 1})

patch_field("easypc_work_orders", "diagnostics", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{area}} — {{result}}"},
    "group": "grp_assessment", "width": "full", "sort": 1})

patch_field("easypc_work_orders", "approvals", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{kind}} — {{decision}} ({{channel}})"},
    "group": "grp_assessment", "width": "full", "sort": 7})

patch_field("easypc_work_orders", "updates", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{update_type}} — {{message}}"},
    "group": "grp_updates", "width": "full", "sort": 1})

patch_field("easypc_work_orders", "warranty_claims", {
    "special": ["o2m"], "interface": "list-o2m",
    "options": {"template": "{{work_order_number}} — {{status}}"},
    "group": "grp_releasing", "width": "full", "sort": 11})

# child-side work_order M2O display
for child in ["easypc_work_order_parts", "easypc_work_order_parts_used", "easypc_job_processes",
              "easypc_diagnostics", "easypc_approvals", "easypc_work_order_updates"]:
    patch_field(child, "work_order", {
        "interface": "select-dropdown-m2o", "display": "related-values",
        "display_options": {"template": "{{work_order_number}}"}, "hidden": True})


# ============================================================
# 7. SEED DATA
# ============================================================
print("== seeds ==")

def seed(coll, rows, key="key"):
    st, res = api("GET", f"/items/{coll}?limit=-1&fields={key}")
    existing = {r[key] for r in res.get("data", [])} if st == 200 else set()
    for row in rows:
        if row[key] in existing:
            print(f"  = {coll}.{row[key]} exists")
            continue
        st2, res2 = api("POST", f"/items/{coll}", row)
        print(f"  + {coll}.{row[key]}" if st2 == 200 else f"  ! seed {row[key]} FAILED {st2}: {json.dumps(res2)[:200]}")

seed("easypc_services", [
    {"key": "diagnosis", "name": "Diagnosis", "sort": 1, "active": True},
    {"key": "recase", "name": "Recase", "sort": 2, "active": True},
    {"key": "upgrade", "name": "Upgrade", "sort": 3, "active": True},
    {"key": "cleaning", "name": "Cleaning", "sort": 4, "active": True},
    {"key": "pc_assembly", "name": "PC Assembly", "sort": 5, "active": True},
])

seed("easypc_stores", [
    {"code": "MAIN", "name": "Main Store (placeholder)", "sort": 1, "active": True},
], key="code")


# ============================================================
# 8. ROLES + PERMISSIONS
# ============================================================
print("== roles ==")

EASYPC_COLLS = [
    "easypc_stores", "easypc_services", "easypc_parts_catalog", "easypc_customers",
    "easypc_work_orders", "easypc_work_order_parts", "easypc_work_order_parts_used",
    "easypc_job_processes", "easypc_diagnostics", "easypc_approvals",
    "easypc_work_order_updates", "easypc_work_orders_files", "easypc_work_orders_services",
]

CRUD = ["create", "read", "update", "delete"]

ROLE_PERMS = {
    "easypc_front_desk": {
        "desc": "Front desk / RA-TECH — intake, customers, parts checklist, releasing",
        "crud": ["easypc_customers", "easypc_work_orders", "easypc_work_order_parts",
                 "easypc_work_order_parts_used", "easypc_approvals", "easypc_work_order_updates",
                 "easypc_work_orders_files", "easypc_work_orders_services"],
        "read": ["easypc_stores", "easypc_services", "easypc_parts_catalog",
                 "easypc_job_processes", "easypc_diagnostics"],
    },
    "easypc_technician": {
        "desc": "Technician — diagnostics, processes, findings, approvals, updates",
        "crud": ["easypc_job_processes", "easypc_diagnostics", "easypc_approvals",
                 "easypc_work_order_updates", "easypc_work_order_parts_used",
                 "easypc_work_orders_files", "easypc_work_orders_services"],
        "read": ["easypc_stores", "easypc_services", "easypc_parts_catalog",
                 "easypc_customers", "easypc_work_order_parts"],
    },
    "easypc_manager": {
        "desc": "Manager — full access incl. status overrides",
        "crud": EASYPC_COLLS,
        "read": [],
    },
}

# technician also updates work_orders
ROLE_PERMS["easypc_technician"]["crud"] = [c for c in ROLE_PERMS["easypc_technician"]["crud"]]


def role_id(name):
    st, res = api("GET", f"/roles?filter[name][_eq]={name}")
    data = res.get("data", [])
    return data[0]["id"] if st == 200 and data else None


def create_role(name, desc):
    rid = role_id(name)
    if rid:
        print(f"  = role {name} exists")
        return rid
    st, res = api("POST", "/roles", {"name": name, "icon": "supervised_user_circle", "description": desc})
    if st == 200:
        rid = res["data"]["id"]
        print(f"  + role {name}")
        return rid
    print(f"  ! role {name} FAILED {st}: {json.dumps(res)[:300]}")
    return None


def create_policy(name, desc):
    st, res = api("GET", f"/policies?filter[name][_eq]={name}")
    data = res.get("data", [])
    if st == 200 and data:
        print(f"  = policy {name} exists")
        return data[0]["id"]
    st, res = api("POST", "/policies",
                  {"name": name, "icon": "policy", "description": desc,
                   "admin_access": False, "app_access": True})
    if st == 200:
        print(f"  + policy {name}")
        return res["data"]["id"]
    print(f"  ! policy {name} FAILED {st}: {json.dumps(res)[:300]}")
    return None


def grant(policy_id, collection, action, fields=None):
    body = {"collection": collection, "action": action, "policy": policy_id,
            "fields": fields or ["*"], "permissions": {}, "validation": {}, "presets": {}}
    st, res = api("POST", "/permissions", body)
    if st != 200:
        print(f"  ! perm {collection}.{action} FAILED {st}: {json.dumps(res)[:200]}")


def link_access(role, policy):
    st, res = api("GET", f"/access?filter[role][_eq]={role}&filter[policy][_eq]={policy}")
    if st == 200 and res.get("data"):
        return
    api("POST", "/access", {"role": role, "policy": policy, "user": None})


for role_name, cfg in ROLE_PERMS.items():
    rid = create_role(role_name, cfg["desc"])
    pid = create_policy(f"{role_name}_policy", cfg["desc"])
    if not (rid and pid):
        continue
    link_access(rid, pid)
    for c in cfg["crud"]:
        for a in CRUD:
            grant(pid, c, a)
    for c in cfg["read"]:
        grant(pid, c, "read")
    # technician can update (not create/delete) work_orders
    if role_name == "easypc_technician":
        grant(pid, "easypc_work_orders", "read")
        grant(pid, "easypc_work_orders", "update")
    # system needs: read users (M2O display), files upload/read
    grant(pid, "directus_users", "read")
    grant(pid, "directus_files", "read")
    grant(pid, "directus_files", "create")
    grant(pid, "directus_files", "update")
    grant(pid, "directus_folders", "read")
    print(f"  + permissions granted for {role_name}")

print("\nDone.")
