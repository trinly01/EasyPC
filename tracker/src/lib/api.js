// Public tracking lookup — hits the easypc_track_lookup webhook flow.
// No auth: the flow validates (wo + key) server-side and returns a
// sanitized payload only. `key` is the customer's mobile number
// (full or last 4 digits); the random tracking token still works too.
// Direct collection access is denied to public.
const LOOKUP_URL =
  "https://likha-playground.zyberlab.com/flows/trigger/eedd97d4-5c26-4e47-a26f-040806686d70"
const APPT_OPTIONS_URL =
  "https://likha-playground.zyberlab.com/flows/trigger/ed1c258e-54b1-4183-9a3a-492f4d054efc"
const APPT_BOOK_URL =
  "https://likha-playground.zyberlab.com/flows/trigger/9bf3bc0a-1bb5-4613-be99-1f6dac87eee4"
const APPT_MANAGE_URL =
  "https://likha-playground.zyberlab.com/flows/trigger/671f175c-b048-4e87-88e9-2563e5a972db"

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error("Request failed (" + res.status + ")")
  return res.json()
}

export async function lookupWorkOrder(wo, key) {
  const data = await post(LOOKUP_URL, { wo, key })
  return data && data.found ? data.work_order : null
}

// Appointment booking — easypc_appointment_* flows (public webhooks,
// capacity + branch rules enforced server-side).
export async function getBookingOptions() {
  const res = await fetch(APPT_OPTIONS_URL)
  if (!res.ok) throw new Error("Failed to load booking options")
  return res.json()
}

export async function bookAppointment(payload) {
  return post(APPT_BOOK_URL, payload)
}

export async function manageAppointment(ref, mobile, action, extra = {}) {
  return post(APPT_MANAGE_URL, { ref, mobile, action, ...extra })
}
