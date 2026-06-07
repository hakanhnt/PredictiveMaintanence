// Configuration
const API_BASE = "/api";
let currentUnitData = null;
let currentCycleIndex = 0; // 0-indexed index in currentUnitData.records
let chartInstance = null;
let playInterval = null;

// Sensor metadata for Turkish localized display
const SENSOR_METADATA = {
    "S2": { name: "Kompresör Giriş Sıcaklığı", unit: "°R", min: 640, max: 645 },
    "S3": { name: "Kompresör Çıkış Sıcaklığı", unit: "°R", min: 1580, max: 1610 },
    "S4": { name: "LPT Giriş Sıcaklığı", unit: "°R", min: 1390, max: 1440 },
    "S7": { name: "HPT Çıkış Basıncı", unit: "psia", min: 549, max: 556 },
    "S8": { name: "Fiziksel Fan Hızı", unit: "rpm", min: 2387.9, max: 2388.3 },
    "S9": { name: "Düzeltilmiş Fan Hızı", unit: "rpm", min: 9020, max: 9100 },
    "S11": { name: "HPT Çıkış Sıcaklığı", unit: "°R", min: 46.9, max: 48.6 },
    "S12": { name: "LPT Hızı", unit: "rpm", min: 518, max: 523 },
    "S13": { name: "Yakıt Akış Oranı", unit: "pps", min: 2387.9, max: 2388.3 },
    "S14": { name: "Düzeltilmiş Fan Hızı 2", unit: "rpm", min: 8110, max: 8170 },
    "S15": { name: "Bypass Oranı", unit: "ratio", min: 8.3, max: 8.6 },
    "S17": { name: "Motor Şaft Hızı", unit: "rpm", min: 389, max: 399 },
    "S20": { name: "HPT Soğutma Havası Akışı", unit: "pps", min: 38.1, max: 39.5 },
    "S21": { name: "LPT Soğutma Havası Akışı", unit: "pps", min: 22.8, max: 23.6 }
};

// DOM Elements
const unitSelect = document.getElementById("unit-select");
const playbackControls = document.getElementById("playback-controls");
const cycleSlider = document.getElementById("cycle-slider");
const currentCycleVal = document.getElementById("current-cycle-val");
const totalCyclesVal = document.getElementById("total-cycles-val");
const engineStatusText = document.getElementById("engine-status-text");
const predRulVal = document.getElementById("pred-rul-val");
const actualRulVal = document.getElementById("actual-rul-val");
const rulProgressFill = document.getElementById("rul-progress-fill");
const maintenanceAlert = document.getElementById("maintenance-alert");
const sensorGrid = document.getElementById("sensor-grid");
const unitSummary = document.getElementById("unit-summary");
const btnPlay = document.getElementById("btn-play");
const btnPause = document.getElementById("btn-pause");

// Initialize Application
window.addEventListener("DOMContentLoaded", () => {
    fetchUnits();
    setupEventListeners();
});

// Fetch all unit IDs
async function fetchUnits() {
    try {
        const response = await fetch(`${API_BASE}/units`);
        if (!response.ok) throw new Error("Units fetch failed");
        const data = await response.json();
        
        // Clear placeholder
        unitSelect.innerHTML = '<option value="" disabled selected>Motor seçin...</option>';
        
        data.units.forEach(unit => {
            const option = document.createElement("option");
            option.value = unit;
            option.textContent = `Motor #${unit}`;
            unitSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error fetching unit list:", error);
        unitSelect.innerHTML = '<option value="" disabled>Yükleme Hatası</option>';
    }
}

function setupEventListeners() {
    unitSelect.addEventListener("change", (e) => {
        const unitId = e.target.value;
        if (unitId) {
            loadUnitData(unitId);
        }
    });

    cycleSlider.addEventListener("input", (e) => {
        const cycle = parseInt(e.target.value);
        setCycle(cycle - 1);
    });

    btnPlay.addEventListener("click", playTelemetry);
    btnPause.addEventListener("click", pauseTelemetry);

    // Info panel toggle
    const infoToggle = document.getElementById("info-toggle");
    const infoContent = document.getElementById("info-content");
    if (infoToggle && infoContent) {
        infoToggle.addEventListener("click", () => {
            if (infoContent.style.display === "none") {
                infoContent.style.display = "block";
                infoToggle.textContent = "Bilgiyi Gizle";
            } else {
                infoContent.style.display = "none";
                infoToggle.textContent = "Proje Bilgisi & Metodoloji";
            }
        });
    }
}

// Fetch details of selected engine unit
async function loadUnitData(unitId) {
    pauseTelemetry();
    try {
        const response = await fetch(`${API_BASE}/unit/${unitId}`);
        if (!response.ok) throw new Error("Unit details fetch failed");
        currentUnitData = await response.json();
        
        const total = currentUnitData.total_cycles;
        
        // Setup slider
        cycleSlider.min = 1;
        cycleSlider.max = total;
        cycleSlider.value = 1;
        
        // Update stats
        totalCyclesVal.textContent = total;
        
        // Show controls
        playbackControls.style.display = "block";
        unitSummary.style.display = "block";
        
        // Render Chart
        renderRulChart();
        
        // Default to cycle 1 (0-indexed 0)
        setCycle(0);
    } catch (error) {
        console.error("Error loading unit details:", error);
    }
}

// Set current display cycle
function setCycle(index) {
    if (!currentUnitData || index < 0 || index >= currentUnitData.records.length) return;
    
    currentCycleIndex = index;
    const record = currentUnitData.records[index];
    
    // Update inputs
    cycleSlider.value = index + 1;
    currentCycleVal.textContent = index + 1;
    
    // RUL values
    const predRul = Math.round(record.predicted_rul);
    const actualRul = record.actual_rul;
    
    predRulVal.textContent = predRul >= 0 ? predRul : 0;
    actualRulVal.textContent = actualRul;
    
    // Calculate progress (C-MAPSS typically starts around 200 cycles of RUL)
    const maxRul = 200;
    const pct = Math.min(100, Math.max(0, (predRul / maxRul) * 100));
    rulProgressFill.style.width = `${pct}%`;
    
    // Change color of progress bar based on status
    if (predRul <= 20) {
        rulProgressFill.style.background = "var(--accent-red)";
        maintenanceAlert.style.display = "flex";
        engineStatusText.textContent = "Kritik (Acil Bakım)";
        engineStatusText.className = "critical";
    } else if (predRul <= 50) {
        rulProgressFill.style.background = "var(--accent-orange)";
        maintenanceAlert.style.display = "none";
        engineStatusText.textContent = "Uyarı (Bakım Yaklaşıyor)";
        engineStatusText.className = "warning";
    } else {
        rulProgressFill.style.background = "linear-gradient(90deg, var(--accent-red) 0%, var(--accent-orange) 30%, var(--accent-green) 100%)";
        maintenanceAlert.style.display = "none";
        engineStatusText.textContent = "Sağlıklı (Aktif)";
        engineStatusText.className = "healthy";
    }
    
    // Draw telemetry grid
    renderSensorTelemetry(record.sensors);
    
    // Update vertical line in Chart.js
    if (chartInstance) {
        chartInstance.update('none'); // Update without full layout animation
    }
}

function renderSensorTelemetry(sensors) {
    sensorGrid.innerHTML = "";
    
    Object.entries(sensors).forEach(([key, val]) => {
        const meta = SENSOR_METADATA[key] || { name: key, unit: "", min: 0, max: val };
        
        // Calculate progress ratio for spark line
        const range = meta.max - meta.min;
        const ratio = range > 0 ? ((val - meta.min) / range) * 100 : 50;
        const pct = Math.min(100, Math.max(0, ratio));
        
        const card = document.createElement("div");
        card.className = "sensor-item-card";
        card.innerHTML = `
            <div class="sensor-meta">
                <span class="sensor-name">${key}</span>
                <span class="sensor-unit">${meta.unit}</span>
            </div>
            <div class="sensor-desc" style="font-size: 0.75rem; color: var(--text-secondary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                ${meta.name}
            </div>
            <div class="sensor-value-row">
                <span class="sensor-val">${val.toFixed(2)}</span>
            </div>
            <div class="sensor-spark-bar">
                <div class="sensor-spark-fill" style="width: ${pct}%;"></div>
            </div>
        `;
        sensorGrid.appendChild(card);
    });
}

// Chart.js render function
function renderRulChart() {
    if (!currentUnitData) return;
    
    const ctx = document.getElementById("rulChart").getContext("2d");
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const labels = currentUnitData.records.map(r => r.cycle);
    const predictedData = currentUnitData.records.map(r => r.predicted_rul);
    const actualData = currentUnitData.records.map(r => r.actual_rul);
    
    // Vertical line drawing plugin
    const verticalLinePlugin = {
        id: 'verticalLine',
        afterDraw: (chart) => {
            if (currentCycleIndex !== null && chart.scales.x) {
                const ctx = chart.ctx;
                const xVal = chart.scales.x.getPixelForValue(currentCycleIndex + 1);
                const topY = chart.scales.y.getPixelForValue(chart.scales.y.max || 200);
                const bottomY = chart.scales.y.getPixelForValue(chart.scales.y.min || 0);
                
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(xVal, topY);
                ctx.lineTo(xVal, bottomY);
                ctx.lineWidth = 2;
                ctx.strokeStyle = '#38bdf8';
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.restore();
            }
        }
    };

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Tahmin Edilen RUL',
                    data: predictedData,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    fill: false,
                    borderWidth: 2.5,
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Gerçek RUL',
                    data: actualData,
                    borderColor: '#94a3b8',
                    borderDash: [5, 5],
                    fill: false,
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#f8fafc',
                        font: {
                            family: 'Outfit'
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Döngü Sayısı (Cycle)',
                        color: '#94a3b8'
                    },
                    ticks: {
                        color: '#94a3b8',
                        stepSize: 20
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Kalan Ömür (RUL)',
                        color: '#94a3b8'
                    },
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                }
            }
        },
        plugins: [verticalLinePlugin]
    });
}

// Telemetry Play/Pause
function playTelemetry() {
    if (!currentUnitData) return;
    
    btnPlay.style.display = "none";
    btnPause.style.display = "block";
    
    if (currentCycleIndex >= currentUnitData.records.length - 1) {
        setCycle(0);
    }
    
    playInterval = setInterval(() => {
        if (currentCycleIndex < currentUnitData.records.length - 1) {
            setCycle(currentCycleIndex + 1);
        } else {
            pauseTelemetry();
        }
    }, 250);
}

function pauseTelemetry() {
    btnPlay.style.display = "block";
    btnPause.style.display = "none";
    
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}
