// Public tracking lookup — hits the easypc_track_lookup webhook flow.
// No auth: the flow validates (wo + token) server-side and returns a
// sanitized payload only. Direct collection access is denied to public.
const LOOKUP_URL =
  "https://likha-playground.zyberlab.com/flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70"

export async function lookupWorkOrder(wo, token) {
  const res = await fetch(LOOKUP_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wo, token }),
  })
  if (!res.ok) throw new Error("Lookup failed (" + res.status + ")")
  const data = await res.json()
  return data && data.found ? data.work_order : null
}
