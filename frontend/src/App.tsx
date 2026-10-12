import { useEffect, useState } from "react"
import { ArrowDown, ArrowUp, Droplets, House, RefreshCw, Thermometer, WifiOff } from "lucide-react"
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type Metric = "temperature_c" | "humidity_pct"
type Range = "24h" | "7d" | "30d" | "1y"
type Point = { ts: number; temperature_c: number | null; humidity_pct: number | null; gap_before: boolean }
type Snapshot = {
  server_time: number; status: "online" | "offline"; range: Range; bucket_seconds: number;
  latest: { measured_at: number; temperature_c: number; humidity_pct: number } | null;
  points: Point[];
  stats: { temperature_min: number | null; temperature_max: number | null; temperature_avg: number | null;
    humidity_min: number | null; humidity_max: number | null; humidity_avg: number | null; samples: number };
}
const ranges: { value: Range; label: string }[] = [
  { value: "24h", label: "Last 24 hours" }, { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" }, { value: "1y", label: "Last year" },
]
const number = (n: number | null | undefined) => n == null ? "-" : n.toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const date = (ts: number, options: Intl.DateTimeFormatOptions) => new Date(ts * 1000).toLocaleString("en-GB", { timeZone: "Europe/Warsaw", hour12: false, ...options })

export default function App() {
  const [range, setRange] = useState<Range>("24h")
  const [metric, setMetric] = useState<Metric>("temperature_c")
  const [data, setData] = useState<Snapshot | null>(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refresh, setRefresh] = useState(0)
  const [receivedAt, setReceivedAt] = useState(0)
  const [clock, setClock] = useState(Date.now())

  useEffect(() => {
    let disposed = false
    let timer: ReturnType<typeof setTimeout>
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      const timeout = setTimeout(() => controller.abort(), 12_000)
      try {
        const response = await fetch(`/api/room?range=${range}`, { signal: controller.signal, cache: "no-store" })
        if (!response.ok) throw new Error("Request failed")
        const snapshot: Snapshot = await response.json()
        if (!disposed) { setData(snapshot); setReceivedAt(Date.now()); setError(false) }
      } catch {
        if (!disposed) setError(true)
      } finally {
        clearTimeout(timeout)
        if (!disposed) {
          setLoading(false)
          timer = setTimeout(() => setRefresh(value => value + 1), 30_000)
        }
      }
    }
    void load()
    return () => { disposed = true; controller.abort(); clearTimeout(timer) }
  }, [range, refresh])

  useEffect(() => { const timer = setInterval(() => setClock(Date.now()), 10_000); return () => clearInterval(timer) }, [])

  const latest = data?.latest
  const age = latest && data ? data.server_time - latest.measured_at + Math.max(0, clock - receivedAt) / 1000 : Infinity
  const online = !error && data?.status === "online" && age <= 150
  const temperature = metric === "temperature_c"
  const unit = temperature ? "°C" : "%"
  const color = temperature ? "#e7aa7a" : "#8dbabf"
  const prefix = temperature ? "temperature" : "humidity"
  const points = (data?.points ?? []).flatMap(p => p.gap_before ? [
    { ...p, ts: p.ts - 1, temperature_c: null, humidity_pct: null }, p,
  ] : [p])
  const hasPoints = points.some(p => p[metric] != null)
  const selectedRange = ranges.find(r => r.value === (data?.range ?? range))!
  const ageText = age < 60 ? "just now" : age < 3600 ? `${Math.floor(age / 60)} min ago` :
    latest ? date(latest.measured_at, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "waiting for first reading"

  return <main className="page-shell">
    <header className="topbar">
      <a href="/" className="brand" aria-label="room-temp home"><span className="brand-icon"><House size={18} strokeWidth={1.6} /></span>room<span className="brand-separator">-</span>temp</a>
      <div className="header-actions">
        <div className={cn("connection", online && "connected")} role="status"><span className="status-dot" />{loading && !data ? "Connecting" : online ? "Sensor online" : error ? "Connection lost" : "Sensor offline"}</div>
        <Button variant="ghost" size="icon" aria-label="Refresh readings" disabled={loading} onClick={() => setRefresh(v => v + 1)}><RefreshCw size={14} className={loading ? "refreshing" : ""} /></Button>
      </div>
    </header>

    {(error || (data && !online)) && <div className="notice" role="status"><WifiOff size={16} /><span>{error ? "Unable to load readings. Retrying automatically." : "No recent reading. Missing readings appear as gaps in the chart."}{latest ? " Showing the last saved reading." : ""}</span></div>}

    <section className="readings" aria-label="Latest reading">
      <MetricCard label="Temperature" value={latest?.temperature_c} unit="°C" icon={<Thermometer size={20} />} accent="warm" active={temperature} onClick={() => setMetric("temperature_c")} stale={!!latest && !online} loading={loading && !data} />
      <MetricCard label="Humidity" value={latest?.humidity_pct} unit="%" icon={<Droplets size={20} />} accent="cool" active={!temperature} onClick={() => setMetric("humidity_pct")} stale={!!latest && !online} loading={loading && !data} />
    </section>

    <div className="reading-meta"><span><span className={cn("tiny-dot", online && "live")} />Latest reading: {ageText}</span><span>Measured every minute</span></div>

    <Card className="history-card">
      <div className="history-header">
        <h2>{temperature ? "Temperature" : "Humidity"}</h2>
        <select className="range-select" aria-label="History range" value={range} onChange={event => setRange(event.target.value as Range)}>
          {ranges.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </div>
      <div className="chart-caption"><span>{data && data.bucket_seconds > 60 ? `${data.bucket_seconds / 60}-minute averages` : "One-minute readings"}</span></div>
      <div className="chart-wrap" aria-busy={loading} role="img" aria-label={`Chart: ${temperature ? "temperature" : "humidity"}, ${selectedRange.label}. Missing readings are shown as gaps.`}>
        {hasPoints ? <ResponsiveContainer width="100%" height="100%"><LineChart data={points} margin={{ top: 15, right: 12, bottom: 5, left: -22 }} accessibilityLayer>
          <CartesianGrid vertical={false} stroke="#252729" strokeDasharray="3 5" />
          <XAxis dataKey="ts" type="number" domain={["dataMin", "dataMax"]} tickLine={false} axisLine={false} tick={{ fill: "#85898d", fontSize: 11 }} minTickGap={45} tickMargin={16} tickFormatter={ts => date(ts, data?.range === "24h" ? { hour: "2-digit", minute: "2-digit" } : { day: "numeric", month: "short" })} />
          <YAxis domain={temperature ? ["auto", "auto"] : [0, 100]} tickLine={false} axisLine={false} tick={{ fill: "#85898d", fontSize: 11 }} tickFormatter={v => `${number(v)}${unit}`} width={70} />
          <Tooltip contentStyle={{ background: "#191b1d", border: "1px solid #343638", borderRadius: 10, color: "#eee", fontSize: 12 }} labelFormatter={ts => date(Number(ts), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })} formatter={value => [`${number(Number(value))} ${unit}`, temperature ? "Temperature" : "Humidity"]} />
          <Line type="linear" dataKey={metric} stroke={color} strokeWidth={2} dot={points.filter(p => p[metric] != null).length < 3 ? { r: 3 } : false} activeDot={{ r: 4, stroke: "#151617", strokeWidth: 2 }} connectNulls={false} isAnimationActive={false} />
        </LineChart></ResponsiveContainer> : <div className="empty-chart"><span className="empty-icon">{temperature ? <Thermometer size={25} /> : <Droplets size={25} />}</span><h3>{loading ? "Loading readings" : "No history yet"}</h3><p>{loading ? "Readings will appear shortly." : "The chart will appear once sensor readings arrive."}</p></div>}
      </div>
      <div className="chart-stats">
        <Stat label="Min" value={data?.stats[`${prefix}_min`]} unit={unit} icon={<ArrowDown size={13} />} />
        <Stat label="Avg" value={data?.stats[`${prefix}_avg`]} unit={unit} />
        <Stat label="Max" value={data?.stats[`${prefix}_max`]} unit={unit} icon={<ArrowUp size={13} />} />
      </div>
    </Card>


  </main>
}

function MetricCard({ label, value, unit, icon, accent, active, onClick, stale, loading }: {
  label: string; value?: number; unit: string; icon: React.ReactNode; accent: string;
  active: boolean; onClick: () => void; stale: boolean; loading: boolean;
}) {
  return <Card className={cn("metric-card", accent, active && "active")}><button className="metric-button" onClick={onClick} aria-pressed={active} aria-label={`Show chart: ${label.toLowerCase()}`}>
    <span className="metric-label">{label}<span className="metric-icon">{icon}</span></span>
    <span className={cn("metric-value", loading && "skeleton")}>{number(value)}<span className="unit">{unit}</span></span>
    <span className="metric-bottom">{stale ? "Last saved reading" : value == null ? "Waiting for sensor" : ""}<span className="metric-indicator" /></span>
  </button></Card>
}

function Stat({ label, value, unit, icon }: { label: string; value?: number | null; unit: string; icon?: React.ReactNode }) {
  return <div className="stat"><span>{icon}{label}</span><strong>{number(value)}<small>{unit}</small></strong></div>
}
