# API Reference

## 🔌 Complete API Documentation

### Registry (Port 8000)

#### POST /register
Register a node with the central registry

**Request:**
```json
{
  "address": "http://localhost:8081"
}
```

**Response:**
```json
{
  "status": "registered",
  "address": "http://localhost:8081"
}
```

#### GET /nodes
Get list of healthy registered nodes

**Response:**
```json
{
  "nodes": [
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:8083"
  ],
  "count": 3
}
```

#### GET /health
Check registry health

**Response:**
```json
{
  "status": "healthy",
  "uptime": "2h30m"
}
```

---

### Node Server (Port 8081+)

#### GET /
Main status page with HTML UI

**Response:** HTML page showing CPU load, peers, best peer

#### GET /load
Current CPU load

**Response:**
```json
{
  "address": "http://localhost:8081",
  "cpuLoad": 45.2
}
```

#### GET /health
Node health check

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /ping
Heartbeat endpoint for A_M_R

**Response:**
```json
{
  "status": "pong",
  "address": "http://localhost:8081"
}
```

---

### A_M_R Endpoints (P2P Fallback)

#### GET /a_m_r/status
Get A_M_R mode status

**Response:**
```json
{
  "mode": "A_M_R",
  "status": "active",
  "my_address": "http://localhost:8081",
  "active_peers_count": 2,
  "active_peers": [
    "http://localhost:8082",
    "http://localhost:8083"
  ],
  "timestamp": "2025-12-07T10:30:45.123456"
}
```

#### GET /a_m_r/botlist
Get this node's peer list

**Response:**
```json
{
  "address": "http://localhost:8081",
  "peers": [
    "http://localhost:8082",
    "http://localhost:8083"
  ],
  "count": 2,
  "timestamp": "2025-12-07T10:30:45.123456"
}
```

#### POST /a_m_r/sync
Synchronize peers from external source

**Request:**
```json
{
  "peers": [
    "http://localhost:8084",
    "http://localhost:8085"
  ]
}
```

**Response:**
```json
{
  "status": "synced",
  "added": 2,
  "total_peers": 4
}
```

#### POST /a_m_r/activate
Manually activate A_M_R mode

**Response:**
```json
{
  "status": "activated",
  "message": "A_M_R mode is now active (P2P)",
  "peers": ["http://localhost:8082", ...]
}
```

#### POST /a_m_r/deactivate
Manually deactivate A_M_R mode

**Response:**
```json
{
  "status": "deactivated",
  "message": "A_M_R mode is now inactive"
}
```

---

## 📊 Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Health check pass |
| 307 | Temporary Redirect | Node overloaded, redirecting |
| 400 | Bad Request | Invalid JSON |
| 500 | Internal Error | Registry/Node error |

---

## 🔄 Headers

### Request Headers

```
X-Redirect-Count: 0
  → Tracks redirect loop prevention
```

### Response Headers

```
X-Redirect-Count: 1
  → Incremented on each redirect
```

---

## 💬 Example Workflows

### Workflow 1: Get Node Status

```bash
# 1. Get load
curl http://localhost:8081/load

# 2. Get health
curl http://localhost:8081/health

# 3. Get A_M_R status
curl http://localhost:8081/a_m_r/status
```

### Workflow 2: Manual P2P Setup

```bash
# Node 1: Introduce Node 2
curl -X POST http://localhost:8081/a_m_r/sync \
  -H "Content-Type: application/json" \
  -d '{"peers": ["http://localhost:8082"]}'

# Node 1: Activate A_M_R
curl -X POST http://localhost:8081/a_m_r/activate

# Node 1: Check botlist
curl http://localhost:8081/a_m_r/botlist
```

### Workflow 3: Stress Testing

```bash
# Terminal 1: Start load test
python3 src/load_test.py --mode async --rate 100

# Terminal 2: Monitor Node 1
while true; do
  curl -s http://localhost:8081/load | jq '.cpuLoad'
  sleep 1
done

# Terminal 3: Monitor A_M_R (if registry down)
curl http://localhost:8081/a_m_r/status | jq '.active_peers'
```

---

Daha fazla örnek için [[Testing]] sayfasını ziyaret et. 🚀
