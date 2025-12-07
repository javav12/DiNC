# A_M_R (Attack Mode Request)

## 🔴 P2P Fallback System

A_M_R, central registry düştüğünde node'ların peer-to-peer ağ kurarak iletişim kurabileceği otomatik fallback sistemidir.

### Diagram

```
Registry UP (Normal):
   ┌──────────┐
   │ Registry │
   └─────┬────┘
         │
   ┌─────┼─────┐
   │     │     │
  Node  Node  Node
   1     2     3

Registry DOWN (A_M_R Active):
Node1 ←→ Node2
  ↑       ↑
  └───┬───┘
      │
    Node3
(Full P2P Mesh)
```

---

## 🎯 Özellikler

- ✅ **Otomatik Aktivasyon**: Registry heartbeat fail → A_M_R starts
- ✅ **Botlist Sync**: Node'lar bildiği node'ları paylaşır
- ✅ **Health Monitoring**: Dead peer'ları otomatik çıkarır
- ✅ **Zero Config**: İlave yapılandırma gerekmez
- ✅ **Modüler**: Kendi logik ekleyebilirsin

---

## 🔄 Nasıl Çalışır

### 1. Botlist Sync Loop (Her 5 Saniye)

```
Node 1 → GET /a_m_r/botlist → Node 2
         "I know [1,2,3,5]"
Node 1 → GET /a_m_r/botlist → Node 3
         "I know [1,2,3,4,6]"

Merge: Node 1 now knows [1,2,3,4,5,6]
```

### 2. Health Check Loop (Her 10 Saniye)

```
Node 1 → GET /health → Node 4 ✓ (alive)
Node 1 → GET /health → Node 7 ✗ (dead)
         Remove Node 7 from list
```

### 3. Senkronizasyon

```
Yeni peer bulunca:
Event: New peer discovered (Node 4 → Node 8)
Action: POST /a_m_r/sync to all peers
Result: Everyone knows Node 8 (Epidemic protocol)
```

---

## 📊 API Endpoints

### GET /a_m_r/status

A_M_R modunun durumunu göster

```bash
curl http://localhost:8081/a_m_r/status
```

Response:
```json
{
  "mode": "A_M_R",
  "status": "active",
  "my_address": "http://localhost:8081",
  "active_peers_count": 3,
  "active_peers": [
    "http://localhost:8082",
    "http://localhost:8083",
    "http://localhost:8084"
  ],
  "timestamp": "2025-12-07T10:30:45"
}
```

### GET /a_m_r/botlist

Bu node'un bildiği peer'ları döndür

```bash
curl http://localhost:8081/a_m_r/botlist
```

Response:
```json
{
  "address": "http://localhost:8081",
  "peers": [
    "http://localhost:8082",
    "http://localhost:8083",
    "http://localhost:8084"
  ],
  "count": 3,
  "timestamp": "2025-12-07T10:30:45"
}
```

### POST /a_m_r/sync

Dış kaynaktan peer'ları senkronize et

```bash
curl -X POST http://localhost:8081/a_m_r/sync \
  -H "Content-Type: application/json" \
  -d '{
    "peers": ["http://localhost:8085", "http://localhost:8086"]
  }'
```

Response:
```json
{
  "status": "synced",
  "added": 2,
  "total_peers": 5
}
```

### POST /a_m_r/activate

A_M_R modunu manuel başlat

```bash
curl -X POST http://localhost:8081/a_m_r/activate
```

### POST /a_m_r/deactivate

A_M_R modunu durdur

```bash
curl -X POST http://localhost:8081/a_m_r/deactivate
```

---

## 🧪 Test Senaryosu

### Setup: 3 Node Network

**Terminal 1:**
```bash
go run src/registry_server/main.go
```

**Terminal 2-4:**
```bash
python3 src/node_server.py --port 8081 &
python3 src/node_server.py --port 8082 &
python3 src/node_server.py --port 8083 &
```

### Test 1: Manual P2P

```bash
# Node 1'e Node 2'yi tanıt
curl -X POST http://localhost:8081/a_m_r/sync \
  -H "Content-Type: application/json" \
  -d '{"peers": ["http://localhost:8082"]}'

# A_M_R başlat
curl -X POST http://localhost:8081/a_m_r/activate

# Botlist senkronizasyonunu izle
for i in {1..10}; do
  echo "=== Iteration $i ==="
  curl -s http://localhost:8081/a_m_r/botlist | jq '.count'
  sleep 1
done

# Beklenen: Count 1 → 2 → 3 (botlist sync'i)
```

### Test 2: Registry Failure

```bash
# Registry'yi durdur
killall go

# Node'ların otomatik A_M_R moduna geçmesini izle
tail -f logs.txt | grep "A_M_R"

# Peer'ların senkronize olup olmadığını kontrol et
curl http://localhost:8081/a_m_r/status

# Registry geri başlat
go run src/registry_server/main.go

# A_M_R otomatik kapanır
```

---

## 🔧 Kustomizasyon

### Özel AMR Sınıfı

`src/utils/a_m_r.py` dosyasında:

```python
class MyCustomAMR(AMRClient):
    """Kendi özel A_M_R mantığı"""
    
    def __init__(self, my_address, known_peers=None, custom_param=None):
        super().__init__(my_address, known_peers)
        self.custom_param = custom_param
    
    def process_botlist(self, botlist):
        """Botlist'i filtrele"""
        # Örn: Sadece sağlıklı peer'ları al
        return [p for p in botlist if self.is_healthy(p)]
    
    def on_peer_found(self, peer_address):
        """Yeni peer bulunduğunda"""
        logger.info(f"🎉 Found peer: {peer_address}")
        # Custom notification
    
    def on_peer_lost(self, peer_address):
        """Peer kaybedildiğinde"""
        logger.warning(f"💀 Lost peer: {peer_address}")
        # Cleanup
```

### Node'da Kullan

`src/node_server.py`:

```python
from utils import MyCustomAMR, register_a_m_r_routes

# Initialize function'da:
a_m_r = MyCustomAMR(my_addr, known_peers=[], custom_param="value")
register_a_m_r_routes(app, a_m_r)
```

---

## ⚙️ Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| botlist_interval | 5s | Botlist sync frequency |
| health_interval | 10s | Health check frequency |
| peer_timeout | 2s | Peer response timeout |
| max_peers | Unlimited | Max peer limit |

### Özelleştirme

`a_m_r.py` başında:

```python
class AMRClient:
    def __init__(self, my_address, known_peers=None, 
                 botlist_interval=5, health_interval=10):
        # ...
        self.botlist_interval = botlist_interval
        self.health_interval = health_interval
```

---

## 🛡️ Güvenlik Notları

⚠️ **A_M_R Mode'da göz at:**

1. **Trust**: Herhangi bir node'u ekleyebilirsin
   - Güvenli olmayan peer'ları kontrol et

2. **Bandwidth**: Botlist sync düzenli yapılır
   - Interval'ları ayarla

3. **DNS**: Domain kullanırsan HTTPS şifrele

4. **Isolation**: P2P ağ internal'de kalmalı

---

## 📈 Performance

| Operation | Time | Impact |
|-----------|------|--------|
| Botlist Sync | ~100ms | Low |
| Health Check | ~50ms | Very Low |
| Peer Addition | ~10ms | Negligible |

---

## 🔗 İlişkili Sayfalar

- [[Architecture]] - Sistem mimarisi
- [[API-Reference]] - Tüm API endpoints
- [[Testing]] - Test senaryoları

Hazır mısın? 🚀
