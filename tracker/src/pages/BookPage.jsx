import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { getBookingOptions, bookAppointment } from "@/lib/api"
import SlotPicker from "@/components/SlotPicker"
import SearchableSelect from "@/components/SearchableSelect"

const inputCls =
  "w-full h-11 rounded-md border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
const labelCls = "text-xs font-medium text-muted-foreground mb-1 block"

const DAY_KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]

export default function BookPage() {
  const [options, setOptions] = useState(null)
  const [form, setForm] = useState({
    store: "", service: "", preferred_date: "", preferred_time: "",
    first_name: "", last_name: "", mobile: "", email: "",
    unit_type: "", concern: "",
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [done, setDone] = useState(null)

  useEffect(() => {
    getBookingOptions().then(setOptions).catch(() => setError("Could not load booking options"))
  }, [])

  const store = useMemo(
    () => options?.stores?.find((s) => s.id === form.store),
    [options, form.store]
  )
  const maxDate = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + (store?.max_advance_days || 30))
    return d.toISOString().slice(0, 10)
  }, [store])
  const today = new Date().toISOString().slice(0, 10)
  const dayClosed =
    form.preferred_date && store?.open_days?.length
      ? !store.open_days.includes(DAY_KEYS[new Date(form.preferred_date + "T00:00:00").getDay()])
      : false

  const set = (k) => (e) => {
    const next = { ...form, [k]: e.target.value }
    if (k === "store" || k === "preferred_date") next.preferred_time = ""
    setForm(next)
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError("")
    try {
      const res = await bookAppointment(form)
      if (!res || !res.appointment_no)
        throw new Error("That slot can't be booked — it may be full or the branch closed. Pick another.")
      setDone(res)
    } catch (err) {
      setError(err.message === "Request failed (500)" ? "That slot can't be booked — try another date." : err.message)
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <CardTitle className="text-primary">Booking confirmed</CardTitle>
            <CardDescription>A confirmation email is on its way.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-black font-mono text-primary">{done.appointment_no}</div>
            <p className="text-sm text-muted-foreground">
              {done.store} — {done.date} {done.time}
            </p>
            <p className="text-xs text-muted-foreground pt-3">
              Keep this reference. To reschedule or cancel, go to Manage booking
              and use this number + your registered mobile.
            </p>
            <div className="flex gap-2 pt-4">
              <Link to="/book/manage" className="flex-1">
                <Button variant="outline" className="w-full">Manage booking</Button>
              </Link>
              <Link to="/" className="flex-1">
                <Button className="w-full">Track a repair</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="mb-6 text-center">
        <div className="text-4xl font-black tracking-tight">
          <span className="text-primary">EASY</span>PC
        </div>
        <p className="text-muted-foreground text-sm mt-1">TECH IT EASY — Book a service</p>
      </div>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Book an appointment</CardTitle>
          <CardDescription>
            Reserve a slot before bringing your unit in. Instant confirmation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className={labelCls}>Branch</label>
              <SearchableSelect
                placeholder="Search branches…"
                value={form.store}
                onChange={(id) => setForm({ ...form, store: id, preferred_time: "" })}
                items={(options?.stores || []).map((s) => ({
                  id: s.id, label: s.name,
                  sub: `${s.code} · ${s.open_time}–${s.close_time}`,
                }))}
              />
            </div>
            <div>
              <label className={labelCls}>Service</label>
              <select className={inputCls} value={form.service} onChange={set("service")} required>
                <option value="">Select service</option>
                {options?.services?.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} — ₱{s.price}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Preferred date</label>
              <input type="date" className={inputCls} min={today} max={maxDate}
                value={form.preferred_date} onChange={set("preferred_date")} required />
              {dayClosed && (
                <p className="text-xs text-destructive mt-1">Branch is closed that day</p>
              )}
            </div>
            <div>
              <label className={labelCls}>Preferred time</label>
              <SlotPicker store={form.store} date={form.preferred_date}
                value={form.preferred_time}
                onChange={(t) => setForm({ ...form, preferred_time: t })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelCls}>First name</label>
                <input className={inputCls} value={form.first_name} onChange={set("first_name")} required />
              </div>
              <div>
                <label className={labelCls}>Last name</label>
                <input className={inputCls} value={form.last_name} onChange={set("last_name")} />
              </div>
            </div>
            <div>
              <label className={labelCls}>Mobile number</label>
              <input className={`${inputCls} font-mono`} inputMode="tel"
                placeholder="09xx xxx xxxx" value={form.mobile} onChange={set("mobile")} required />
            </div>
            <div>
              <label className={labelCls}>Email</label>
              <input type="email" className={inputCls} placeholder="you@email.com"
                value={form.email} onChange={set("email")} required />
            </div>
            <div>
              <label className={labelCls}>Unit type</label>
              <input className={inputCls} placeholder="e.g. Laptop, Desktop, AIO"
                value={form.unit_type} onChange={set("unit_type")} />
            </div>
            <div>
              <label className={labelCls}>Concern / issue</label>
              <textarea className={`${inputCls} h-20 py-2 resize-none`} placeholder="Describe the problem"
                value={form.concern} onChange={set("concern")} />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" size="lg"
              disabled={busy || dayClosed || !form.preferred_time}>
              {busy ? "Booking…" : "Confirm booking"}
            </Button>
          </form>
          <p className="text-center text-xs text-muted-foreground mt-3">
            Have an appointment already? <Link to="/book/manage" className="text-primary underline">Manage booking</Link>
          </p>
        </CardContent>
      </Card>
      <p className="text-muted-foreground text-xs mt-8">© EasyPC — Authorized service centers</p>
    </div>
  )
}
