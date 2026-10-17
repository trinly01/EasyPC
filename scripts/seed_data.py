import json, os, urllib.request, urllib.error, urllib.parse, time

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

def items(coll):
    st, res = api('GET', f'/items/{coll}?limit=-1')
    return res.get('data', [])

def find(coll, field, val):
    q = urllib.parse.quote(str(val), safe='')
    st, res = api('GET', f'/items/{coll}?filter%5B{field}%5D%5B_eq%5D={q}&limit=1')
    return (res.get('data') or [None])[0]

def upsert(coll, match_field, match_val, payload):
    row = find(coll, match_field, match_val)
    if row:
        st, res = api('PATCH', f"/items/{coll}/{row['id']}", payload)
        return row['id'], 'updated'
    st, res = api('POST', f'/items/{coll}', payload)
    return (res.get('data') or {}).get('id'), 'created'

# ---------- stores ----------
main = find('easypc_stores', 'code', 'MAIN')
if main:
    api('PATCH', f"/items/easypc_stores/{main['id']}", {'name': 'EasyPC Gilmore (HQ)', 'code': 'GIL'})
stores = {}
for name, code in [('EasyPC Gilmore (HQ)', 'GIL'), ('EasyPC SM North EDSA', 'SMNE'), ('EasyPC Cebu IT Park', 'CEB')]:
    sid, act = upsert('easypc_stores', 'code', code, {'name': name, 'code': code, 'active': True})
    stores[code] = sid
    print('store', code, act)

# ---------- services (price the existing 5, add more) ----------
services = [
    ('diagnosis', 'Diagnosis', 300),
    ('recase', 'Recase', 800),
    ('upgrade', 'Upgrade', 500),
    ('cleaning', 'Cleaning', 450),
    ('pc_assembly', 'PC Assembly', 1500),
    ('os_install', 'OS Installation', 800),
    ('data_recovery', 'Data Recovery', 1500),
    ('virus_removal', 'Virus / Malware Removal', 600),
    ('screen_replacement', 'Screen Replacement (Labor)', 1200),
    ('thermal_repaste', 'Thermal Repaste', 650),
]
svc_ids = {}
for key, name, price in services:
    sid, act = upsert('easypc_services', 'key', key, {'key': key, 'name': name, 'price': price, 'active': True})
    svc_ids[key] = sid
print('services seeded:', len(svc_ids))

# ---------- parts catalog ----------
parts_cat = [
    ('KF432C16BB-8', 'Kingston Fury Beast 8GB DDR4-3200', 'ram', 'Kingston', 'DDR4 8GB 3200MHz', 1450, 180),
    ('KF432C16BB-16', 'Kingston Fury Beast 16GB DDR4-3200', 'ram', 'Kingston', 'DDR4 16GB 3200MHz', 2750, 180),
    ('MZ-V8V500BW', 'Samsung 980 500GB NVMe SSD', 'storage', 'Samsung', 'NVMe Gen3 500GB', 3200, 365),
    ('SNV2S-1000G', 'Kingston NV2 1TB NVMe SSD', 'storage', 'Kingston', 'NVMe Gen4 1TB', 4100, 365),
    ('ST1000DM010', 'Seagate Barracuda 1TB HDD', 'storage', 'Seagate', '3.5" 7200RPM', 2650, 365),
    ('CP-9020210', 'Corsair CV550 550W PSU', 'psu', 'Corsair', '550W 80+ Bronze', 2850, 365),
    ('HV-PRO-650', 'FSP HV Pro 650W PSU', 'psu', 'FSP', '650W 80+ Bronze', 2300, 365),
    ('NE5165001BG1', 'Palit GTX 1650 StormX 4GB', 'gpu', 'Palit', 'GDDR6 4GB', 8950, 365),
    ('TW-FORGE-M', 'Tecware Forge M Case', 'case_other', 'Tecware', 'mATX tempered glass', 1650, 0),
    ('MX-4-4G', 'Arctic MX-4 Thermal Paste', 'cpu_cooler', 'Arctic', '4g tube', 350, 0),
    ('SCR-156-FHD', 'Laptop Screen 15.6" FHD IPS', 'case_other', 'Generic', '1920x1080 30-pin', 3800, 90),
    ('BAT-HP-HT03XL', 'Laptop Battery HT03XL', 'case_other', 'OEM-compat', 'HP 15/250 G7 series', 2200, 90),
    ('FAN-120-PWM', '120mm PWM Case Fan', 'cpu_cooler', 'Generic', '120mm 4-pin', 350, 90),
]
cat_ids = {}
for sku, name, ptype, brand, spec, price, wdays in parts_cat:
    pid, act = upsert('easypc_parts_catalog', 'sku', sku,
        {'sku': sku, 'name': name, 'part_type': ptype, 'brand': brand, 'spec': spec,
         'price': price, 'warranty_days': wdays, 'active': True})
    cat_ids[sku] = pid
print('catalog seeded:', len(cat_ids))

# ---------- customers ----------
customers = [
    ('Juan Dela Cruz', '09171234567', 'juan.delacruz@gmail.com'),
    ('Maria Santos', '09182223344', 'maria.santos@yahoo.com'),
    ('Mark Villanueva', '09205556677', 'mark.v@outlook.com'),
    ('Ana Reyes', '09198887766', None),
    ('Grace Lim', '09171112233', 'grace.lim@gmail.com'),
]
cust_ids = {}
for name, contact, email in customers:
    cid, act = upsert('easypc_customers', 'name', name,
        {'name': name, 'contact_no': contact, 'email': email})
    cust_ids[name] = cid
print('customers seeded:', len(cust_ids))

def wo_svc(wo_id, svc_key, price):
    api('POST', '/items/easypc_work_orders_services',
        {'easypc_work_orders_id': wo_id, 'easypc_services_id': svc_ids[svc_key], 'charged_price': price})

# ---------- WO 1: awaiting_approval (new desktop intake) ----------
if not find('easypc_work_orders', 'customer_concern', 'PC very slow, takes 10 minutes to boot'):
    st, res = api('POST', '/items/easypc_work_orders', {
        'status': 'awaiting_approval', 'store': stores['GIL'],
        'odoo_ticket': 'S00142', 'customer': cust_ids['Juan Dela Cruz'],
        'unit_type': 'desktop', 'unit_brand_model': 'Custom build — Ryzen 5 3600 / MSI B450M',
        'password_handling': 'not_needed',
        'customer_concern': 'PC very slow, takes 10 minutes to boot',
        'terms_accepted': True, 'terms_version': 'v2024.1',
        'diagnosis_findings': 'HDD has bad sectors (CrystalDiskInfo: caution). RAM at 8GB only.',
        'recommended_solution': 'Upgrade to 1TB NVMe SSD + add 8GB RAM. Clone OS to new drive.'})
    wo1 = res['data']['id']
    wo_svc(wo1, 'diagnosis', 300)
    wo_svc(wo1, 'upgrade', 500)
    api('POST', '/items/easypc_work_order_parts', {'work_order': wo1, 'part_type': 'cpu', 'provided': True, 'brand_model': 'Ryzen 5 3600', 'condition': 'good'})
    api('POST', '/items/easypc_work_order_parts', {'work_order': wo1, 'part_type': 'storage', 'provided': True, 'brand_model': 'WD Blue 1TB HDD', 'serial_no': 'WD-WMAL9M2', 'condition': 'with_damage', 'damage_notes': 'bad sectors detected'})
    api('POST', '/items/easypc_approvals', {'work_order': wo1, 'kind': 'assessment', 'decision': 'pending', 'channel': 'call', 'notes': 'Called customer — waiting for go signal on parts'})
    print('wo1 created (awaiting_approval)')

# ---------- WO 2: in_repair (laptop cleaning + repaste) ----------
if not find('easypc_work_orders', 'customer_concern', 'Laptop overheating and shutting down'):
    st, res = api('POST', '/items/easypc_work_orders', {
        'status': 'in_repair', 'store': stores['SMNE'],
        'customer': cust_ids['Maria Santos'],
        'unit_type': 'laptop', 'unit_brand_model': 'HP Pavilion 15-cs3000',
        'password_handling': 'customer_to_enter',
        'customer_concern': 'Laptop overheating and shutting down',
        'terms_accepted': True, 'terms_version': 'v2024.1',
        'diagnosis_findings': 'Fans clogged with dust, thermal paste dried out. Temps hitting 95C.',
        'recommended_solution': 'Full cleaning + thermal repaste',
        })
    wo2 = res['data']['id']
    wo_svc(wo2, 'cleaning', 450)
    wo_svc(wo2, 'thermal_repaste', 650)
    api('POST', '/items/easypc_job_processes', {'work_order': wo2, 'process_type': 'cleaning', 'coverage': 'full'})
    api('POST', '/items/easypc_diagnostics', {'work_order': wo2, 'area': 'cooling_fans',
        'tests': ['fan_speed', 'thermal_stress'], 'issues': 'Fan 1 rattling; temps 95C under load',
        'result': 'fail'})
    print('wo2 created (in_repair)')

# ---------- WO 3: testing (desktop upgrade, parts used) ----------
if not find('easypc_work_orders', 'customer_concern', 'Want faster PC for photo editing'):
    st, res = api('POST', '/items/easypc_work_orders', {
        'status': 'testing', 'store': stores['GIL'],
        'customer': cust_ids['Mark Villanueva'],
        'unit_type': 'desktop', 'unit_brand_model': 'Custom build — i5-9400F / ASUS H310M',
        'password_handling': 'customer_to_enter',
        'customer_concern': 'Want faster PC for photo editing',
        'terms_accepted': True, 'terms_version': 'v2024.1',
        'diagnosis_findings': 'System healthy; bottleneck is HDD + 8GB RAM.',
        'recommended_solution': 'Install NVMe SSD, upgrade to 24GB RAM',
        'test_result': 'passed', })
    wo3 = res['data']['id']
    wo_svc(wo3, 'upgrade', 500)
    api('POST', '/items/easypc_work_order_parts_used', {
        'work_order': wo3, 'catalog_item': cat_ids['SNV2S-1000G'], 'price_source': 'catalog',
        'part_type': 'storage', 'description': 'Kingston NV2 1TB NVMe SSD',
        'qty': 1, 'unit_price': 4100, 'source': 'easypc',
        'warranty_provider': 'easypc', 'warranty_days': 365})
    api('POST', '/items/easypc_work_order_parts_used', {
        'work_order': wo3, 'catalog_item': cat_ids['KF432C16BB-16'], 'price_source': 'catalog',
        'part_type': 'ram', 'description': 'Kingston Fury Beast 16GB DDR4-3200',
        'qty': 1, 'unit_price': 2750, 'source': 'easypc',
        'warranty_provider': 'easypc', 'warranty_days': 180})
    api('POST', '/items/easypc_diagnostics', {'work_order': wo3, 'area': 'storage',
        'tests': ['smart_check', 'read_write'], 'result': 'pass'})
    api('POST', '/items/easypc_diagnostics', {'work_order': wo3, 'area': 'ram',
        'tests': ['memtest'], 'result': 'pass'})
    print('wo3 created (testing)')

# ---------- WO 4: released (complete journey — flows stamp released_at/warranty) ----------
if not find('easypc_work_orders', 'customer_concern', 'No display on boot'):
    st, res = api('POST', '/items/easypc_work_orders', {
        'status': 'registered', 'store': stores['CEB'],
        'customer': cust_ids['Ana Reyes'],
        'unit_type': 'desktop', 'unit_brand_model': 'Acer Aspire TC-875',
        'password_handling': 'not_needed',
        'customer_concern': 'No display on boot',
        'terms_accepted': True, 'terms_version': 'v2024.1',
        'diagnosis_findings': 'PSU dead — no standby voltage. Replaced with CV550.',
        'recommended_solution': 'PSU replacement',
        'test_result': 'passed', })
    wo4 = res['data']['id']
    wo_svc(wo4, 'diagnosis', 300)
    api('POST', '/items/easypc_work_order_parts_used', {
        'work_order': wo4, 'catalog_item': cat_ids['CP-9020210'], 'price_source': 'catalog',
        'part_type': 'psu', 'description': 'Corsair CV550 550W PSU',
        'qty': 1, 'unit_price': 2850, 'source': 'easypc',
        'warranty_provider': 'easypc', 'warranty_days': 365})
    api('POST', '/items/easypc_diagnostics', {'work_order': wo4, 'area': 'psu',
        'tests': ['voltage_rails'], 'result': 'pass'})
    # walk the journey so flows fire
    for s in ('awaiting_approval', 'in_repair', 'testing', 'ready_for_release'):
        api('PATCH', f'/items/easypc_work_orders/{wo4}', {'status': s})
    api('PATCH', f'/items/easypc_work_orders/{wo4}',
        {'so_number': 'SO-2026-0917', 'amount': 3150, 'old_parts_disposition': 'returned',
         'receiver_name': 'Ana Reyes', 'receiver_id': 'UMID-0111-2222333'})
    api('PATCH', f'/items/easypc_work_orders/{wo4}', {'status': 'released'})
    print('wo4 created + released')
    time.sleep(2)
    st, res = api('GET', f'/items/easypc_work_orders/{wo4}?fields=work_order_number,status,released_at,service_warranty_until')
    print('wo4 final:', json.dumps(res.get('data')))

print('done')
