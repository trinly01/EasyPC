"""Build the EasyPC Insights dashboard.

Mirrors the BIS Dashboard pattern on this instance:
  - metric panels use native collection/aggregate options
  - echarts-panel panels point at a webhook flow that runs `likha_sql`
    (key sql_1) then an `exec` op (key chart) returning an echarts option
    object as the flow result

Creates 6 easypc_chart_* flows + 'EasyPC Dashboard' with 6 metrics and
6 echarts panels. Idempotent by name.

Run:  DIRECTUS_TOKEN=<admin> python scripts/build_dashboard.py
"""
import json, os, urllib.request, urllib.error, urllib.parse

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")
BRAND = '#00c853'

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

def find_by(coll, field, val):
    q = urllib.parse.quote(str(val), safe='')
    st, res = api('GET', f'/{coll}?filter%5B{field}%5D%5B_eq%5D={q}&limit=1')
    return (res.get('data') or [None])[0]

JS_PREAMBLE = """module.exports = async function(data) {
  var rows = data.sql_1 || data.$last || [];
  if (rows && rows.rows) rows = rows.rows;
"""

BAR_STYLE = "type: 'bar', itemStyle: { color: '%s', borderRadius: [4,4,0,0] }, label: { show: true, position: 'top' }" % BRAND
HBAR_STYLE = "type: 'bar', itemStyle: { color: '%s', borderRadius: [0,4,4,0] }, label: { show: true, position: 'right' }" % BRAND
LINE_STYLE = "type: 'line', smooth: true, areaStyle: { opacity: 0.15 }, itemStyle: { color: '%s' }" % BRAND
PIE_STYLE = "type: 'pie', radius: ['40%','68%'], center: ['50%','55%'], itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 }, label: { formatter: '{b}: {c}' }"

STATUS_LABELS = """  var labels = { registered: 'Registered', awaiting_assessment: 'Awaiting Assessment',
    assessing: 'Assessing', awaiting_approval: 'Awaiting Approval', approved: 'Approved',
    declined: 'Declined', in_repair: 'In Repair', testing: 'Testing',
    ready_for_release: 'Ready for Pickup', released: 'Released',
    cancelled: 'Cancelled', unclaimed: 'Unclaimed' };
"""
PART_LABELS = """  var labels = { cpu: 'CPU', motherboard: 'Motherboard', ram: 'RAM', gpu: 'GPU',
    storage: 'Storage', psu: 'PSU', cpu_cooler: 'Cooling', case_other: 'Case/Other' };
"""

CHARTS = [
    {
        'name': 'easypc_chart_intake_trend',
        'sql': "SELECT to_char(date_trunc('month', date_time_in), 'YYYY-MM') AS m, COUNT(*) AS cnt FROM easypc_work_orders GROUP BY 1 ORDER BY 1",
        'code': JS_PREAMBLE + """  return {
    title: { text: "Monthly Work Order Intake", left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, top: 40, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: rows.map(function(r){ return r.m; }), boundaryGap: false },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ """ + LINE_STYLE + """, data: rows.map(function(r){ return Number(r.cnt); }) }]
  };
}""",
    },
    {
        'name': 'easypc_chart_revenue',
        'sql': "SELECT to_char(date_trunc('month', released_at), 'YYYY-MM') AS m, ROUND(SUM(amount)) AS total FROM easypc_work_orders WHERE status = 'released' AND released_at IS NOT NULL GROUP BY 1 ORDER BY 1",
        'code': JS_PREAMBLE + """  return {
    title: { text: "Monthly Revenue, PHP (Released)", left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, top: 40, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: rows.map(function(r){ return r.m; }) },
    yAxis: { type: 'value' },
    series: [{ """ + BAR_STYLE + """,
      data: rows.map(function(r){ return Number(r.total); }) }]
  };
}""",
    },
    {
        'name': 'easypc_chart_status',
        'sql': "SELECT status AS name, COUNT(*) AS cnt FROM easypc_work_orders GROUP BY 1 ORDER BY cnt DESC",
        'code': JS_PREAMBLE + STATUS_LABELS + """  return {
    title: { text: "Work Orders by Status", left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{ """ + PIE_STYLE + """,
      data: rows.map(function(r){ return { name: labels[r.name] || r.name, value: Number(r.cnt) }; }) }]
  };
}""",
    },
    {
        'name': 'easypc_chart_top_services',
        'sql': "SELECT s.name AS name, COUNT(*) AS cnt FROM easypc_work_orders_services j JOIN easypc_services s ON s.id = j.easypc_services_id GROUP BY s.name ORDER BY cnt DESC LIMIT 10",
        'code': JS_PREAMBLE + """  rows = rows.slice().reverse();
  return {
    title: { text: "Top Services Requested", left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 40, top: 40, bottom: 10, containLabel: true },
    yAxis: { type: 'category', data: rows.map(function(r){ return r.name; }) },
    xAxis: { type: 'value', minInterval: 1 },
    series: [{ """ + HBAR_STYLE + """, data: rows.map(function(r){ return Number(r.cnt); }) }]
  };
}""",
    },
    {
        'name': 'easypc_chart_branch',
        'sql': "SELECT st.name AS name, COUNT(w.id) AS cnt FROM easypc_work_orders w JOIN easypc_stores st ON st.id = w.store GROUP BY st.name ORDER BY cnt DESC",
        'code': JS_PREAMBLE + """  return {
    title: { text: "Work Orders by Branch", left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, top: 40, bottom: 10, containLabel: true },
    xAxis: { type: 'category', data: rows.map(function(r){ return r.name; }), axisLabel: { interval: 0, rotate: 12 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ """ + BAR_STYLE + """, data: rows.map(function(r){ return Number(r.cnt); }) }]
  };
}""",
    },
    {
        'name': 'easypc_chart_parts',
        'sql': "SELECT part_type AS name, SUM(qty) AS cnt FROM easypc_work_order_parts_used GROUP BY part_type ORDER BY cnt DESC",
        'code': JS_PREAMBLE + PART_LABELS + """  return {
    title: { text: "Replacement Parts Used", left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [{ """ + PIE_STYLE + """,
      data: rows.map(function(r){ return { name: labels[r.name] || r.name, value: Number(r.cnt) }; }) }]
  };
}""",
    },
]


def ensure_flow(name, sql, code):
    flow = find_by('flows', 'name', name)
    if not flow:
        st, res = api('POST', '/flows', {
            'name': name, 'icon': 'bar_chart', 'color': BRAND,
            'status': 'active', 'trigger': 'webhook', 'accountability': 'all',
            'options': {'error_on_reject': True}})
        flow = res.get('data') or {}
        print('flow created:', name, st)
    fid = flow['id']

    st, res = api('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={fid}&fields=id,key,type,options')
    ops = {o['key']: o for o in res.get('data', [])}

    # chart (exec) op — last in chain
    chart_body = {'flow': fid, 'name': 'Build Option', 'key': 'chart', 'type': 'exec',
                  'position_x': 19, 'position_y': 41, 'options': {'code': code}}
    if 'chart' in ops:
        api('PATCH', f"/operations/{ops['chart']['id']}", {'options': {'code': code}})
        chart_id = ops['chart']['id']
    else:
        st, res = api('POST', '/operations', chart_body)
        chart_id = (res.get('data') or {}).get('id')

    # sql op — resolves into chart op
    if 'sql_1' in ops:
        api('PATCH', f"/operations/{ops['sql_1']['id']}",
            {'options': {'sql': sql, 'binding': []}, 'resolve': chart_id})
        sql_id = ops['sql_1']['id']
    else:
        st, res = api('POST', '/operations', {
            'flow': fid, 'name': 'SQL', 'key': 'sql_1', 'type': 'likha_sql',
            'position_x': 19, 'position_y': 1, 'resolve': chart_id,
            'options': {'sql': sql, 'binding': []}})
        sql_id = (res.get('data') or {}).get('id')

    if flow.get('operation') != sql_id:
        api('PATCH', f'/flows/{fid}', {'operation': sql_id})
    return fid


def ensure_panel(dash_id, name, ptype, x, y, w, h, options):
    st, res = api('GET', f'/panels?filter%5Bdashboard%5D%5B_eq%5D={dash_id}'
                  f'&filter%5Bname%5D%5B_eq%5D={urllib.parse.quote(name, safe="")}&limit=1')
    existing = (res.get('data') or [None])[0]
    body = {'dashboard': dash_id, 'name': name, 'type': ptype, 'icon': None,
            'show_header': True,
            'position_x': x, 'position_y': y, 'width': w, 'height': h, 'options': options}
    if existing:
        api('PATCH', f"/panels/{existing['id']}", body)
        return existing['id']
    st, res = api('POST', '/panels', body)
    return (res.get('data') or {}).get('id')


# ---------- build flows ----------
flow_ids = {}
for c in CHARTS:
    flow_ids[c['name']] = ensure_flow(c['name'], c['sql'], c['code'])
print('flows:', json.dumps(flow_ids, indent=1))

# ---------- dashboard ----------
dash = find_by('dashboards', 'name', 'EasyPC Dashboard')
if not dash:
    st, res = api('POST', '/dashboards', {
        'name': 'EasyPC Dashboard', 'icon': 'space_dashboard', 'color': BRAND,
        'note': 'Service operations overview'})
    dash = res.get('data') or {}
    print('dashboard created:', st)
did = dash['id']

# ---------- metric panels (top row, same grid as BIS) ----------
METRICS = [
    ('Open Work Orders', {'collection': 'easypc_work_orders', 'field': 'id', 'function': 'count',
      'sortField': None, 'filter': {'_and': [{'status': {'_nin': ['released', 'cancelled', 'unclaimed']}}]}}),
    ('Ready for Pickup', {'collection': 'easypc_work_orders', 'field': 'id', 'function': 'count',
      'sortField': None, 'filter': {'_and': [{'status': {'_eq': 'ready_for_release'}}]}}),
    ('Awaiting Approval', {'collection': 'easypc_work_orders', 'field': 'id', 'function': 'count',
      'sortField': None, 'filter': {'_and': [{'status': {'_eq': 'awaiting_approval'}}]}}),
    ('Customers', {'collection': 'easypc_customers', 'field': 'id', 'function': 'count',
      'sortField': None}),
    ('Revenue Released', {'collection': 'easypc_work_orders', 'field': 'amount', 'function': 'sum',
      'sortField': None, 'filter': {'_and': [{'status': {'_eq': 'released'}}]}}),
    ('Bookings Ahead', {'collection': 'easypc_appointments', 'field': 'id', 'function': 'count',
      'sortField': None, 'filter': {'_and': [{'preferred_date': {'_gte': '$NOW'}},
                                           {'status': {'_eq': 'confirmed'}}]}}),
]
for i, (name, opts) in enumerate(METRICS):
    ensure_panel(did, name, 'metric', 1 + i * 9, 1, 8, 9, opts)
    print('metric panel:', name)

# ---------- echarts panels (2 cols x 3 rows, same grid as BIS) ----------
ECHART_PANELS = [
    ('Work Order Intake Trend', 'easypc_chart_intake_trend'),
    ('Monthly Revenue', 'easypc_chart_revenue'),
    ('Work Orders by Status', 'easypc_chart_status'),
    ('Top Services', 'easypc_chart_top_services'),
    ('Work Orders by Branch', 'easypc_chart_branch'),
    ('Parts Used', 'easypc_chart_parts'),
]
for i, (name, flow_name) in enumerate(ECHART_PANELS):
    x = 1 if i % 2 == 0 else 29
    y = 11 + (i // 2) * 22
    ensure_panel(did, name, 'echarts-panel', x, y, 27, 22,
                 {'flow': {'key': flow_ids[flow_name], 'collection': 'directus_flows'}})
    print('echarts panel:', name)

print('done — dashboard id:', did)
