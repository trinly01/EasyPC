import { useEffect, useState } from "react"
import { getSlots } from "@/lib/api"

// Calendly-style time-slot grid: fetches live availability per store+date,
// disables full / past / closed slots. Slots come pre-generated server-side
// from the branch's open/close hours and slot_minutes.
export default function SlotPicker({ store, date, value, onChange }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState("")

  useEffect(() => {
    setData(null)
    setErr("")
    if (!store || !date) return
    let alive = true
    setLoading(true)
    getSlots(store, date)
      .then((d) => alive && setData(d))
      .catch(() => alive && setErr("Could not load time slots"))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [store, date])

  if (!store || !date) {
    return <p className="text-xs text-muted-foreground">Pick a branch and date first.</p>
  }
  if (loading) {
    return <p className="text-xs text-muted-foreground animate-pulse">Loading available times…</p>
  }
  if (err) return <p className="text-xs text-destructive">{err}</p>
  if (!data) return null
  if (data.closed) {
    return <p className="text-xs text-destructive">Branch is closed that day.</p>
  }
  if (!data.slots?.length) {
    return <p className="text-xs text-muted-foreground">No slots configured for this branch.</p>
  }

  return (
    <div className="grid grid-cols-3 gap-2">
      {data.slots.map((s) => {
        const sel = value === s.time
        return (
          <button
            key={s.time}
            type="button"
            disabled={!s.available}
            onClick={() => onChange(s.time)}
            className={
              "h-10 rounded-md border text-sm font-mono transition-colors " +
              (sel
                ? "bg-primary text-primary-foreground border-primary"
                : s.available
                ? "border-border hover:border-primary hover:text-primary"
                : "border-border/50 text-muted-foreground/40 line-through cursor-not-allowed")
            }
            title={s.available ? `${s.remaining} slot${s.remaining === 1 ? "" : "s"} left` : "Fully booked"}
          >
            {s.time}
          </button>
        )
      })}
    </div>
  )
}
