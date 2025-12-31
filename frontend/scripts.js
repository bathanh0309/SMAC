// ===== Person Detection Gate System - Frontend Script =====
// No MQTT - using Python API directly

console.log('[SMAC] Person Detection Gate System loading...');

// Gate state
let gateState = 'OFF';

// ================= UPDATE GATE UI =================
function updateGateUI(stateStr) {
    const state = stateStr.toUpperCase();
    const isOpen = (state === 'ON' || state === 'OPEN');

    gateState = state;

    const barrier = document.getElementById('barrier-in');
    const btn = document.getElementById('btn-in');
    const btnState = document.getElementById('btn-in-state');

    if (!barrier || !btn || !btnState) {
        return;
    }

    if (isOpen) {
        barrier.classList.add('open');
        btn.classList.add('active');
        btnState.textContent = 'OPEN';
    } else {
        barrier.classList.remove('open');
        btn.classList.remove('active');
        btnState.textContent = 'CLOSE';
    }
}

// ================= MANUAL GATE CONTROL =================
function toggleGateIN() {
    console.log('[User] Manual IN button clicked');

    const btn = document.getElementById('btn-in');
    const isCurrentlyOpen = btn.classList.contains('active');
    const newState = isCurrentlyOpen ? 'OFF' : 'ON';

    // Send manual control to server
    fetch('/api/gate/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gate: 'IN', state: newState })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(`[Manual Control] Gate IN → ${newState}`);
                updateGateUI(newState);
                setTimeout(fetchLogs, 300);
            }
        })
        .catch(err => console.error('[API Error]', err));
}

// ================= LOAD LOGS FROM API ==================
function fetchLogs() {
    fetch('/api/logs')
        .then(res => res.json())
        .then(data => {
            if (data.message === 'success') {
                const tbody = document.querySelector('#log-table tbody');
                tbody.innerHTML = '';

                if (data.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" class="table-empty">No logs yet</td></tr>';
                    return;
                }

                data.data.forEach(log => {
                    const row = document.createElement('tr');

                    // Timestamp
                    const tdTime = document.createElement('td');
                    tdTime.textContent = log.timestamp;
                    row.appendChild(tdTime);

                    // Event Type with color
                    const tdEvent = document.createElement('td');
                    tdEvent.textContent = log.event_type;

                    if (log.event_type === 'GATE_OPEN' || log.event_type === 'GATE_ON') {
                        tdEvent.style.color = '#4CAF50';
                        tdEvent.style.fontWeight = '600';
                    } else if (log.event_type === 'GATE_CLOSE' || log.event_type === 'GATE_OFF') {
                        tdEvent.style.color = '#f44336';
                        tdEvent.style.fontWeight = '600';
                    } else if (log.event_type === 'PERSON_DETECTED') {
                        tdEvent.style.color = '#2196F3';
                        tdEvent.style.fontWeight = '600';
                    }
                    row.appendChild(tdEvent);

                    // Description
                    const tdDesc = document.createElement('td');
                    tdDesc.textContent = log.description;
                    row.appendChild(tdDesc);

                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => console.error('[API Error]', err));
}

// ================= LOAD DETECTIONS ==================
function fetchDetections() {
    fetch('/api/detections')
        .then(res => res.json())
        .then(data => {
            if (data.message === 'success') {
                const tbody = document.querySelector('#detections-table tbody');
                tbody.innerHTML = '';

                if (data.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" class="table-empty">No detections</td></tr>';
                    return;
                }

                data.data.slice(0, 10).forEach(det => {
                    const row = document.createElement('tr');

                    // Person count
                    const tdPerson = document.createElement('td');
                    tdPerson.textContent = `${det.person_count || 1} person(s)`;
                    tdPerson.style.fontWeight = '600';
                    tdPerson.style.color = '#2196F3';
                    row.appendChild(tdPerson);

                    // Time
                    const tdTime = document.createElement('td');
                    tdTime.textContent = det.datetime;
                    tdTime.style.fontSize = '0.9em';
                    row.appendChild(tdTime);

                    // Confidence
                    const tdConf = document.createElement('td');
                    tdConf.textContent = `${(det.confidence * 100).toFixed(1)}%`;
                    tdConf.style.color = '#4CAF50';
                    row.appendChild(tdConf);

                    tbody.appendChild(row);
                });
            }
        })
        .catch(err => console.error('[API Error]', err));
}

// ================= EXPORT CSV =================
function exportLogsToCSV() {
    window.location.href = '/api/logs/export';
}

// ================= CHECK CAMERA STATUS =================
function checkCameraStatus() {
    const streamImg = document.getElementById('stream');
    const statusText = document.getElementById('camera-status-text');

    streamImg.onerror = () => {
        statusText.textContent = '🔴 AI Camera: Disconnected';
        statusText.style.color = '#f44336';
    };

    streamImg.onload = () => {
        statusText.textContent = '🟢 AI Camera: Active';
        statusText.style.color = '#4caf50';
    };
}

// ================= LIGHT BULB & DETECTION STATUS =================
function updateDetectionStatus(data) {
    const lightBulb = document.getElementById('light-bulb');
    const countdownText = document.getElementById('countdown-text');
    const detectionStatus = document.getElementById('detection-status-text');

    if (!lightBulb || !countdownText) {
        console.error('[UI] Light bulb or countdown elements not found');
        return;
    }

    const personDetected = data.person_detected;
    const countdown = data.countdown;
    const gateState = data.gate_state;
    const confidence = data.confidence;
    const personCount = data.person_count;

    // Update detection status text with countdown inline
    if (detectionStatus) {
        if (personDetected && countdown > 0 && gateState !== 'OPEN') {
            // Show person detected + countdown
            detectionStatus.textContent = `🟢 Phát hiện ${personCount} người (${(confidence * 100).toFixed(0)}%) - ⏱️ ${Math.ceil(countdown)}s`;
            detectionStatus.style.color = '#ff9800';  // Orange during countdown
        } else if (personDetected && gateState === 'OPEN') {
            // Gate is open
            detectionStatus.textContent = `🟢 Phát hiện ${personCount} người (${(confidence * 100).toFixed(0)}%) - 🚪 Cổng mở`;
            detectionStatus.style.color = '#4caf50';  // Green when open
        } else if (personDetected) {
            // Just detected
            detectionStatus.textContent = `🟢 Phát hiện ${personCount} người (${(confidence * 100).toFixed(0)}%)`;
            detectionStatus.style.color = '#4caf50';
        } else {
            detectionStatus.textContent = '⚪ Chờ phát hiện...';
            detectionStatus.style.color = '#999';
        }
    }

    // Update realtime detection table (Recent Detections)
    updateRealtimeTable(personDetected, personCount, confidence, countdown, gateState);

    // Update light bulb - always ON when person detected
    if (personDetected) {
        lightBulb.classList.add('active');
        console.log('[UI] Light ON - person detected');
    } else {
        lightBulb.classList.remove('active');
    }

    // Update countdown text below light bulb
    if (countdown > 0 && gateState !== 'OPEN') {
        countdownText.classList.add('counting');
        countdownText.textContent = `⏱️ ${Math.ceil(countdown)}s`;
    } else if (gateState === 'OPEN') {
        countdownText.classList.remove('counting');
        countdownText.textContent = '🚪 Cổng đang mở';
    } else {
        countdownText.classList.remove('counting');
        countdownText.textContent = '';
    }

    // Update gate UI
    updateGateUI(gateState);
}

// ================= UPDATE REALTIME TABLE =================
function updateRealtimeTable(personDetected, personCount, confidence, countdown, gateState) {
    const tbody = document.querySelector('#detections-table tbody');
    if (!tbody) return;

    if (personDetected) {
        // Show current detection at the top of realtime table
        const now = new Date();
        const timeStr = now.toLocaleString('vi-VN');

        let statusText = '';
        if (countdown > 0 && gateState !== 'OPEN') {
            statusText = ` ⏱️${Math.ceil(countdown)}s`;
        } else if (gateState === 'OPEN') {
            statusText = ' 🚪Mở';
        }

        tbody.innerHTML = `
            <tr style="background: #e8f5e9;">
                <td style="font-weight:600; color:#2196F3;">${personCount} người${statusText}</td>
                <td style="font-size:0.9em;">${timeStr}</td>
                <td style="color:#4CAF50;">${(confidence * 100).toFixed(1)}%</td>
            </tr>
        `;
    } else {
        // When no detection, show "No detections"
        tbody.innerHTML = '<tr><td colspan="3" class="table-empty">Chờ phát hiện...</td></tr>';
    }
}

// ================= AUTO LOAD ON PAGE LOAD =================
window.addEventListener('DOMContentLoaded', () => {
    console.log('[Page] DOM loaded, initializing...');

    checkCameraStatus();
    fetchLogs();
    fetchDetections();

    // Auto-refresh logs and detections every 3 seconds
    setInterval(() => {
        fetchLogs();
        fetchDetections();
    }, 3000);

    // Check detection status from Python backend (fast polling for realtime)
    setInterval(() => {
        fetch('http://localhost:8000/api/status')
            .then(res => res.json())
            .then(data => {
                updateDetectionStatus(data);
            })
            .catch(() => { });
    }, 300);  // Poll every 300ms for smooth countdown
});