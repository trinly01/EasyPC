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

code_gen = '''module.exports = async function(data){
  const t = data.$trigger || {};
  const p = t.payload || {};
  if (p.status !== "in_repair") throw new Error("not entering in_repair");
  const wo = data.$last || {};
  const key = (t.keys||[])[0];
  let link = wo.video_call_link;
  let resumed = !!link;
  if (!link) {
    const rand = Math.random().toString(36).slice(2, 10);
    const num = wo.work_order_number || String(key).slice(0,8);
    const slug = ("easypc-" + num + "-" + rand).toLowerCase().replace(/[^a-z0-9-]/g,"");
    link = "https://meet.jit.si/" + slug;
  }
  const msg = resumed
    ? "Work on your unit has resumed. Video call link if needed: " + link
    : "Your unit is now being worked on by our technician. Join the video call for updates/questions: " + link;
  return { key: key, link: link, msg: msg };
}'''
st, res = api('PATCH', '/operations/' + genlink['id'], {'options': {'code': code_gen}})
print('genlink updated:', st)
