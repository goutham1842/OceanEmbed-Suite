import { useMemo, useState } from 'react'
import { oceanTempColor } from '../../lib/ocean'

export default function TransectHeatmap({ transect, lon, maxDepth = 1000 }) {
  const [hover, setHover] = useState(null)
  const model = useMemo(() => {
    if (!transect?.longitudes || !transect?.depths || !transect?.temperatures_2d) return null
    return transect
  }, [transect])

  if (!model) return <div className="chart-empty">Loading basin transect from API…</div>

  const nLon = model.longitudes.length
  const nDep = model.depths.length
  const depthMax = Math.max(...model.depths, maxDepth)

  return (
    <div className="chart-wrap">
      <svg
        viewBox="0 0 760 340"
        className="chart-svg"
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect()
          const nx = Math.max(0, Math.min(1, (e.clientX - rect.left - 55) / (rect.width - 70)))
          const ny = Math.max(0, Math.min(1, (e.clientY - rect.top - 15) / (rect.height - 35)))
          const lonV = 45 + nx * 60
          const z = ny * depthMax
          let nearestI = 0
          let nearestJ = 0
          let bestLon = 1e9
          let bestZ = 1e9
          model.longitudes.forEach((l, i) => {
            if (Math.abs(l - lonV) < bestLon) { bestLon = Math.abs(l - lonV); nearestI = i }
          })
          model.depths.forEach((d, j) => {
            if (Math.abs(d - z) < bestZ) { bestZ = Math.abs(d - z); nearestJ = j }
          })
          const temp = model.temperatures_2d[nearestI]?.[nearestJ]
          setHover({
            lon: Math.round(lonV * 10) / 10,
            depth: Math.round(z),
            temp,
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          })
        }}
        onMouseLeave={() => setHover(null)}
      >
        {(() => {
          const cellW = (760 - 70) / Math.max(1, nLon - 1)
          const cellH = (340 - 35) / Math.max(1, nDep - 1)
          const cells = []
          for (let j = 0; j < nDep - 1; j++) {
            for (let i = 0; i < nLon - 1; i++) {
              const temp = model.temperatures_2d[i][j]
              cells.push(
                <rect
                  key={`${i}-${j}`}
                  x={55 + i * cellW}
                  y={15 + j * cellH}
                  width={cellW + 0.6}
                  height={cellH + 0.6}
                  fill={oceanTempColor(temp)}
                />
              )
            }
          }
          return cells
        })()}
        {model.d20_depths && (
          <path
            d={`M ${model.longitudes.map((l, i) => {
              const x = 55 + ((l - 45) / 60) * (745 - 55)
              const y = 15 + (model.d20_depths[i] / depthMax) * (340 - 35)
              return `${x},${y}`
            }).join(' L ')}`}
            fill="none"
            stroke="#fff"
            strokeWidth="2.2"
            strokeDasharray="6 4"
          />
        )}
        {(() => {
          const buoyX = 55 + ((Math.max(45, Math.min(105, lon)) - 45) / 60) * (745 - 55)
          return <line x1={buoyX} y1={15} x2={buoyX} y2={320} stroke="#00f0ff" strokeWidth="2.2" />
        })()}
        {[0, 200, 400, 600, 800, 1000].filter((d) => d <= depthMax).map((d) => {
          const y = 15 + (d / depthMax) * (340 - 35)
          return (
            <g key={d}>
              <text x={48} y={y + 4} className="axis-label" textAnchor="end">{d}m</text>
            </g>
          )
        })}
      </svg>
      <div className="transect-axis">
        <span>45°E Somali</span>
        <span>75°E</span>
        <span>88°E BoB</span>
        <span>105°E Andaman</span>
      </div>
      {hover && (
        <div className="chart-tip">
          <div>{hover.lon}°E · {hover.depth} m</div>
          <div>{hover.temp != null ? `${Number(hover.temp).toFixed(2)} °C` : '—'}</div>
        </div>
      )}
    </div>
  )
}
