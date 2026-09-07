import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { PRESET_SCENARIOS } from '../../lib/ocean'

export default function BasinMap({ lat, lon, onPick, field }) {
  const el = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const heatRef = useRef(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick

  useEffect(() => {
    if (!el.current || mapRef.current) return
    const map = L.map(el.current, {
      center: [lat, lon],
      zoom: 4,
      minZoom: 3,
      maxZoom: 8,
      zoomControl: false,
    })
    L.control.zoom({ position: 'topright' }).addTo(map)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles © Esri, GEBCO, NOAA',
      maxZoom: 13,
    }).addTo(map)
    L.rectangle([[5, 45], [30, 105]], {
      color: '#00f0ff',
      weight: 1.4,
      dashArray: '5,5',
      fillColor: '#00f0ff',
      fillOpacity: 0.04,
    }).addTo(map)

    PRESET_SCENARIOS.forEach((p) => {
      const m = L.circleMarker([p.lat, p.lon], {
        radius: 6,
        color: '#10b981',
        fillColor: '#07101f',
        fillOpacity: 0.9,
        weight: 2,
      }).addTo(map)
      m.bindTooltip(`${p.name}<br/>${p.lat}°N, ${p.lon}°E`, { direction: 'top' })
      m.on('click', () => onPickRef.current({ lat: p.lat, lon: p.lon, date: p.date, scenarioId: p.id }))
    })

    const marker = L.circleMarker([lat, lon], {
      radius: 9,
      color: '#00f0ff',
      fillColor: '#00f0ff',
      fillOpacity: 0.9,
      weight: 2,
    }).addTo(map)

    map.on('click', (e) => {
      const nlat = Math.round(e.latlng.lat * 10) / 10
      const nlon = Math.round(e.latlng.lng * 10) / 10
      if (nlat >= 5 && nlat <= 30 && nlon >= 45 && nlon <= 105) {
        onPickRef.current({ lat: nlat, lon: nlon, scenarioId: null })
      }
    })

    mapRef.current = map
    markerRef.current = marker
    setTimeout(() => map.invalidateSize(), 200)
    return () => {
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
  }, [])

  useEffect(() => {
    markerRef.current?.setLatLng([lat, lon])
    mapRef.current?.panTo([lat, lon], { animate: true, duration: 0.35 })
  }, [lat, lon])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !field?.lats || !field?.temperatures) return
    if (heatRef.current) {
      heatRef.current.remove()
      heatRef.current = null
    }
    const layer = L.layerGroup()
    const temps = field.temperatures.flat()
    const tmin = Math.min(...temps)
    const tmax = Math.max(...temps)
    field.lats.forEach((la, i) => {
      field.lons.forEach((lo, j) => {
        const t = field.temperatures[i][j]
        const n = (t - tmin) / (tmax - tmin || 1)
        const color = n > 0.66 ? '#f97316' : n > 0.33 ? '#22c55e' : '#38bdf8'
        L.rectangle(
          [[la - 0.45, lo - 0.7], [la + 0.45, lo + 0.7]],
          { color, weight: 0, fillColor: color, fillOpacity: 0.18 }
        ).addTo(layer)
      })
    })
    layer.addTo(map)
    heatRef.current = layer
  }, [field])

  useEffect(() => {
    const id = setTimeout(() => mapRef.current?.invalidateSize(), 250)
    return () => clearTimeout(id)
  }, [lat, lon, field])

  return <div ref={el} className="basin-map" />
}
