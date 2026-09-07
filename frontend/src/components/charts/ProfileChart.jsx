import { useMemo, useState } from 'react'
import { interp1d } from '../../lib/ocean'

export default function ProfileChart({
  profile,
  nominal,
  argo,
  depth,
  maxDepth = 1000,
  showUncertainty = true,
  compareNominal = false,
  onProbe,
}) {
  const [hover, setHover] = useState(null)

  const paths = useMemo(() => {
    if (!profile?.depths || !profile?.temperatures) return null
    const toXY = (d, t) => {
      const x = 60 + (t / 32) * 580
      const y = 20 + (d / maxDepth) * 320
      return [x, y]
    }
    const main = profile.depths.map((d, i) => toXY(d, profile.temperatures[i]))
    const mainD = `M ${main.map(([x, y]) => `${x},${y}`).join(' L ')}`
    let band = null
    if (showUncertainty && profile.uncertainties) {
      const up = profile.depths.map((d, i) => toXY(d, profile.temperatures[i] + profile.uncertainties[i]))
      const dn = [...profile.depths].reverse().map((d, idx) => {
        const i = profile.depths.length - 1 - idx
        return toXY(d, profile.temperatures[i] - profile.uncertainties[i])
      })
      band = `M ${up.map(([x, y]) => `${x},${y}`).join(' L ')} L ${dn.map(([x, y]) => `${x},${y}`).join(' L ')} Z`
    }
    let nom = null
    if (compareNominal && nominal?.depths) {
      nom = `M ${nominal.depths.map((d, i) => {
        const [x, y] = toXY(d, nominal.temperatures[i])
        return `${x},${y}`
      }).join(' L ')}`
    }
    const argoPts = (argo?.depths && argo?.observed_temps)
      ? argo.depths.map((d, i) => ({ d, t: argo.observed_temps[i], xy: toXY(d, argo.observed_temps[i]) }))
      : []
    return { mainD, band, nom, argoPts, toXY }
  }, [profile, nominal, argo, maxDepth, showUncertainty, compareNominal])

  if (!paths) {
    return <div className="chart-empty">Waiting for profile…</div>
  }

  const thermo = profile.thermocline || {}
  const d20Y = 20 + ((thermo.d20_depth_m || 0) / maxDepth) * 320
  const mldY = 20 + ((thermo.mld_m || 0) / maxDepth) * 320
  const probeY = 20 + (depth / maxDepth) * 320
  const probeT = interp1d(profile.depths, profile.temperatures, depth) ?? 0
  const probeX = 60 + (probeT / 32) * 580

  return (
    <div className="chart-wrap">
      <svg viewBox="0 0 720 380" className="chart-svg" role="img" aria-label="Vertical temperature profile">
        <defs>
          <linearGradient id="uncBand" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#00f0ff" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        {[0, 5, 10, 15, 20, 25, 30].map((temp) => {
          const x = 60 + (temp / 32) * 580
          return (
            <g key={temp}>
              <line x1={x} y1={20} x2={x} y2={340} className="grid-line" />
              <text x={x} y={360} className="axis-label" textAnchor="middle">{temp}°C</text>
            </g>
          )
        })}
        {[0, 200, 400, 600, 800, 1000].filter((d) => d <= maxDepth).map((d) => {
          const y = 20 + (d / maxDepth) * 320
          return (
            <g key={d}>
              <line x1={60} y1={y} x2={640} y2={y} className="grid-line" />
              <text x={50} y={y + 4} className="axis-label" textAnchor="end">{d}m</text>
            </g>
          )
        })}
        {thermo.d20_depth_m != null && (
          <g>
            <line x1={60} y1={d20Y} x2={640} y2={d20Y} stroke="#00f0ff" strokeDasharray="4 4" strokeWidth="1.4" opacity="0.8" />
            <text x={650} y={d20Y + 4} fill="#00f0ff" fontSize="10" fontWeight="700">D20</text>
          </g>
        )}
        {thermo.mld_m != null && (
          <g>
            <line x1={60} y1={mldY} x2={640} y2={mldY} stroke="#a855f7" strokeDasharray="4 4" strokeWidth="1.4" opacity="0.8" />
            <text x={650} y={mldY + 4} fill="#a855f7" fontSize="10" fontWeight="700">MLD</text>
          </g>
        )}
        {paths.band && <path d={paths.band} fill="url(#uncBand)" />}
        {paths.nom && <path d={paths.nom} fill="none" stroke="#fff" strokeWidth="2" strokeDasharray="5 4" opacity="0.75" />}
        <path d={paths.mainD} fill="none" stroke="#00f0ff" strokeWidth="3.2" className="glow-stroke" />
        {paths.argoPts.map((p, i) => (
          <circle key={i} cx={p.xy[0]} cy={p.xy[1]} r="3.5" fill="#10b981" stroke="#fff" strokeWidth="1" />
        ))}
        <line x1={60} y1={probeY} x2={640} y2={probeY} stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1.4" />
        <circle cx={probeX} cy={probeY} r="6" fill="#f59e0b" stroke="#fff" strokeWidth="2" />
        {hover && (
          <g>
            <line x1={60} y1={hover.y} x2={640} y2={hover.y} stroke="rgba(255,255,255,0.35)" strokeDasharray="2 2" />
            <circle cx={hover.x} cy={hover.y} r="5" fill="#fff" stroke="#00f0ff" strokeWidth="2" />
          </g>
        )}
        <rect
          x={60}
          y={20}
          width={580}
          height={320}
          fill="transparent"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect()
            const relY = (e.clientY - rect.top) / rect.height
            const z = Math.max(0, Math.min(maxDepth, relY * maxDepth))
            const t = interp1d(profile.depths, profile.temperatures, z)
            const u = interp1d(profile.depths, profile.uncertainties || [], z)
            const x = 60 + ((t || 0) / 32) * 580
            const y = 20 + (z / maxDepth) * 320
            setHover({ z: Math.round(z), t, u, x, y })
            onProbe?.(z)
          }}
          onMouseLeave={() => setHover(null)}
        />
      </svg>
      {hover && (
        <div className="chart-tip">
          <div>Depth {hover.z} m</div>
          <div>T {hover.t?.toFixed(2)} °C</div>
          {hover.u != null && <div>±{hover.u.toFixed(2)} °C</div>}
        </div>
      )}
    </div>
  )
}
