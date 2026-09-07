import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || ''

const http = axios.create({
  baseURL: API_BASE,
  timeout: 45000,
})

export async function getHealth() {
  const { data } = await http.get('/api/health')
  return data
}

export async function getMetadata() {
  const { data } = await http.get('/api/metadata')
  return data
}

export async function getDepths() {
  const { data } = await http.get('/api/depths')
  return data
}

export async function getDates() {
  const { data } = await http.get('/api/dates')
  return data
}

export async function postProfile({ lat, lon, date, masks }) {
  const { data } = await http.post('/api/profile', { lat, lon, date, masks })
  return data
}

export async function getPrediction({ lat, lon, date, depth }) {
  const { data } = await http.get('/api/prediction', { params: { lat, lon, date, depth } })
  return data
}

export async function getTransect({ lat, date }) {
  const { data } = await http.get('/api/transect', { params: { lat, date } })
  return data
}

export async function getMap({ date, depth, lat_step = 1, lon_step = 1.5 }) {
  const { data } = await http.get('/api/map', { params: { date, depth, lat_step, lon_step } })
  return data
}

export async function getMetrics() {
  const { data } = await http.get('/api/metrics')
  return data
}

export async function getArgoComparison(params = {}) {
  const { data } = await http.get('/api/argo-comparison', { params })
  return data
}

export async function getAblations() {
  const { data } = await http.get('/api/ablations')
  return data
}
