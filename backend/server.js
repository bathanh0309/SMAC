// ===== File: server.js =====
// Person Detection Gate Control - Backend Server
// Simplified: Only IN gate, no vehicle/plate tracking

const express = require('express');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const PORT = 3000;

// 1. SETUP DATABASE (SQLite)
const dbPath = path.join(__dirname, '../database/gate_system.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) console.error('[DB] Cannot open database:', err.message);
    else console.log('[DB] Connected to SQLite database.');
});

// Create logs table if not exists
db.run(`CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,
    description TEXT
)`);

// Create detections table for person events
db.run(`CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_count INTEGER NOT NULL,
    datetime TEXT NOT NULL,
    confidence REAL NOT NULL,
    image_path TEXT
)`, (err) => {
    if (err) console.error('[DB] Error creating detections table:', err);
    else console.log('[DB] ✓ Detections table ready');
});

// 2. GATE STATE (No MQTT from server - Python handles MQTT)
let currentGateState = {
    in: 'OFF'
};

// Helper: Get local timestamp
function getLocalTime() {
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    return new Date(now.getTime() - offset).toISOString().slice(0, 19).replace('T', ' ');
}

// 3. SERVER CONFIG
app.use(express.static(path.join(__dirname, '../frontend')));
app.use(express.json());

// ===== API: Get logs =====
app.get('/api/logs', (req, res) => {
    db.all("SELECT * FROM logs ORDER BY id DESC LIMIT 50", [], (err, rows) => {
        if (err) {
            res.status(400).json({ "error": err.message });
            return;
        }
        res.json({
            "message": "success",
            "data": rows
        });
    });
});

// ===== API: Get recent detections =====
app.get('/api/detections', (req, res) => {
    db.all("SELECT * FROM detections ORDER BY id DESC LIMIT 20", [], (err, rows) => {
        if (err) {
            res.status(400).json({ "error": err.message });
            return;
        }
        res.json({
            "message": "success",
            "data": rows
        });
    });
});

// ===== API: Get gate status =====
app.get('/api/gate/status', (req, res) => {
    res.json({
        "in": currentGateState.in
    });
});

// ===== API: Update gate status (called by Python) =====
app.post('/api/gate/status', (req, res) => {
    const { state } = req.body;

    if (!state || !['ON', 'OFF'].includes(state.toUpperCase())) {
        return res.json({ status: 'error', message: 'Invalid state' });
    }

    const newState = state.toUpperCase();
    const localTime = getLocalTime();

    // Only log if state changed
    if (currentGateState.in !== newState) {
        currentGateState.in = newState;

        const eventType = newState === 'ON' ? 'GATE_OPEN' : 'GATE_CLOSE';
        const description = newState === 'ON' ? 'Person detected - Gate opened' : 'No person - Gate closed';

        // Log event
        const stmt = db.prepare("INSERT INTO logs (timestamp, event_type, description) VALUES (?, ?, ?)");
        stmt.run(localTime, eventType, description);
        stmt.finalize();

        console.log(`[Gate] ${eventType} at ${localTime}`);
    }

    res.json({
        status: 'success',
        gate: 'IN',
        state: newState,
        timestamp: localTime
    });
});

// ===== API: Add detection record (called by Python) =====
app.post('/api/detection', (req, res) => {
    const { person_count, confidence, image_path } = req.body;

    if (person_count === undefined || confidence === undefined) {
        return res.json({ status: 'error', message: 'Missing required fields' });
    }

    const localTime = getLocalTime();

    const stmt = db.prepare("INSERT INTO detections (person_count, datetime, confidence, image_path) VALUES (?, ?, ?, ?)");
    stmt.run(person_count, localTime, confidence, image_path || '', (err) => {
        if (err) {
            console.error('[DB] Insert detection error:', err);
            return res.json({ status: 'error', message: err.message });
        }

        // Also log the event
        const logStmt = db.prepare("INSERT INTO logs (timestamp, event_type, description) VALUES (?, ?, ?)");
        logStmt.run(localTime, 'PERSON_DETECTED', `Detected ${person_count} person(s) (${(confidence * 100).toFixed(1)}%)`);
        logStmt.finalize();

        console.log(`[Detection] ${person_count} person(s) at ${localTime}`);

        res.json({
            status: 'success',
            person_count: person_count,
            timestamp: localTime
        });
    });
    stmt.finalize();
});

// ===== API: Manual gate control =====
app.post('/api/gate/manual', (req, res) => {
    const { gate, state } = req.body;

    if (!gate || !state || gate.toUpperCase() !== 'IN') {
        return res.json({ status: 'error', message: 'Invalid parameters (only IN gate supported)' });
    }

    const localTime = getLocalTime();
    const gateState = state.toUpperCase();

    currentGateState.in = gateState;

    const eventType = `GATE_${gateState}`;
    const description = `Manual control - ${gateState}`;

    console.log(`[Manual Control] ${eventType} at ${localTime}`);

    const stmt = db.prepare("INSERT INTO logs (timestamp, event_type, description) VALUES (?, ?, ?)");
    stmt.run(localTime, eventType, description, (err) => {
        if (err) {
            console.error('[DB Error]', err);
            return res.json({ status: 'error', message: 'Database error' });
        }

        res.json({
            status: 'success',
            gate: 'IN',
            state: gateState,
            timestamp: localTime
        });
    });
    stmt.finalize();
});

// ===== API: Export logs as CSV =====
app.get('/api/logs/export', (req, res) => {
    db.all("SELECT * FROM logs ORDER BY timestamp DESC", [], (err, rows) => {
        if (err) {
            res.status(400).json({ "error": err.message });
            return;
        }

        let csv = 'ID,Timestamp,Event Type,Description\n';
        rows.forEach(row => {
            csv += `${row.id},"${row.timestamp}","${row.event_type}","${row.description}"\n`;
        });

        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', 'attachment; filename=gate_logs.csv');
        res.send(csv);
    });
});

// Serve Frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// Start Server
app.listen(PORT, () => {
    console.log('\n========================================');
    console.log('   PERSON DETECTION GATE SYSTEM');
    console.log('========================================');
    console.log(`✓ Web Server : http://localhost:${PORT}`);
    console.log(`✓ Database   : database/gate_system.db`);
    console.log(`✓ Gate Mode  : IN only`);
    console.log('========================================\n');
});