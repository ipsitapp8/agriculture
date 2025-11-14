const {calendar} = window.App

const latEl = document.getElementById('cal-lat')
const lonEl = document.getElementById('cal-lon')
const currentGrid = document.getElementById('month-grid')
const climatologyGrid = document.getElementById('climatology-grid')
const viewCurrentBtn = document.getElementById('view-current')
const viewClimatologyBtn = document.getElementById('view-climatology')
const currentViewPanel = document.getElementById('current-view')
const climatologyViewPanel = document.getElementById('climatology-view')

let currentData = null

function renderMonth(m, showDetails = false){
  const d = document.createElement('div')
  d.className = `month ${m.status}`
  
  const statusIcon = {
    'green': '<i class="fas fa-check-circle" style="color: var(--success); font-size: 1.5rem; margin-bottom: 0.5rem;"></i>',
    'yellow': '<i class="fas fa-exclamation-circle" style="color: var(--warning); font-size: 1.5rem; margin-bottom: 0.5rem;"></i>',
    'red': '<i class="fas fa-times-circle" style="color: var(--danger); font-size: 1.5rem; margin-bottom: 0.5rem;"></i>'
  }[m.status] || '<i class="fas fa-question-circle" style="color: var(--text-secondary); font-size: 1.5rem; margin-bottom: 0.5rem;"></i>'
  
  let content = `
    ${statusIcon}
    <strong style="display: block; font-size: 1.25rem; margin-bottom: 0.5rem;">${m.month}</strong>
    <span style="display: block; color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.75rem;">${m.note}</span>
  `
  
  if (showDetails && (m.temp !== undefined || m.rain !== undefined)) {
    content += `<div class="month-details">`
    if (m.temp !== undefined) {
      content += `<span><i class="fas fa-thermometer-half" style="margin-right: 0.5rem;"></i>Temp: ${m.temp}°C</span>`
    }
    if (m.rain !== undefined) {
      content += `<span><i class="fas fa-cloud-rain" style="margin-right: 0.5rem;"></i>Rain: ${m.rain}mm</span>`
    }
    content += `</div>`
  }
  
  d.innerHTML = content
  if (m.planting_ok) {
    d.style.borderLeft = "4px solid var(--success)"
  }
  return d
}

function switchView(view) {
  if (view === 'current') {
    viewCurrentBtn.classList.add('active')
    viewClimatologyBtn.classList.remove('active')
    currentViewPanel.style.display = 'block'
    climatologyViewPanel.style.display = 'none'
  } else {
    viewCurrentBtn.classList.remove('active')
    viewClimatologyBtn.classList.add('active')
    currentViewPanel.style.display = 'none'
    climatologyViewPanel.style.display = 'block'
  }
}

async function run(){
  const lat = parseFloat(latEl.value || '28.6139')
  const lon = parseFloat(lonEl.value || '77.2090')
  currentData = await calendar(lat,lon)
  
  // Render current conditions
  currentGrid.innerHTML = ''
  if (currentData.months) {
    currentData.months.forEach(m=>{ 
      currentGrid.appendChild(renderMonth(m, false)) 
    })
  } else {
    currentGrid.innerHTML = '<div class="no-data">No current conditions data available</div>'
  }
  
  // Render climatology data
  climatologyGrid.innerHTML = ''
  if (currentData.climatology_months) {
    currentData.climatology_months.forEach(m=>{ 
      climatologyGrid.appendChild(renderMonth(m, true)) 
    })
  } else {
    climatologyGrid.innerHTML = '<div class="no-data">No climatology data available</div>'
  }
}

viewCurrentBtn.addEventListener('click', () => switchView('current'))
viewClimatologyBtn.addEventListener('click', () => switchView('climatology'))
document.getElementById('cal-run').addEventListener('click', run)
run()
