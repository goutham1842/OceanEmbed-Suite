import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import {
  getAblations,
  getArgoComparison,
  getHealth,
  getMap,
  getMetadata,
  getMetrics,
  getPrediction,
  getTransect,
  postProfile,
} from './api/client'
import BasinMap from './components/map/BasinMap'
import ProfileChart from './components/charts/ProfileChart'
import TransectHeatmap from './components/charts/TransectHeatmap'
import SubsurfaceCube from './components/three/SubsurfaceCube'
import {
  PRESET_SCENARIOS,
  SEASONS,
  clampCoord,
  computeTchp,
  downloadBlob,
  fmt,
  interp1d,
  snapGrid,
} from './lib/ocean'

const OceanScene = lazy(() => import('./components/three/OceanScene'))

const NAV_ITEMS = [
  { id: 'explore', label: 'Home' },
  { id: 'explore_nav', label: 'Explore' },
  { id: 'about', label: 'About' },
  { id: 'methodology', label: 'Methodology' },
  { id: 'contact', label: 'Contact' },
]

const SIDEBAR_ITEMS = [
  { id: 'explore', icon: '🏠', label: 'Explore Ocean' },
  { id: 'analysis3d', icon: '⬡', label: '3D Analysis' },
  { id: 'satellite', icon: '🛰️', label: 'Satellite Data' },
  { id: 'argo', icon: '📍', label: 'ARGO Validation' },
  { id: 'downloads', icon: '⬇️', label: 'Downloads' },
  { id: 'learn', icon: '📖', label: 'Learn' },
  { id: 'settings', icon: '⚙️', label: 'Settings' },
]

const DEMO_CASES = [
  { id: 'amphan', name: 'CASE 01 - Bay of Bengal', lat: 13.5, lon: 82.0, date: '2020-05-15', tag: 'Cyclone Pre-condition' },
  { id: 'arabian', name: 'CASE 02 - Arabian Sea', lat: 16.0, lon: 66.0, date: '2021-05-14', tag: 'MHW Extreme' },
  { id: 'equatorial', name: 'CASE 03 - Equatorial Indian Ocean', lat: 5.0, lon: 85.0, date: '2019-10-20', tag: 'IOD Positive' },
]

export default function App() {
  const [page, setPage] = useState('explore')
  const [viewMode, setViewMode] = useState('3d')
  const [coordMode, setCoordMode] = useState('map')
  const [lat, setLat] = useState(13.5)
  const [lon, setLon] = useState(82.0)
  const [date, setDate] = useState('2020-05-15')
  const [depth, setDepth] = useState(137.5)
  const [scenarioId, setScenarioId] = useState('amphan')
  const [missing, setMissing] = useState({ sst: false, sss: false, ssh: false, current_u: false, current_v: false, wind_u: false, wind_v: false })
  const [playing, setPlaying] = useState(false)
  const [seasonIdx, setSeasonIdx] = useState(1)
  const [compareNominal, setCompareNominal] = useState(false)
  const [showUnc, setShowUnc] = useState(true)
  const [health, setHealth] = useState(null)
  const [meta, setMeta] = useState(null)
  const [apiOk, setApiOk] = useState(true)
  const [profile, setProfile] = useState(null)
  const [nominal, setNominal] = useState(null)
  const [probe, setProbe] = useState(null)
  const [transect, setTransect] = useState(null)
  const [field, setField] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [argo, setArgo] = useState(null)
  const [ablations, setAblations] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const masks = useMemo(() => ({
    sst: missing.sst,
    sss: missing.sss,
    ssh: missing.ssh,
    current_u: missing.current_u,
    current_v: missing.current_v,
    wind_u: missing.wind_u,
    wind_v: missing.wind_v,
  }), [missing])

  const boot = () => {
    getHealth()
      .then((h) => { setHealth(h); setApiOk(true) })
      .catch(() => { setApiOk(false); setHealth({ status: 'offline', demo_mode: true, data_type: 'UNAVAILABLE' }) })
    getMetadata().then(setMeta).catch(() => {})
    getMetrics().then(setMetrics).catch(() => {})
    getArgoComparison().then(setArgo).catch(() => {})
    getAblations().then(setAblations).catch(() => {})
  }

  useEffect(() => { boot() }, [])

  useEffect(() => {
    let timer
    if (playing) {
      timer = setInterval(() => {
        setSeasonIdx((prev) => {
          const next = (prev + 1) % SEASONS.length
          setDate(SEASONS[next].date)
          return next
        })
      }, 2400)
    }
    return () => timer && clearInterval(timer)
  }, [playing])

  useEffect(() => {
    if (!apiOk) return
    let cancelled = false
    setLoading(true)
    setError(null)
    const body = { lat: Number(lat), lon: Number(lon), date, masks }
    Promise.all([
      postProfile(body),
      postProfile({ ...body, masks: { sst: false, sss: false, ssh: false, current_u: false, current_v: false, wind_u: false, wind_v: false } }),
    ])
      .then(([p, n]) => {
        if (cancelled) return
        setProfile(p)
        setNominal(n)
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err?.message || 'Profile request failed')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [lat, lon, date, masks, apiOk])

  useEffect(() => {
    if (!apiOk || !profile) return
    const t = setTimeout(() => {
      getPrediction({ lat: Number(lat), lon: Number(lon), date, depth })
        .then(setProbe)
        .catch(() => setProbe(null))
    }, 280)
    return () => clearTimeout(t)
  }, [lat, lon, date, depth, apiOk, profile])

  useEffect(() => {
    if (!apiOk || (page !== 'transect' && page !== 'explore')) return
    getTransect({ lat: Number(lat), date }).then(setTransect).catch(() => setTransect(null))
  }, [lat, date, page, apiOk])

  useEffect(() => {
    if (!apiOk || (page !== 'satellite' && page !== 'explore')) return
    getMap({ date, depth }).then(setField).catch(() => setField(null))
  }, [date, depth, page, apiOk])

  const thermo = profile?.thermocline || {}
  const tchp = useMemo(() => computeTchp(profile?.depths, profile?.temperatures), [profile])
  const surface = profile?.surface_inputs || {}

  const go = (id) => {
    if (id === 'explore_nav') {
      setPage('explore')
    } else {
      setPage(id)
    }
  }

  const applyDemoCase = (c) => {
    setLat(c.lat)
    setLon(c.lon)
    setDate(c.date)
    setScenarioId(c.id)
  }

  const locateGrid = () => {
    const s = snapGrid(lat, lon)
    setLat(s.lat)
    setLon(s.lon)
  }

  const exportCSV = () => {
    if (!profile) return
    const rows = [['depth_m', 'temperature_c', 'uncertainty_c', 'lat', 'lon', 'date', 'data_type']]
    profile.depths.forEach((d, i) => {
      rows.push([d, profile.temperatures[i], profile.uncertainties?.[i] ?? '', lat, lon, date, profile.data_type || ''])
    })
    downloadBlob(`oceanembed_${lat}N_${lon}E_${date}.csv`, rows.map((r) => r.join(',')).join('\n'), 'text/csv')
  }

  const exportJSON = () => {
    if (!profile) return
    downloadBlob(
      `oceanembed_${lat}N_${lon}E_${date}.json`,
      JSON.stringify({ query: { lat, lon, date, depth, masks }, profile, probe, tchp }, null, 2),
      'application/json'
    )
  }

  const sensorRow = (key, title, hint, paired) => (
    <div className={`sensor ${missing[key] ? 'dropped' : ''}`}>
      <div>
        <div className="sensor-title">{title}</div>
        <div className="muted tiny">{hint}</div>
      </div>
      <button
        className={missing[key] ? 'btn-ghost danger' : 'btn-teal'}
        onClick={() => {
          setMissing((m) => {
            const next = { ...m, [key]: !m[key] }
            if (paired) next[paired] = next[key]
            return next
          })
        }}
      >
        {missing[key] ? 'Dropped' : 'Active'}
      </button>
    </div>
  )

  return (
    <div className="app-shell">
      {/* ── TOP NAVBAR ── */}
      <header className="top-navbar">
        <div className="logo" onClick={() => go('explore')} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">
            <span style={{ fontSize: '26px', color: '#00d4ff', lineHeight: 1, letterSpacing: '-2px', fontWeight: '800' }}>≋</span>
          </div>
          <div className="logo-text">
            <h1 style={{ color: '#ffffff', fontSize: '20px', fontWeight: '800', letterSpacing: '-0.3px' }}>OceanEmbed</h1>
            <p style={{ color: '#94a3b8', fontSize: '11px', marginTop: '1px' }}>
              From Space to Subsurface | AI-driven 3D Ocean Temperature Reconstruction
            </p>
          </div>
        </div>

        <div className="nav-links">
          {NAV_ITEMS.map((n) => (
            <button
              key={n.id}
              className={`nav-link ${(page === n.id || (n.id === 'explore' && page === 'explore')) ? 'active' : ''}`}
              onClick={() => go(n.id)}
            >
              {n.label}
            </button>
          ))}
          <button
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.12)',
              color: '#94a3b8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              marginLeft: '6px'
            }}
            title="User Profile"
          >
            👤
          </button>
        </div>

        <div className="nav-right">
          <div className="system-online-badge">
            System Online
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', lineHeight: '1.25', textAlign: 'right' }}>
            <div>Deeper Insights.</div>
            <div style={{ color: '#64748b' }}>A Safer, More Resilient Ocean.</div>
          </div>
        </div>
      </header>

      {/* ── MAIN WORKSPACE ── */}
      <div className="app-layout">
        <aside className="sidebar">
          {SIDEBAR_ITEMS.map((item, idx) => {
            const isActive = page === item.id || (item.id === 'learn' && page === 'methodology')
            return (
              <div key={item.id}>
                {idx === 4 && <div className="sidebar-divider" />}
                <button
                  className={`sidebar-btn ${isActive ? 'active' : ''}`}
                  onClick={() => go(item.id === 'learn' ? 'methodology' : item.id)}
                >
                  <span className="sb-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              </div>
            )
          })}
        </aside>

        <main className="main-content" style={{ padding: '20px 24px', flex: 1, minWidth: 0 }}>
          {page === 'explore' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', alignItems: 'start' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#ffffff', letterSpacing: '-0.2px' }}>
                      Explore the North Indian Ocean
                    </h2>
                    <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '3px' }}>
                      Select a location or enter grid coordinates to view 3D temperature profile.
                    </p>
                  </div>
                  <div style={{ display: 'flex', background: '#091528', padding: '3px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <button
                      onClick={() => setViewMode('2d')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        border: 'none',
                        cursor: 'pointer',
                        background: viewMode === '2d' ? '#0084ff' : 'transparent',
                        color: viewMode === '2d' ? '#ffffff' : '#94a3b8',
                        transition: 'all 0.15s'
                      }}
                    >
                      2D View
                    </button>
                    <button
                      onClick={() => setViewMode('3d')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        border: 'none',
                        cursor: 'pointer',
                        background: viewMode === '3d' ? '#0084ff' : 'transparent',
                        color: viewMode === '3d' ? '#ffffff' : '#94a3b8',
                        transition: 'all 0.15s'
                      }}
                    >
                      3D View
                    </button>
                  </div>
                </div>

                <div
                  className="glass-card"
                  style={{
                    position: 'relative',
                    height: '420px',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    border: '1px solid rgba(255,255,255,0.08)',
                    background: '#091426'
                  }}
                >
                  <BasinMap
                    lat={lat}
                    lon={lon}
                    field={field}
                    onPick={({ lat: la, lon: lo, date: da, scenarioId: sid }) => {
                      setLat(la)
                      setLon(lo)
                      if (da) setDate(da)
                      setScenarioId(sid ?? null)
                    }}
                  />

                  <div
                    style={{
                      position: 'absolute',
                      top: '12px',
                      right: '12px',
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      background: 'rgba(8,16,30,0.85)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '10px',
                      fontWeight: '800',
                      color: '#ffffff',
                      zIndex: 400
                    }}
                  >
                    <span>▲</span>
                    <span style={{ fontSize: '9px', marginTop: '-2px' }}>N</span>
                  </div>

                  <div
                    style={{
                      position: 'absolute',
                      top: '38%',
                      left: '46%',
                      transform: 'translate(-50%, -50%)',
                      background: 'rgba(6, 13, 26, 0.88)',
                      border: '1px solid #00d4ff',
                      borderRadius: '6px',
                      padding: '4px 10px',
                      fontSize: '11px',
                      fontFamily: 'JetBrains Mono',
                      color: '#f0f6ff',
                      boxShadow: '0 4px 14px rgba(0,0,0,0.6)',
                      pointerEvents: 'none',
                      zIndex: 400,
                      textAlign: 'center'
                    }}
                  >
                    <div>Lat: {lat.toFixed(1)}° N</div>
                    <div>Lon: {lon.toFixed(1)}° E</div>
                  </div>

                  <div
                    style={{
                      position: 'absolute',
                      bottom: '12px',
                      left: '12px',
                      background: 'rgba(8, 16, 32, 0.9)',
                      border: '1px solid rgba(255,255,255,0.12)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      zIndex: 400,
                      minWidth: '220px'
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>
                      Sea Surface Temperature (°C)
                    </div>
                    <div
                      style={{
                        height: '8px',
                        borderRadius: '4px',
                        background: 'linear-gradient(90deg, #38bdf8 0%, #22c55e 33%, #f59e0b 66%, #ef4444 100%)',
                        marginBottom: '4px'
                      }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8', fontFamily: 'JetBrains Mono' }}>
                      <span>20</span>
                      <span>24</span>
                      <span>28</span>
                      <span>32</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '500' }}>Demo cases:</span>
                  {DEMO_CASES.map((c) => {
                    const isSelected = scenarioId === c.id || (lat === c.lat && lon === c.lon)
                    return (
                      <button
                        key={c.id}
                        onClick={() => applyDemoCase(c)}
                        style={{
                          padding: '6px 14px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: isSelected ? '600' : '400',
                          border: isSelected ? '1px solid #0084ff' : '1px solid rgba(255,255,255,0.08)',
                          background: isSelected ? '#0084ff' : '#0a1628',
                          color: isSelected ? '#ffffff' : '#94a3b8',
                          cursor: 'pointer',
                          transition: 'all 0.15s'
                        }}
                      >
                        {c.name}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div
                  className="glass-card"
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    background: '#091426',
                    border: '1px solid rgba(255,255,255,0.08)'
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: '700', color: '#ffffff', marginBottom: '12px' }}>
                    Grid Location
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '12px' }}>
                    <button
                      onClick={() => setCoordMode('map')}
                      style={{
                        padding: '7px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: coordMode === 'map' ? '700' : '400',
                        background: coordMode === 'map' ? '#0084ff' : 'transparent',
                        color: coordMode === 'map' ? '#ffffff' : '#94a3b8',
                        border: coordMode === 'map' ? 'none' : '1px solid rgba(255,255,255,0.08)',
                        cursor: 'pointer'
                      }}
                    >
                      Select on Map
                    </button>
                    <button
                      onClick={() => setCoordMode('manual')}
                      style={{
                        padding: '7px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: coordMode === 'manual' ? '700' : '400',
                        background: coordMode === 'manual' ? '#0084ff' : 'transparent',
                        color: coordMode === 'manual' ? '#ffffff' : '#94a3b8',
                        border: coordMode === 'manual' ? 'none' : '1px solid rgba(255,255,255,0.08)',
                        cursor: 'pointer'
                      }}
                    >
                      Enter Coordinates
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Latitude (°N)</div>
                      <input
                        type="number"
                        min="5"
                        max="30"
                        step="0.5"
                        value={lat}
                        onChange={(e) => { const c = clampCoord(e.target.value, lon); setLat(c.lat); setScenarioId(null) }}
                        style={{
                          width: '100%',
                          background: '#060d1a',
                          border: '1px solid rgba(255,255,255,0.12)',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          color: '#ffffff',
                          fontFamily: 'JetBrains Mono',
                          fontSize: '13px'
                        }}
                      />
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Longitude (°E)</div>
                      <input
                        type="number"
                        min="45"
                        max="105"
                        step="0.5"
                        value={lon}
                        onChange={(e) => { const c = clampCoord(lat, e.target.value); setLon(c.lon); setScenarioId(null) }}
                        style={{
                          width: '100%',
                          background: '#060d1a',
                          border: '1px solid rgba(255,255,255,0.12)',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          color: '#ffffff',
                          fontFamily: 'JetBrains Mono',
                          fontSize: '13px'
                        }}
                      />
                    </div>
                  </div>

                  <button
                    onClick={locateGrid}
                    style={{
                      width: '100%',
                      padding: '10px',
                      background: '#0084ff',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    <span>🌐</span> Locate Grid
                  </button>
                  <p style={{ fontSize: '10px', color: '#64748b', marginTop: '6px', textAlign: 'center' }}>
                    Snaps to the nearest deterministic demo grid.
                  </p>
                </div>

                <div
                  className="glass-card"
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    background: '#091426',
                    border: '1px solid rgba(255,255,255,0.08)'
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: '700', color: '#ffffff', marginBottom: '12px' }}>
                    Quick Stats (Selected Grid)
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
                        <span>🌡️</span> SST (°C)
                      </div>
                      <span style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                        {fmt(thermo.surface_temp_c ?? surface.sst ?? 29.4, 1)}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
                        <span>💧</span> SSS (PSU)
                      </div>
                      <span style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                        {fmt(surface.sss ?? 33.8, 1)}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
                        <span>〰️</span> Sea Level Anomaly (cm)
                      </div>
                      <span style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                        {surface.ssh !== undefined ? `+${(surface.ssh * 100).toFixed(1)}` : '+8.5'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#94a3b8' }}>
                        <span>💨</span> Wind Stress (N/m²)
                      </div>
                      <span style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff', fontFamily: 'JetBrains Mono' }}>
                        {surface.wind_speed !== undefined ? (surface.wind_speed * 0.015).toFixed(2) : '0.12'}
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  className="glass-card"
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    background: '#091426',
                    border: '1px solid rgba(255,255,255,0.08)'
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: '700', color: '#ffffff', marginBottom: '2px' }}>
                    3D Subsurface Temperature
                  </div>
                  <div style={{ fontSize: '11px', color: '#00d4ff', marginBottom: '10px' }}>
                    📍 Location: {lat.toFixed(1)}° N, {lon.toFixed(1)}° E
                  </div>
                  <SubsurfaceCube
                    profile={profile}
                    lat={lat}
                    lon={lon}
                    sst={thermo.surface_temp_c ?? surface.sst ?? 29.4}
                  />
                </div>
              </div>
            </div>
          )}

          {page === 'analysis3d' && (
            <section className="glass-card pad">
              <h2 className="section-heading">3D Thermal Volume Analysis</h2>
              <p className="section-subheading">Interactive 3D reconstruction of the API subsurface temperature profile. Rotate to inspect thermocline inversion layers.</p>
              <Suspense fallback={<div className="chart-empty">Loading WebGL 3D Volume…</div>}>
                <OceanScene profile={profile} depth={depth} className="ocean-canvas tall" />
              </Suspense>
              <div className="probe-bar" style={{ marginTop: 14 }}>
                <div className="row-between">
                  <span>Continuous Depth Probe:</span>
                  <strong className="mono">{depth.toFixed(1)} m</strong>
                </div>
                <input type="range" min="0" max="1000" step="0.5" value={depth} onChange={(e) => setDepth(Number(e.target.value))} />
              </div>
              <div className="two-col" style={{ marginTop: 16 }}>
                <article className="mini-panel">
                  <h3>Tropical Cyclone Heat Potential (TCHP)</h3>
                  <p className="huge coral">{fmt(tchp.tchp, 1)} <small>kJ/cm²</small></p>
                  <p className="muted">{tchp.category}. Integrated heat above 26°C isotherm.</p>
                </article>
                <article className="mini-panel">
                  <h3>Vertical Stratification</h3>
                  <p>Max gradient: <strong>{fmt(thermo.max_gradient_c_per_m, 4)} °C/m</strong></p>
                  <p>D20 Isotherm Depth: <strong>{fmt(thermo.d20_depth_m, 1)} m</strong></p>
                  <p>Mixed Layer Depth (MLD): <strong>{fmt(thermo.mld_m, 1)} m</strong></p>
                </article>
              </div>
            </section>
          )}

          {page === 'satellite' && (
            <section className="glass-card pad">
              <h2 className="section-heading">Satellite Observation Data & Sensor Lab</h2>
              <p className="section-subheading">Simulate sensor dropouts and test the neural network robustness against cloud-cover / missing satellite telemetry.</p>
              <div className="two-col map-lab">
                <BasinMap
                  lat={lat}
                  lon={lon}
                  field={field}
                  onPick={({ lat: la, lon: lo, date: da, scenarioId: sid }) => {
                    setLat(la)
                    setLon(lo)
                    if (da) setDate(da)
                    setScenarioId(sid ?? null)
                  }}
                />
                <div className="sensor-stack">
                  {sensorRow('sst', 'SST', 'OSTIA / Sea Surface Temperature skin')}
                  {sensorRow('sss', 'SSS', 'SMAP / Satellite Salinity')}
                  {sensorRow('ssh', 'SSH / SLA', 'DUACS Altimetry Sea Level Anomaly')}
                  {sensorRow('current_u', 'Currents U/V', 'Surface Current Vectors', 'current_v')}
                  {sensorRow('wind_u', 'Winds U/V', 'Scatterometer Wind Stress', 'wind_v')}
                </div>
              </div>
            </section>
          )}

          {page === 'argo' && (
            <section className="glass-card pad">
              <h2 className="section-heading">ARGO In-Situ CTD Matchup & Validation</h2>
              <p className="section-subheading">Independent validation against real-world INCOIS / Argo profiling float CTD data (0–2000m).</p>
              <ProfileChart
                profile={profile}
                nominal={nominal}
                argo={nearestArgo}
                depth={depth}
                showUncertainty={showUnc}
                compareNominal={compareNominal}
              />
            </section>
          )}

          {page === 'downloads' && (
            <section className="glass-card pad">
              <h2 className="section-heading">Export Ocean Temperature Data</h2>
              <p className="section-subheading">Export current vertical profile and hydrographic metadata for {lat}°N, {lon}°E on {date}.</p>
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button className="btn-primary" onClick={exportCSV} disabled={!profile}>📥 Export CSV</button>
                <button className="btn-teal" onClick={exportJSON} disabled={!profile}>📋 Export JSON</button>
              </div>
            </section>
          )}

          {page === 'methodology' && (
            <section className="glass-card pad prose">
              <h2>Scientific Methodology & Architecture</h2>
              <p><strong>OceanEmbed</strong> utilizes continuous Implicit Neural Representations (INR) parameterized by multi-modal surface satellite observations (SST, SSS, SSH, currents, wind stress) to reconstruct subsurface ocean temperature fields T(z).</p>
              <h3>Physics & Stratification Invariants</h3>
              <p>Upper-ocean thermodynamics are governed by strict stability constraints: ∂T/∂z &le; 0 (stable vertical density layering) and conservation of surface boundary conditions.</p>
              <h3>Independent Validation</h3>
              <p>Validation profiles are retrieved from independent in-situ ARGO profiling floats deployed by INCOIS across the Arabian Sea, Bay of Bengal, and Equatorial Indian Ocean.</p>
            </section>
          )}

          {page === 'about' && (
            <section className="glass-card pad prose">
              <h2>About OceanEmbed Suite</h2>
              <p>AI-driven 3D Ocean Subsurface Temperature Reconstruction Suite for the North Indian Ocean.</p>
              <p>Developed for Smart India Hackathon (SIH26066) in collaboration with the Ministry of Earth Sciences (MoES) and Indian National Centre for Ocean Information Services (INCOIS).</p>
            </section>
          )}

          {page === 'contact' && (
            <section className="glass-card pad prose">
              <h2>Contact & Support</h2>
              <p>For technical queries, operational integration, or scientific collaboration, please reach out via GitHub or the INCOIS Earth Sciences portal.</p>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}
