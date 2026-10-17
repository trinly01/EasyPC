import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function LookupPage() {
  const [wo, setWo] = useState("")
  const [token, setToken] = useState("")
  const navigate = useNavigate()

  function submit(e) {
    e.preventDefault()
    const w = wo.trim().toUpperCase()
    const t = token.trim().toLowerCase()
    if (w && t) navigate(`/track/${w}/${t}`)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="mb-8 text-center">
        <div className="text-4xl font-black tracking-tight">
          <span className="text-primary">EASY</span>PC
        </div>
        <p className="text-muted-foreground text-sm mt-1">TECH IT EASY — Repair Tracking</p>
      </div>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Track your repair</CardTitle>
          <CardDescription>
            Enter the Work Order number and tracking code printed on your service form.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <input
              className="w-full h-11 rounded-md border border-input bg-background px-3 text-sm font-mono uppercase placeholder:normal-case placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="WO-2026-0001"
              value={wo}
              onChange={(e) => setWo(e.target.value)}
            />
            <input
              className="w-full h-11 rounded-md border border-input bg-background px-3 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Tracking code"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <Button type="submit" className="w-full" size="lg">
              Track
            </Button>
          </form>
        </CardContent>
      </Card>
      <p className="text-muted-foreground text-xs mt-8">© EasyPC — Authorized service centers</p>
    </div>
  )
}
