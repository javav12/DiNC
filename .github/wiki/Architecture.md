# Architecture

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────┐
│        DiNC Distributed System          │
└─────────────────────────────────────────┘

        ┌──────────────────┐
        │   Go Registry    │  (Port 8000)
        │   Central Hub    │
        └────────┬─────────┘
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
    ┌─────┐  ┌─────┐  ┌─────┐
    │ N1  │  │ N2  │  │ N3  │  (Python Flask Nodes)
    │8081 │  │8082 │  │8083 │
    └─────┘  └─────┘  └─────┘
        │        │        │
        └────────┼────────┘
                 │
          Registry DOWN?
                 ▼
        ┌──────────────────┐
        │   P2P A_M_R      │  (Fallback Mode)
        │   Botlist Sync   │
        └──────────────────┘
```

---

## 🔄 Üç Layer Mimarisi

### Layer 1: Central Registry (Go)
- **Rolü**: Node discovery ve health management
- **Port**: 8000
- **Protokol**: HTTP/REST
- **Sürekliliği**: Heartbeat (5s), Health check (15s)

```go
// Node registration
POST /register
{
  "address": "http://localhost:8081"
}

// Node discovery
GET /nodes
→ ["http://localhost:8081", "http://localhost:8082"]
```

### Layer 2: Node Servers (Python/Flask)
- **Rolü**: İş yükü işleme, load balancing
- **Port**: 8081+ (dinamik)
- **Protokol**: HTTP/REST
- **Protokol**: State management, peer discovery

```python
# CPU load
GET /load → {"cpuLoad": 45.2}

# Health check
GET /health → {"status": "healthy"}

# Redirect to best peer
GET / → 307 to http://localhost:8082
```

### Layer 3: P2P Fallback (A_M_R)
- **Rolü**: Registry düştüğünde P2P ağ
- **Protokol**: Botlist sync, peer discovery
- **Sürekliliği**: Her 5-10 saniye

```python
# Get active peers
GET /a_m_r/botlist → ["http://localhost:8082", ...]

# Health check
GET /health → Node alive?
```

---

## 📊 Veri Akışı

### 1. Normal Operasyon (Registry UP)

```
Client Request
     │
     ▼
[Node 1] - Heartbeat → [Registry]
    │                       │
    ├─ GET /load ───→ CPU load rapor
    │
    ├─ Is overloaded?
    │  YES → Redirect to best peer
    │  NO  → Process request
    │
    ▼
Response to Client
```

### 2. Registry Düştüğünde

```
Client Request
     │
     ▼
[Node 1] - Heartbeat FAIL
    │
    ├─ A_M_R Mode AUTO ACTIVATE
    │
    ├─ GET /a_m_r/botlist ─→ [Node 2, 3, ...]
    │
    ├─ Botlist Sync (every 5s)
    │  ├─ Peer 1 → "I know [2, 3, 4, 5]"
    │  ├─ Peer 2 → "I know [1, 3, 4, 6]"
    │  └─ Merge: All peers know each other
    │
    ├─ Health Check (every 10s)
    │  ├─ Dead peers → Remove
    │  └─ Alive peers → Keep
    │
    ▼
Full P2P Network
```

### 3. Registry Geri Geldiğinde

```
[Registry] comes back online
     │
     ▼
[Nodes] - Heartbeat SUCCESS
    │
    ├─ A_M_R Mode AUTO DEACTIVATE
    │
    ├─ Back to normal discovery
    │
    ▼
Centralized Control Restored
```

---

## 🎯 Komponent İlişkileri

| Komponent | Bağımlılık | Fonksiyon |
|-----------|-----------|-----------|
| Registry | Standalone | Node discovery |
| Heartbeat | Registry | Periodic registration |
| Discovery | Registry | Peer listing |
| State | Local | CPU/latency tracking |
| A_M_R | None (P2P) | Fallback when Registry down |
| Load Balancer | State, best_peer | Redirect logic |

---

## 🔗 İletişim Protokolleri

### Registry ↔ Node

```
HEARTBEAT (Heartbeat.py):
Every 5 seconds:
POST /register → {address: "http://localhost:8081"}

DISCOVERY (Discovery.py):
Every 10 seconds:
GET /nodes → [node1, node2, ...]

PEER LOAD POLLING:
Every 7 seconds:
GET /load → {cpuLoad: 45.2, address: ...}
```

### Node ↔ Node (P2P Mode)

```
BOTLIST SYNC (A_M_R):
Every 5 seconds:
GET /a_m_r/botlist → {peers: [...], count: N}

HEALTH CHECK:
Every 10 seconds:
GET /health → {status: "healthy"}

STATE SYNC:
POST /a_m_r/sync → {peers: [...]}
```

---

## ⚙️ Scoring Algoritması

Her peer için **composite score** hesaplanır:

```
Score = (CPU_Load × 0.7) + (Latency_ms × 0.3)

Düşük score = Daha iyi peer ✅
```

### Örnek

```
Node 1: CPU=50%, Latency=10ms
Score = (50 × 0.7) + (10 × 0.3) = 35 + 3 = 38

Node 2: CPU=70%, Latency=5ms
Score = (70 × 0.7) + (5 × 0.3) = 49 + 1.5 = 50.5

Node 3: CPU=30%, Latency=20ms
Score = (30 × 0.7) + (20 × 0.3) = 21 + 6 = 27

BEST PEER: Node 3 (lowest score)
```

---

## 🛡️ Redirect Loop Koruması

Her redirect'te `X-Redirect-Count` header'ı arttırılır:

```
Request 1: X-Redirect-Count: 0
  → Node 1 overloaded
  → Redirect to Node 2 (count: 1)

Request 2: X-Redirect-Count: 1
  → Node 2 overloaded
  → Redirect to Node 1 (count: 2)

Request 3: X-Redirect-Count: 2
  → Node 1 overloaded
  → Redirect to Node 3 (count: 3)

Request 4: X-Redirect-Count: 3
  → Max redirects reached!
  → Serve from self (no more redirects)
```

---

## 🧵 Threading Model

```python
Node Server:
├── Main Thread
│   └── Flask app (HTTP server)
│
├── Heartbeat Thread
│   └── POST /register (every 5s)
│
├── Discovery Thread
│   ├── GET /nodes (every 10s)
│   └── GET /load (every 7s for each peer)
│
└── A_M_R Thread (when Registry DOWN)
    ├── Botlist Sync (every 5s)
    └── Health Check (every 10s)

All operations are thread-safe with RLock()
```

---

## 📈 Skalabilite

| Metrik | Sınır | Notlar |
|--------|-------|--------|
| Node Sayısı | 100+ | Registry'ye bağlı |
| Request Rate | 1000+ req/s | Load test'e bağlı |
| Peer Discovery | O(n) | Botlist senkronizasyonu |
| Memory/Node | ~50MB | Baseline |

---

## 🔐 Güvenlik Katmanları

1. **HTTP**: İsteklerin şifrelenmesi (opsiyonel HTTPS)
2. **Validation**: Input validation ve sanitization
3. **Timeout**: Request timeout'ları (2-3 sn)
4. **Health Check**: Dead peer'ların otomatik çıkarılması

---

Daha fazla bilgi için [[Components]] sayfasını ziyaret et. 📖
