// Wait for App API to be available
function waitForApp() {
  return new Promise((resolve) => {
    if (window.App) {
      resolve(window.App)
    } else {
      const checkInterval = setInterval(() => {
        if (window.App) {
          clearInterval(checkInterval)
          resolve(window.App)
        }
      }, 50)
      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve(null)
      }, 5000)
    }
  })
}

let App = null
let loc = {lat:28.6139, lon:77.2090}
let coordSpan = null
let statusSpan = null
let input = null
let debounceTimer = null

async function init() {
  App = await waitForApp()
  if (!App) {
    console.error('App API not available')
    return
  }
  
  coordSpan = document.getElementById('coord')
  statusSpan = document.getElementById('status')
  input = document.getElementById('location-input')
  
  if (!coordSpan || !statusSpan || !input) {
    console.error('Required DOM elements not found')
    return
  }
  
  setupEventListeners()
  coordSpan.textContent = `${loc.lat}, ${loc.lon}`
  loadAll()
}

function setupEventListeners() {
  const searchBtn = document.getElementById('search-btn')
  if (searchBtn) {
    searchBtn.addEventListener('click', handleSearch)
  }
  if (input) {
    input.addEventListener('input', ()=>{
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(handleSearch, 400)
    })
  }
}

async function handleSearch(){
  if (!App || !App.geocode) {
    if(statusSpan) statusSpan.textContent = 'App not initialized'
    return
  }
  try{
    const q = input.value.trim()
    if(!q) return
    const g = await App.geocode(q)
    const first = g.results && g.results[0]
    if(first){
      loc = {lat:first.lat, lon:first.lon}
      if(coordSpan) coordSpan.textContent = `${loc.lat.toFixed(4)}, ${loc.lon.toFixed(4)}`
      await loadAll()
    } else {
      if(statusSpan) statusSpan.textContent = 'No results found'
    }
  }catch(e){
    console.error('Search error:', e)
    if(statusSpan) statusSpan.textContent = 'Search failed: ' + (e.message || 'Unknown error')
  }
}

let rainChart, tempChart, phChart, socChart

function drawCharts(w,s){
  if (typeof Chart === 'undefined') {
    if(statusSpan) statusSpan.textContent = 'Charts unavailable (offline)'
    return
  }
  if(!w || !w.daily || !Array.isArray(w.daily) || w.daily.length === 0) {
    console.error('Invalid weather data for charts:', w)
    return
  }
  if(!s || s.ph === undefined) {
    console.error('Invalid soil data for charts:', s)
    return
  }
  const labels = w.daily.map((_,i)=>`Day ${i+1}`)
  const rain = w.daily.map(d=>typeof d.rain==='number'?d.rain:(d.rain && typeof d.rain==='object'?d.rain['1h']||0:0))
  const temps = w.daily.map(d=>{
    if(d.temp && typeof d.temp==='object') {
      return d.temp.day || d.temp.min || 0
    }
    return typeof d.temp==='number'?d.temp:0
  })
  rainChart && rainChart.destroy()
  tempChart && tempChart.destroy()
  phChart && phChart.destroy()
  socChart && socChart.destroy()
  
  const primaryColor = '#3b82f6'
  const secondaryColor = '#10b981'
  const accentColor = '#f59e0b'
  const bgColor = '#f1f5f9'
  
  rainChart = new Chart(document.getElementById('rainChart'),{
    type:'line',
    data:{
      labels,
      datasets:[{
        label:'Rainfall (mm)',
        data:rain,
        borderColor: primaryColor,
        backgroundColor: `${primaryColor}20`,
        tension:0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options:{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: bgColor }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  })
  
  tempChart = new Chart(document.getElementById('tempChart'),{
    type:'line',
    data:{
      labels,
      datasets:[{
        label:'Temperature (°C)',
        data:temps,
        borderColor: accentColor,
        backgroundColor: `${accentColor}20`,
        tension:0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options:{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: bgColor }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  })
  
  phChart = new Chart(document.getElementById('phChart'),{
    type:'doughnut',
    data:{
      labels:['pH Level',''],
      datasets:[{
        data:[s.ph,7.5-s.ph],
        backgroundColor:[secondaryColor, bgColor],
        borderWidth: 0
      }]
    },
    options:{
      responsive: true,
      maintainAspectRatio: false,
      plugins:{
        legend:{display:false},
        tooltip: {
          callbacks: {
            label: function(context) {
              if (context.dataIndex === 0) {
                return `pH: ${s.ph.toFixed(2)}`
              }
              return ''
            }
          }
        }
      }
    }
  })
  
  socChart = new Chart(document.getElementById('socChart'),{
    type:'bar',
    data:{
      labels:['Organic Carbon'],
      datasets:[{
        label:'SOC (%)',
        data:[s.soc_pct],
        backgroundColor: secondaryColor,
        borderRadius: 8
      }]
    },
    options:{
      responsive: true,
      maintainAspectRatio: false,
      indexAxis:'y',
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 10,
          grid: { color: bgColor }
        },
        y: {
          grid: { display: false }
        }
      }
    }
  })
}

function setMetrics(w,s){
  const wm = document.getElementById('weather-metrics')
  if(!wm) {
    console.error('weather-metrics element not found')
    return
  }
  if(!w || !w.current) {
    wm.innerHTML = '<div style="color: var(--danger);">No weather data available</div>'
    return
  }
  wm.innerHTML = `
    <div>
      <strong>${Number(w.current.temp || 0).toFixed(1)}</strong>
      <span><i class="fas fa-thermometer-half"></i> Temperature (°C)</span>
    </div>
    <div>
      <strong>${Number(w.current.humidity || 0)}</strong>
      <span><i class="fas fa-tint"></i> Humidity (%)</span>
    </div>
    <div>
      <strong>${Number(w.current.wind_speed || 0).toFixed(1)}</strong>
      <span><i class="fas fa-wind"></i> Wind (m/s)</span>
    </div>
  `
  const sm = document.getElementById('soil-metrics')
  if(!sm) {
    console.error('soil-metrics element not found')
    return
  }
  if(!s || s.ph === undefined) {
    sm.innerHTML = '<div style="color: var(--danger);">No soil data available</div>'
    return
  }
  sm.innerHTML = `
    <div>
      <strong>${Number(s.ph || 0).toFixed(2)}</strong>
      <span><i class="fas fa-flask"></i> pH Level</span>
    </div>
    <div>
      <strong>${Number(s.soc_pct || 0).toFixed(2)}</strong>
      <span><i class="fas fa-leaf"></i> Organic Carbon (%)</span>
    </div>
    <div>
      <strong>${s.texture || 'N/A'}</strong>
      <span><i class="fas fa-mountain"></i> Texture</span>
    </div>
  `
}

const clientCache = {}
async function loadAll(){
  if (!App || !App.weather || !App.soil) {
    console.error('App API functions not available')
    if(statusSpan) statusSpan.textContent = 'App not initialized'
    return
  }
  try {
    if(statusSpan) statusSpan.textContent = 'Loading…'
    const key = `${loc.lat.toFixed(3)},${loc.lon.toFixed(3)}`
    let w = clientCache[`w:${key}`]
    let s = clientCache[`s:${key}`]
    if(!w) { 
      w = await App.weather(loc.lat,loc.lon)
      if(w && w.current) {
        clientCache[`w:${key}`] = w
      } else {
        throw new Error('Invalid weather data received')
      }
    }
    if(!s) { 
      s = await App.soil(loc.lat,loc.lon)
      if(s && s.ph !== undefined) {
        clientCache[`s:${key}`] = s
      } else {
        throw new Error('Invalid soil data received')
      }
    }
    if(w && s) {
      setMetrics(w,s)
      drawCharts(w,s)
      if(statusSpan) statusSpan.textContent = ''
    } else {
      throw new Error('Failed to load data')
    }
  } catch(e) {
    console.error('Error loading data:', e)
    if(statusSpan) statusSpan.textContent = 'Error loading data: ' + (e.message || 'Unknown error')
    // Show error in metrics
    const wm = document.getElementById('weather-metrics')
    const sm = document.getElementById('soil-metrics')
    if(wm) wm.innerHTML = '<div style="color: var(--danger); padding: 1rem;">Error loading weather data: ' + (e.message || 'Unknown error') + '</div>'
    if(sm) sm.innerHTML = '<div style="color: var(--danger); padding: 1rem;">Error loading soil data: ' + (e.message || 'Unknown error') + '</div>'
  }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init)
} else {
  init()
}
