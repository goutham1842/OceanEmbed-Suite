import { useState, useRef, useEffect } from 'react'

export default function SubsurfaceCube({ profile, lat, lon, sst = 29.4 }) {
  const [rotation, setRotation] = useState({ x: 22, y: -35 })
  const [isDragging, setIsDragging] = useState(false)
  const dragStart = useRef({ x: 0, y: 0 })
  const initialRotation = useRef({ x: 22, y: -35 })

  const handleMouseDown = (e) => {
    setIsDragging(true)
    dragStart.current = { x: e.clientX, y: e.clientY }
    initialRotation.current = { ...rotation }
  }

  const handleMouseMove = (e) => {
    if (!isDragging) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    setRotation({
      x: Math.max(5, Math.min(60, initialRotation.current.x - dy * 0.4)),
      y: initialRotation.current.y + dx * 0.4
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  const resetView = () => {
    setRotation({ x: 22, y: -35 })
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '220px', userSelect: 'none' }}>
      {/* Reset view button */}
      <button
        onClick={resetView}
        style={{
          position: 'absolute',
          top: '0px',
          right: '0px',
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.12)',
          color: '#94a3b8',
          fontSize: '11px',
          padding: '3px 8px',
          borderRadius: '4px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          zIndex: 10
        }}
      >
        <span>↺</span> Reset view
      </button>

      {/* Surface depth label */}
      <div style={{ position: 'absolute', left: '10px', top: '35px', fontSize: '11px', color: '#94a3b8', lineHeight: '1.2', zIndex: 10 }}>
        <div>0 m</div>
        <div style={{ fontSize: '10px', color: '#64748b' }}>(Surface)</div>
      </div>

      {/* Right temperature scale */}
      <div style={{ position: 'absolute', right: '10px', top: '30px', bottom: '20px', width: '32px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', zIndex: 10 }}>
        <div style={{ fontSize: '9px', color: '#64748b', marginBottom: '2px', textAlign: 'right' }}>Temp (°C)</div>
        <div style={{ fontSize: '10px', color: '#ef4444', fontWeight: '600' }}>30</div>
        <div style={{ flex: 1, width: '4px', margin: '4px 4px', borderRadius: '2px', background: 'linear-gradient(180deg, #ef4444 0%, #f97316 25%, #eab308 50%, #10b981 75%, #3b82f6 100%)' }} />
        <div style={{ fontSize: '10px', color: '#3b82f6', fontWeight: '600' }}>15</div>
      </div>

      {/* 3D Interactive Isometric Cube Container */}
      <div
        onMouseDown={handleMouseDown}
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: isDragging ? 'grabbing' : 'grab',
          perspective: '600px',
        }}
      >
        <div
          style={{
            width: '140px',
            height: '110px',
            position: 'relative',
            transformStyle: 'preserve-3d',
            transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
            transition: isDragging ? 'none' : 'transform 0.3s ease-out'
          }}
        >
          {/* Top Face: Sea Surface */}
          <div
            style={{
              position: 'absolute',
              width: '140px',
              height: '140px',
              top: '0',
              left: '0',
              transform: 'rotateX(90deg) translateZ(0px)',
              background: 'linear-gradient(135deg, #ea580c 0%, #ef4444 50%, #f97316 100%)',
              border: '1px solid rgba(255,255,255,0.3)',
              boxShadow: 'inset 0 0 15px rgba(0,0,0,0.3)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gridTemplateRows: 'repeat(3, 1fr)',
            }}
          >
            {[...Array(9)].map((_, i) => (
              <div key={i} style={{ border: '0.5px solid rgba(255,255,255,0.2)' }} />
            ))}
          </div>

          {/* Front Face: Depth Stratification Gradient */}
          <div
            style={{
              position: 'absolute',
              width: '140px',
              height: '110px',
              top: '0',
              left: '0',
              transform: 'translateZ(70px)',
              background: 'linear-gradient(180deg, #ef4444 0%, #f97316 20%, #eab308 40%, #10b981 65%, #0284c7 85%, #1e40af 100%)',
              border: '1px solid rgba(255,255,255,0.2)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gridTemplateRows: 'repeat(5, 1fr)',
            }}
          >
            {[...Array(15)].map((_, i) => (
              <div key={i} style={{ border: '0.5px solid rgba(255,255,255,0.1)' }} />
            ))}
          </div>

          {/* Right Face: Lateral Thermal Slice */}
          <div
            style={{
              position: 'absolute',
              width: '140px',
              height: '110px',
              top: '0',
              left: '0',
              transform: 'rotateY(90deg) translateZ(70px)',
              background: 'linear-gradient(180deg, #dc2626 0%, #ea580c 20%, #ca8a04 40%, #059669 65%, #0369a1 85%, #1e3a8a 100%)',
              border: '1px solid rgba(255,255,255,0.2)',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gridTemplateRows: 'repeat(5, 1fr)',
            }}
          >
            {[...Array(15)].map((_, i) => (
              <div key={i} style={{ border: '0.5px solid rgba(255,255,255,0.1)' }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
