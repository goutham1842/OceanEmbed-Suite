import { Canvas, useFrame } from '@react-three/fiber'
import { Float, OrbitControls, Stars } from '@react-three/drei'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'
import { oceanTempHex } from '../../lib/ocean'

function ThermalColumn({ profile, depth, maxDepth }) {
  const group = useRef()
  const points = useMemo(() => {
    if (!profile?.depths) return []
    return profile.depths.map((d, i) => ({
      y: 2.4 - (d / maxDepth) * 4.8,
      temp: profile.temperatures[i],
      color: oceanTempHex(profile.temperatures[i]),
    }))
  }, [profile, maxDepth])

  useFrame((_, dt) => {
    if (group.current) group.current.rotation.y += dt * 0.15
  })

  const probeY = 2.4 - (depth / maxDepth) * 4.8
  const probeTemp = points.length
    ? points.reduce((best, p) => (Math.abs(p.y - probeY) < Math.abs(best.y - probeY) ? p : best), points[0]).temp
    : 20

  return (
    <group ref={group}>
      {points.map((p, i) => (
        <mesh key={i} position={[0, p.y, 0]}>
          <sphereGeometry args={[0.09 + (p.temp / 80), 16, 16]} />
          <meshStandardMaterial
            color={p.color}
            emissive={p.color}
            emissiveIntensity={0.45}
            roughness={0.25}
            metalness={0.2}
          />
        </mesh>
      ))}
      <mesh position={[0, probeY, 0]}>
        <torusGeometry args={[0.42, 0.025, 12, 64]} />
        <meshStandardMaterial color="#f59e0b" emissive="#f59e0b" emissiveIntensity={0.9} />
      </mesh>
      <mesh position={[0, probeY, 0]}>
        <sphereGeometry args={[0.14, 20, 20]} />
        <meshStandardMaterial color={oceanTempHex(probeTemp)} emissive="#ffffff" emissiveIntensity={0.25} />
      </mesh>
    </group>
  )
}

function BasinShell() {
  const mesh = useRef()
  useFrame((_, dt) => {
    if (mesh.current) mesh.current.rotation.y += dt * 0.04
  })
  return (
    <mesh ref={mesh} rotation={[0.35, 0.4, 0]}>
      <torusGeometry args={[2.9, 0.08, 16, 128]} />
      <meshStandardMaterial color="#00d4ff" emissive="#0ea5e9" emissiveIntensity={0.55} transparent opacity={0.55} />
    </mesh>
  )
}

function CausticsPlane() {
  const mat = useRef()
  useFrame(({ clock }) => {
    if (mat.current) mat.current.opacity = 0.12 + Math.sin(clock.elapsedTime * 0.8) * 0.04
  })
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.6, 0]}>
      <circleGeometry args={[4.2, 64]} />
      <meshStandardMaterial ref={mat} color="#083344" transparent opacity={0.14} />
    </mesh>
  )
}

function Particles() {
  const ref = useRef()
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry()
    const n = 420
    const pos = new Float32Array(n * 3)
    for (let i = 0; i < n; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 8
      pos[i * 3 + 1] = (Math.random() - 0.5) * 6
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8
    }
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    return g
  }, [])
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.03
  })
  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial color="#7dd3fc" size={0.025} transparent opacity={0.55} />
    </points>
  )
}

export default function OceanScene({ profile, depth, maxDepth = 1000, className }) {
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  return (
    <div className={className || 'ocean-canvas'}>
      <Canvas camera={{ position: [0, 1.2, 7.2], fov: 42 }} dpr={[1, 1.75]} gl={{ antialias: true, alpha: true }}>
        <color attach="background" args={['#030914']} />
        <fog attach="fog" args={['#030914', 8, 16]} />
        <ambientLight intensity={0.45} />
        <pointLight position={[4, 6, 4]} intensity={1.4} color="#67e8f9" />
        <pointLight position={[-5, -2, -3]} intensity={0.7} color="#1d4ed8" />
        <Stars radius={40} depth={30} count={reduced ? 200 : 900} factor={2.4} fade speed={reduced ? 0 : 0.6} />
        <Float speed={reduced ? 0 : 1.4} rotationIntensity={0.15} floatIntensity={0.4}>
          <BasinShell />
          <ThermalColumn profile={profile} depth={depth} maxDepth={maxDepth} />
        </Float>
        <CausticsPlane />
        {!reduced && <Particles />}
        <OrbitControls enablePan={false} minDistance={5} maxDistance={11} autoRotate={!reduced} autoRotateSpeed={0.6} />
      </Canvas>
    </div>
  )
}
