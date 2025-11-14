;(function(){
  async function getJSON(url, opts={}){
    try{
      const r = await fetch(url, opts)
      if(!r.ok) {
        const errorData = await r.json().catch(() => ({}))
        const error = new Error(errorData.error || `Request failed with status ${r.status}`)
        error.status = r.status
        error.data = errorData
        throw error
      }
      return r.json()
    }catch(e){
      if(e.status) throw e // Re-throw API errors
      const err = new Error('Network unavailable')
      err.code = 'OFFLINE'
      err.originalError = e
      throw err
    }
  }
  async function geocode(q){
    try{
      return await getJSON(`/api/geocode?query=${encodeURIComponent(q)}`)
    }catch(e){
      return {results:[{name:'Sample', lat:28.6139, lon:77.2090}]}
    }
  }
  async function weather(lat,lon){
    try{
      const data = await getJSON(`/api/weather?lat=${lat}&lon=${lon}`)
      if(data.error) {
        throw new Error(data.error)
      }
      return data
    }catch(e){
      console.error('Weather API error:', e)
      // Return fallback data only for network errors, not API errors
      if(e.code === 'OFFLINE' || !e.status) {
        return {
          lat, lon,
          current: {temp:26, humidity:60, wind_speed:3.2, rain:{'1h':0}},
          daily: [
            {dt:0, temp:{day:26}, rain:5},
            {dt:1, temp:{day:27}, rain:12},
            {dt:2, temp:{day:25}, rain:8},
            {dt:3, temp:{day:24}, rain:2},
            {dt:4, temp:{day:26}, rain:15},
            {dt:5, temp:{day:28}, rain:0},
            {dt:6, temp:{day:27}, rain:10}
          ],
          climatology: {
            monthly: [
              {month:1, temp:18, rain:25},
              {month:2, temp:20, rain:30},
              {month:3, temp:24, rain:35},
              {month:4, temp:28, rain:45},
              {month:5, temp:32, rain:60},
              {month:6, temp:34, rain:80},
              {month:7, temp:33, rain:90},
              {month:8, temp:32, rain:85},
              {month:9, temp:30, rain:70},
              {month:10, temp:26, rain:50},
              {month:11, temp:22, rain:35},
              {month:12, temp:19, rain:28}
            ]
          }
        }
      }
      throw e
    }
  }
  async function soil(lat,lon){
    try{
      const data = await getJSON(`/api/soil?lat=${lat}&lon=${lon}`)
      if(data.error) {
        throw new Error(data.error)
      }
      return data
    }catch(e){
      console.error('Soil API error:', e)
      // Return fallback data only for network errors, not API errors
      if(e.code === 'OFFLINE' || !e.status) {
        return {lat, lon, ph:6.4, soc_pct:1.2, texture:'clay loam', sand_pct:45, silt_pct:30, clay_pct:25}
      }
      throw e
    }
  }
  async function recommend(lat,lon){
    return getJSON(`/api/recommend`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lon})})
  }
  async function calendar(lat,lon){
    return getJSON(`/api/calendar?lat=${lat}&lon=${lon}`)
  }
  async function getCrops(){
    return getJSON(`/api/crops`)
  }
  async function exportCSV(recs, fields){
    const body = {recs, fields}
    const r = await fetch('/api/export/csv', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    if(!r.ok) throw new Error('Export failed')
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'crop_recommendations.csv'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }
  window.App = {geocode, weather, soil, recommend, calendar, getCrops, exportCSV}
})();
