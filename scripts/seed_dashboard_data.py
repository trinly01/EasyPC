"""Seed realistic demo data for the EasyPC Insights dashboard.

Creates ~66 work orders spread May-Oct 2026 (weighted statuses, service
junctions, parts used, released fields), ~25 extra customers and ~14
upcoming appointments. Idempotent: each WO carries a deterministic
`job_order_no` (JO-26-NNNN) which is existence-checked before create.

Run:  DIRECTUS_TOKEN=<admin> python scripts/seed_dashboard_data.py
"""
import json, os, random, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timedelta

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")
random.seed(42)

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

def items(coll, fields='id'):
    st, res = api('GET', f'/items/{coll}?limit=-1&fields={fields}')
    return res.get('data', [])

def find(coll, field, val):
    q = urllib.parse.quote(str(val), safe='')
    st, res = api('GET', f'/items/{coll}?filter%5B{field}%5D%5B_eq%5D={q}&limit=1')
    return (res.get('data') or [None])[0]

# ---------- lookups ----------
stores = [s['id'] for s in items('easypc_stores', 'id,code')]
services = {s['key']: s for s in items('easypc_services', 'id,key,price')}
catalog = items('easypc_parts_catalog', 'id,part_type,name,price,warranty_days')
assert stores and services, 'run scripts/seed_data.py first'

# ---------- extra customers (seed_data.py already made 8) ----------
EXTRA_CUSTOMERS = [
    ('Jose Ramos', '09175550101', 'jose.ramos@gmail.com'),
    ('Kristine Bautista', '09286650202', 'kris.bautista@yahoo.com'),
    ('Paolo Mendoza', '09177750303', None),
    ('Liza Fernandez', '09398850404', 'liza.f@gmail.com'),
    ('Ramon Gutierrez', '09179950505', 'rgutierrez@outlook.com'),
    ('Jenny Castillo', '09271150606', None),
    ('Albert Aquino', '09182250707', 'albert.aquino@gmail.com'),
    ('Rhea Dominguez', '09393350808', 'rhea.d@gmail.com'),
    ('Enrico Salazar', '09184450909', None),
    ('Mylene Torres', '09205551010', 'mylene.torres@yahoo.com'),
    ('Danilo Flores', '09176651111', None),
    ('Cherry Navarro', '09287751212', 'cherry.nav@gmail.com'),
    ('Gilbert Ocampo', '09188851313', None),
    ('Sofia Del Rosario', '09399951414', 'sofia.dr@gmail.com'),
    ('Nelson Cruz', '09170051515', 'nelson.cruz@outlook.com'),
    ('Angelica Pascual', '09281151616', None),
    ('Renato Mercado', '09192251717', 'rmercado@gmail.com'),
    ('Divina Santos', '09303351818', None),
    ('Carlos Velasco', '09174451919', 'cvelasco@yahoo.com'),
    ('Imelda Garcia', '09285552020', None),
    ('Francis Lim', '09196652121', 'francis.lim@gmail.com'),
    ('Rowena Diaz', '09307752222', None),
    ('Victor Santiago', '09178852323', 'v.santiago@outlook.com'),
    ('Camille Ortega', '09289952424', 'camille.o@gmail.com'),
    ('Benedict Yu', '09190052525', None),
]
cust_ids = [c['id'] for c in items('easypc_customers', 'id')]
existing_names = {c.get('name') for c in items('easypc_customers', 'id,name')}
for name, phone, email in EXTRA_CUSTOMERS:
    if name in existing_names:
        continue
    st, res = api('POST', '/items/easypc_customers',
        {'name': name, 'contact_no': phone, 'email': email})
    cid = (res.get('data') or {}).get('id')
    if cid:
        cust_ids.append(cid)
print('customers total:', len(cust_ids))

# ---------- work order generation ----------
LAPTOPS = [
    ('HP Pavilion 15-eh1000', 'Laptop overheating and shutting down'),
    ('Lenovo IdeaPad 3 15ITL6', 'Screen flickering then goes black'),
    ('Acer Aspire 5 A515', 'Very slow, apps take forever to open'),
    ('ASUS VivoBook 14 X415', 'Battery drains fast, wont hold charge'),
    ('Dell Inspiron 14 5420', 'No display but power light is on'),
    ('MacBook Air A2337', 'Liquid spill, keyboard not responding'),
    ('Lenovo Legion 5', 'Fans very loud, thermal throttling in games'),
    ('HP 14s-dq5000', 'BSOD on boot, restarts in a loop'),
]
DESKTOPS = [
    ('Custom build - Ryzen 5 5600 / B550M', 'PC very slow, takes 10 minutes to boot'),
    ('Custom build - i5-12400F / H610M', 'No display on boot, fans spin'),
    ('Custom build - Ryzen 7 5800X / B450', 'Random shutdowns while gaming'),
    ('Acer Aspire TC-1760', 'Wont power on at all'),
    ('HP Pavilion TP01', 'HDD clicking noise, files corrupted'),
    ('Custom build - i7-11700K / Z590', 'Want faster PC for video editing'),
    ('Custom build - Ryzen 5 3600 / A520M', 'Upgrade request: SSD + RAM'),
    ('Dell OptiPlex 7090 SFF', 'Windows wont boot after power outage'),
]
LOOSE = [
    ('Loose parts - GTX 1660 Super', 'GPU artifacts, customer wants testing'),
    ('Loose parts - PC build (boxed)', 'Full PC assembly from customer parts'),
    ('Loose parts - Ryzen 7 5700X kit', 'CPU+mobo+RAM upgrade install'),
]
DIAG_NOTES = {
    'overheat': 'Fans clogged with dust, thermal paste dried out. Temps hitting 95C under load.',
    'storage': 'HDD has bad sectors (SMART: caution). Recommend SSD replacement/upgrade.',
    'power': 'PSU dead - no standby voltage on rails. Needs replacement.',
    'gpu': 'Artifacts under load, VRAM errors in memtest_vulkan. Fans seized.',
    'board': 'POST fail, debug LED stuck on DRAM. RAM reseat no help.',
    'os': 'Corrupted Windows installation, boot files damaged. Recommend clean OS install + backup.',
    'battery': 'Battery health 42%, swollen pack. Screen hinges also loose.',
    'generic': 'Unit tested; fault isolated during diagnostics. See diagnostic rows for details.',
}
SOLUTIONS = {
    'overheat': 'Full cleaning + thermal repaste, replace worn fan',
    'storage': 'Upgrade to NVMe SSD, clone/recover data',
    'power': 'PSU replacement, verify rails under load',
    'gpu': 'Fan replacement + repaste; if artifacts persist, declare for replacement',
    'board': 'RMA/board-level repair; quote before proceeding',
    'os': 'Backup user data, clean OS install + drivers',
    'battery': 'Battery replacement (HT03XL), hinge check',
    'generic': 'Proceed per approved scope',
}

def pick_concern(unit_type):
    if unit_type == 'laptop':
        bm, concern = random.choice(LAPTOPS)
        key = 'overheat' if 'overheat' in concern or 'loud' in concern else \
              'battery' if 'Battery' in concern or 'charge' in concern else \
              'board' if 'display' in concern or 'spill' in concern else \
              'os' if 'BSOD' in concern else 'storage'
    elif unit_type == 'desktop':
        bm, concern = random.choice(DESKTOPS)
        key = 'power' if 'power' in concern.lower() or 'Wont power' in concern else \
              'storage' if 'slow' in concern or 'HDD' in concern or 'SSD' in concern else \
              'gpu' if 'display' in concern else 'generic'
    else:
        bm, concern = random.choice(LOOSE)
        key = 'generic'
    return bm, concern, key

def status_for_age(age_days):
    r = random.random()
    if age_days > 45:
        return 'released' if r < 0.90 else ('cancelled' if r < 0.95 else 'unclaimed')
    if age_days > 20:
        return ('released' if r < 0.80 else 'ready_for_release' if r < 0.88 else
                'in_repair' if r < 0.94 else 'testing' if r < 0.97 else 'cancelled')
    return ('released' if r < 0.35 else 'ready_for_release' if r < 0.45 else
            'in_repair' if r < 0.60 else 'testing' if r < 0.70 else
            'awaiting_approval' if r < 0.82 else 'assessing' if r < 0.90 else
            'awaiting_assessment' if r < 0.96 else 'registered')

# month -> count (Oct is partial month, still busiest)
PLAN = [(5, 6), (6, 8), (7, 10), (8, 11), (9, 13), (10, 18)]
TODAY = datetime(2026, 10, 21)
svc_keys = list(services.keys())
svc_weights = {'diagnosis': 0.30, 'cleaning': 0.16, 'thermal_repaste': 0.12, 'upgrade': 0.10,
               'os_install': 0.10, 'virus_removal': 0.08, 'data_recovery': 0.06,
               'screen_replacement': 0.04, 'pc_assembly': 0.03, 'recase': 0.01}
CHANNELS = ['messenger', 'sms', 'call', 'in_person']
JO_COUNTER_START = 101

def weighted_services(n):
    keys = [k for k in svc_keys]
    w = [svc_weights.get(k, 0.05) for k in keys]
    picked = set()
    while len(picked) < n:
        picked.add(random.choices(keys, weights=w)[0])
    return list(picked)

created = skipped = 0
jo_no = JO_COUNTER_START
for month, count in PLAN:
    for _ in range(count):
        jo = f'JO-26-{jo_no:04d}'
        jo_no += 1
        if find('easypc_work_orders', 'job_order_no', jo):
            skipped += 1
            continue

        # intake datetime inside the month, capped at today
        day = random.randint(1, 28 if month != 10 else 21)
        intake = datetime(2026, month, min(day, 28), random.randint(9, 18), random.choice([0, 15, 30, 45]))
        if intake > TODAY:
            intake = TODAY - timedelta(hours=random.randint(1, 48))
        age = (TODAY - intake).days
        status = status_for_age(age)

        unit_type = random.choices(['laptop', 'desktop', 'loose_parts'], weights=[55, 35, 10])[0]
        bm, concern, dkey = pick_concern(unit_type)
        store = random.choices(stores, weights=[50, 30, 20])[0]
        customer = random.choice(cust_ids)
        n_svc = random.choices([1, 2, 3], weights=[55, 35, 10])[0]
        chosen = weighted_services(n_svc)

        done = status in ('released', 'unclaimed', 'ready_for_release', 'testing', 'in_repair',
                          'approved', 'awaiting_approval', 'assessing')
        released = status == 'released'
        release_dt = intake + timedelta(days=random.randint(1, 8), hours=random.randint(0, 6)) if released or status == 'unclaimed' else None
        if release_dt and release_dt > TODAY:
            release_dt = TODAY - timedelta(hours=random.randint(1, 24))
        parts_rows = []
        if released and random.random() < 0.62:
            for _ in range(random.randint(1, 3)):
                p = random.choice(catalog)
                parts_rows.append({
                    'catalog_item': p['id'], 'price_source': 'catalog',
                    'part_type': p['part_type'], 'description': p['name'],
                    'qty': 1, 'unit_price': float(p['price']), 'source': 'easypc',
                    'warranty_provider': 'easypc', 'warranty_days': p['warranty_days']})
        svc_total = sum(float(services[k]['price']) for k in chosen)
        parts_total = sum(r['qty'] * r['unit_price'] for r in parts_rows)

        wo = {
            'job_order_no': jo,
            'status': status,
            'store': store,
            'customer': customer,
            'date_time_in': intake.strftime('%Y-%m-%dT%H:%M:%S'),
            'intake_path': random.choice(['wait_for_assessment', 'leave_device']),
            'unit_type': unit_type,
            'unit_brand_model': bm,
            'password_handling': random.choice(['not_needed', 'customer_to_enter']),
            'customer_concern': concern,
            'terms_accepted': True,
            'terms_version': 'v2024.1',
        }
        if done:
            wo['diagnosis_findings'] = DIAG_NOTES[dkey]
            wo['recommended_solution'] = SOLUTIONS[dkey]
            wo['assessed_at'] = (intake + timedelta(hours=random.randint(2, 24))).strftime('%Y-%m-%dT%H:%M:%S')
        if released or status == 'unclaimed':
            wo['test_result'] = 'passed'
            wo['test_remarks'] = 'Boot test OK, stress test stable'
        if released:
            wo.update({
                'released_at': release_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'amount': round(svc_total + parts_total, 2),
                'so_number': f'SO-2026-{random.randint(8000, 9999)}',
                'receiver_name': 'Customer',
                'receiver_id': random.choice(['UMID', 'Drivers License', 'PhilID', 'Passport']) + f'-{random.randint(1000,9999)}-{random.randint(1000,9999)}',
                'old_parts_disposition': random.choice(['returned', 'none', 'dispose']),
                'service_warranty_until': (release_dt + timedelta(days=30)).strftime('%Y-%m-%d'),
            })

        st, res = api('POST', '/items/easypc_work_orders', wo)
        wo_id = (res.get('data') or {}).get('id')
        if not wo_id:
            print('WO create failed', st, res)
            continue
        created += 1

        for k in chosen:
            price = round(float(services[k]['price']) * random.uniform(0.9, 1.1))
            api('POST', '/items/easypc_work_orders_services',
                {'easypc_work_orders_id': wo_id, 'easypc_services_id': services[k]['id'], 'charged_price': price})
        for pr in parts_rows:
            pr['work_order'] = wo_id
            if release_dt:
                pr['warranty_until'] = (release_dt + timedelta(days=pr['warranty_days'])).strftime('%Y-%m-%d')
            api('POST', '/items/easypc_work_order_parts_used', pr)
        if status in ('awaiting_approval',):
            api('POST', '/items/easypc_approvals', {'work_order': wo_id, 'kind': 'assessment',
                'decision': 'pending', 'channel': random.choice(CHANNELS),
                'notes': 'Estimate sent - waiting for customer go signal'})
        elif done and status not in ('assessing',):
            api('POST', '/items/easypc_approvals', {'work_order': wo_id, 'kind': 'assessment',
                'decision': 'approved', 'channel': random.choice(CHANNELS),
                'informed_at': wo['assessed_at'],
                'decided_at': (intake + timedelta(hours=random.randint(25, 60))).strftime('%Y-%m-%dT%H:%M:%S'),
                'notes': 'Customer approved recommended scope'})
        if status in ('in_repair', 'testing', 'ready_for_release', 'released', 'unclaimed'):
            api('POST', '/items/easypc_job_processes', {'work_order': wo_id,
                'process_type': random.choice(['cleaning', 'install_upgrade', 'troubleshooting']),
                'coverage': json.dumps([random.choice(['dust_fans', 'heatsink', 'os_drivers', 'ram', 'storage', 'power_post', 'boot_os'])]),
                'done_at': (intake + timedelta(days=random.randint(0, 3))).strftime('%Y-%m-%dT%H:%M:%S')})
        if done and random.random() < 0.7:
            api('POST', '/items/easypc_diagnostics', {'work_order': wo_id,
                'area': random.choice(['cpu', 'storage', 'ram', 'psu', 'gpu', 'cooling_fans', 'os_software']),
                'tests': json.dumps([random.choice(['stress_test', 'smart_health', 'memory_test', 'post_bios', 'load_test'])]),
                'result': random.choice(['pass', 'pass', 'observation', 'fail']),
                'tested_at': wo.get('assessed_at')})

print(f'work orders: {created} created, {skipped} skipped (existing)')

# ---------- upcoming appointments ----------
svc_list = list(services.values())
existing_appts = len(items('easypc_appointments', 'id'))
TIMES = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
APPT_UNITS = ['laptop', 'desktop', 'loose_parts']
appt_made = 0
if existing_appts < 20:
    for i in range(14):
        d = TODAY.date() + timedelta(days=i // 2)
        _, concern, _ = pick_concern(random.choice(APPT_UNITS))
        st, res = api('POST', '/items/easypc_appointments', {
            'status': 'confirmed' if random.random() < 0.85 else 'cancelled',
            'store': random.choices(stores, weights=[50, 30, 20])[0],
            'customer': random.choice(cust_ids),
            'service': random.choice(svc_list)['id'],
            'preferred_date': d.strftime('%Y-%m-%d'),
            'preferred_time': random.choice(TIMES),
            'unit_type': random.choice(APPT_UNITS),
            'concern': concern,
            'notes': random.choice(['Returning customer', 'Referred by friend', '', '', '']),
        })
        if res.get('data'):
            appt_made += 1
print('appointments created:', appt_made)
print('done')
