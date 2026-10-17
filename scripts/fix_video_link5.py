import json, os, urllib.request, urllib.error

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

st, fls = api('GET', '/flows?filter%5Bname%5D%5B_eq%5D=easypc_video_link')
fid = fls['data'][0]['id']
st, ops = api('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=' + fid)
genlink = [o for o in ops['data'] if o['key'] == 'genlink'][0]
mkupd = [o for o in ops['data'] if o['key'] == 'mkupdate'][0]

code_gen = '''module.exports = async function(data){
  const t = data.$trigger || {};
  const p = t.payload || {};
  const st = p.status;
  if (st !== "in_repair" && st !== "testing") throw new Error("not a video milestone");
  const wo = data.$last || {};
  const key = (t.keys||[])[0];
  let link = wo.video_call_link;
  const existed = !!link;
  if (!link) {
    const rand = Math.random().toString(36).slice(2, 10);
    const num = wo.work_order_number || String(key).slice(0,8);
    const slug = ("easypc-" + num + "-" + rand).toLowerCase().replace(/[^a-z0-9-]/g,"");
    link = "https://meet.jit.si/" + slug;
  }
  let msg;
  if (st === "testing") {
    msg = "Your unit is now in final testing — join the video call to watch the live diagnostics and see your unit working: " + link;
  } else {
    msg = existed
      ? "Work on your unit has resumed. Video call link if needed: " + link
      : "Your unit is now being worked on by our technician. Join the video call to see the actual work: " + link;
  }
  return { key: key, link: link, msg: msg, milestone: st };
}'''
st, res = api('PATCH', '/operations/' + genlink['id'], {'options': {'code': code_gen}})
print('genlink:', st)

# milestone now dynamic
st, res = api('PATCH', '/operations/' + mkupd['id'], {'options': {
    'collection': 'easypc_work_order_updates',
    'payload': {'work_order': '{{genlink.key}}', 'update_type': 'milestone',
                'milestone': '{{genlink.milestone}}', 'message': '{{genlink.msg}}',
                'notify_customer': True},
    'permissions': '$full'}})
print('mkupdate:', st)

# drop 'testing' from milestone flow's map — video_link flow owns that message now
st, fls2 = api('GET', '/flows?filter%5Bname%5D%5B_eq%5D=easypc_status_milestone')
st2, ops2r = api('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=' + fls2['data'][0]['id'])
chk = [o for o in ops2r['data'] if o['key'] == 'check'][0]
code = chk['options']['code'].replace(
    '"testing": "Repair work on your unit is complete and it is now in final testing.", ', '')
st, res = api('PATCH', '/operations/' + chk['id'], {'options': {'code': code}})
print('milestone map minus testing:', st, '| testing removed:', '"testing"' not in code)
