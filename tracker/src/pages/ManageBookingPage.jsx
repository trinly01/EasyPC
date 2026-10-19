import { useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { manageAppointment } from "@/lib/api"

const inputCls =
  "w-full h-11 rounded-md border border-input bg-background px-3 text-sm font-mono placeholder:font-sans placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
const labelCls = "text-xs font-medium text-muted-foreground mb-1 block"

const STATUS_VARIANT = {
  confirmed: "default", arrived: "secondary", cancelled: "destructive",
  no_show: "destructive", rescheduled: "secondary",
}

export default function ManageBookingPage() {
  const [params] = useSearchParams()
  const [ref, setRef] = useState(params.get("ref") || "")
  const [mobile, setMobile] = useState("")
  const [booking, setBooking] = useState(null)
  const [resched, setResched] = useState(false)
  const [newDate, setNewDate] = useState("")
  const [newTime, setNewTime] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState("")

  async function call(action, extra) {
    setBusy(true)
    setError("")
    setNote("")
    try {
      const res = await manageAppointment(ref, mobile, action, extra)
      if (!res.found) {
        setError("No booking found for that reference + mobile number.")
        setBooking(null)
      } else if (res.error) {
        setError(res.error)
      } else {
        setBooking(res.booking)
        if (action === "cancel") setNote("Booking cancelled.")
        if (action === "reschedule") { setNote("Booking moved."); setResched(false) }
      }
    } catch (e) {
      setError(e.message === "Request failed (500)" ? "Action failed — the date may be full or the branch closed." : e.message)
    } finally {
      setBusy(false)
    }
  }

  const canAct = booking && booking.status !== "cancelled" && booking.status !== "arrived"

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="mb-6 text-center">
        <div className="text-4xl font-black tracking-tight">
          <span className="text-primary">EASY</span>PC
        </div>
        <p className="text-muted-foreground text-sm mt-1">TECH IT EASY — Manage booking</p>
      </div>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Your appointment</CardTitle>
          <CardDescription>Enter your appointment number and registered mobile.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <label className={labelCls}>Appointment no.</label>
            <input className={`${inputCls} uppercase`} placeholder="APPT-2026-0001"
              value={ref} onChange={(e) => setRef(e.target.value)} />
          </div>
          <div>
            <label className={labelCls}>Registered mobile</label>
            <input className={inputCls} inputMode="tel" placeholder="09xx xxx xxxx or last 4"
              value={mobile} onChange={(e) => setMobile(e.target.value)} />
          </div>
          {!booking && (
            <Button className="w-full" onClick={() => call("view")} disabled={busy || !ref || !mobile}>
              {busy ? "Checking…" : "Find booking"}
            </Button>
          )}

          {booking && (
            <div className="rounded-md border border-border p-3 space-y-1 text-sm">
              <div className="flex justify-between items-center">
                <span className="font-mono font-bold">{booking.appointment_no}</span>
                <Badge variant={STATUS_VARIANT[booking.status] || "secondary"}>{booking.status}</Badge>
              </div>
              <div className="text-muted-foreground">{booking.customer_name}</div>
              <div>{booking.store}</div>
              <div>{booking.service}{booking.service_price ? ` — ₱${booking.service_price}` : ""}</div>
              <div className="font-medium">{booking.date} {booking.time}</div>
            </div>
          )}

          {canAct && !resched && (
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setResched(true)}>Reschedule</Button>
              <Button variant="destructive" className="flex-1" onClick={() => call("cancel")} disabled={busy}>Cancel</Button>
            </div>
          )}

          {resched && (
            <div className="space-y-2 rounded-md border border-border p-3">
              <label className={labelCls}>New date</label>
              <input type="date" className={inputCls} value={newDate} onChange={(e) => setNewDate(e.target.value)} />
              <label className={labelCls}>New time</label>
              <input type="time" className={inputCls} value={newTime} onChange={(e) => setNewTime(e.target.value)} />
              <div className="flex gap-2">
                <Button className="flex-1" disabled={busy || !newDate}
                  onClick={() => call("reschedule", { new_date: newDate, new_time: newTime })}>
                  {busy ? "Saving…" : "Confirm new slot"}
                </Button>
                <Button variant="outline" onClick={() => setResched(false)}>Back</Button>
              </div>
            </div>
          )}

          {note && <p className="text-sm text-primary">{note}</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}

          <p className="text-center text-xs text-muted-foreground">
            <Link to="/book" className="text-primary underline">Book a new appointment</Link>
          </p>
        </CardContent>
      </Card>
      <p className="text-muted-foreground text-xs mt-8">© EasyPC — Authorized service centers</p>
    </div>
  )
}
