import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { lookupWorkOrder } from "@/lib/api"
import { JOURNEY, STATUS_LABEL, STATUS_DESC, statusVariant } from "@/lib/status"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Check, Circle, Video, ShieldCheck, Store, Monitor, Loader2 } from "lucide-react"

function fmt(ts) {
  if (!ts) return null
  const d = new Date(ts.replace(" ", "T"))
  return isNaN(d) ? ts : d.toLocaleString("en-PH", { dateStyle: "medium", timeStyle: "short" })
}

export default function TrackPage() {
  const { wo, key } = useParams()
  const [state, setState] = useState({ loading: true, error: null, data: null })

  useEffect(() => {
    lookupWorkOrder(wo, key)
      .then((data) => setState({ loading: false, error: data ? null : "notfound", data }))
      .catch((e) => setState({ loading: false, error: e.message, data: null }))
  }, [wo, key])

  if (state.loading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-primary" size={40} />
      </div>
    )

  if (state.error || !state.data)
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4 text-center">
        <div className="text-3xl font-black mb-2"><span className="text-primary">EASY</span>PC</div>
        <p className="text-muted-foreground mb-6">
          We couldn't find that work order. Check the work order number and
          mobile number you registered with us.
        </p>
        <Link to="/"><Button variant="outline">Back to lookup</Button></Link>
      </div>
    )

  const d = state.data
  const currentIdx = JOURNEY.indexOf(d.status)
  const isException = d.status === "cancelled" || d.status === "unclaimed"

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-2xl mx-auto">
      {/* header */}
      <div className="flex items-center justify-between mb-6">
        <div className="text-2xl font-black tracking-tight">
          <span className="text-primary">EASY</span>PC
        </div>
        <Badge variant={statusVariant(d.status)}>{STATUS_LABEL[d.status] || d.status}</Badge>
      </div>

      {/* work order card */}
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="font-mono">{d.number}</CardTitle>
          <CardDescription>{STATUS_DESC[d.status]}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          {d.unit && (
            <div className="flex items-center gap-2">
              <Monitor size={16} className="text-muted-foreground shrink-0" />
              <span>{d.unit} <span className="text-muted-foreground">({d.unit_type})</span></span>
            </div>
          )}
          {d.store && (
            <div className="flex items-center gap-2">
              <Store size={16} className="text-muted-foreground shrink-0" />
              <span>{d.store.name}</span>
            </div>
          )}
          {d.received && <div className="text-muted-foreground">Received: {fmt(d.received)}</div>}
          {d.released_at && <div className="text-muted-foreground">Released: {fmt(d.released_at)}</div>}
          {d.service_warranty_until && (
            <div className="flex items-center gap-2 text-success">
              <ShieldCheck size={16} className="shrink-0" />
              <span>Service warranty until {fmt(d.service_warranty_until)}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* video call */}
      {d.video_call_link && (
        <Card className="mb-4 border-primary/40">
          <CardContent className="pt-6 flex items-center justify-between gap-4">
            <div>
              <div className="font-semibold">Live with our technician</div>
              <p className="text-sm text-muted-foreground">
                See the actual work on your unit — no account needed.
              </p>
            </div>
            <a href={d.video_call_link} target="_blank" rel="noreferrer">
              <Button><Video size={16} /> Join call</Button>
            </a>
          </CardContent>
        </Card>
      )}

      {/* services */}
      {d.services?.length > 0 && (
        <Card className="mb-4">
          <CardHeader><CardTitle className="text-base">Services</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-1">
            {d.services.map((s, i) => (
              <div key={i} className="flex justify-between">
                <span>{s.name}</span>
                <span className="text-muted-foreground font-mono">₱{Number(s.charged_price).toLocaleString()}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* journey timeline */}
      <Card>
        <CardHeader><CardTitle className="text-base">Progress</CardTitle></CardHeader>
        <CardContent>
          {isException ? (
            <p className="text-destructive text-sm">{STATUS_DESC[d.status]}</p>
          ) : (
            <ol className="relative border-l border-border ml-2 space-y-5">
              {JOURNEY.map((s, i) => {
                const done = i < currentIdx
                const current = i === currentIdx
                if (currentIdx === -1) return null
                return (
                  <li key={s} className="ml-5 relative">
                    <span className={
                      "absolute -left-[1.72rem] flex h-5 w-5 items-center justify-center rounded-full border " +
                      (done ? "bg-primary border-primary text-primary-foreground"
                           : current ? "bg-background border-primary"
                                     : "bg-secondary border-border")
                    }>
                      {done ? <Check size={12} /> : <Circle size={8} className={current ? "text-primary fill-primary" : "text-muted-foreground"} />}
                    </span>
                    <div className={current ? "font-semibold text-primary" : done ? "" : "text-muted-foreground"}>
                      {STATUS_LABEL[s]}
                    </div>
                    {current && <div className="text-xs text-muted-foreground mt-0.5">{STATUS_DESC[s]}</div>}
                  </li>
                )
              })}
            </ol>
          )}

          {/* activity log */}
          {d.updates?.length > 0 && (
            <div className="mt-6 pt-4 border-t border-border">
              <div className="text-sm font-semibold mb-2">Activity</div>
              <ul className="space-y-2">
                {[...d.updates].reverse().map((u, i) => (
                  <li key={i} className="text-xs">
                    <span className="text-muted-foreground">{fmt(u.date_created)} — </span>
                    <span>{u.message}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
