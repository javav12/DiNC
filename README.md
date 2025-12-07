# DiNC - Distributed Node Coordinator

[🇹🇷 Türkçe](#türkçe) | [🇬🇧 English](#english) | [📖 Wiki](https://github.com/javav12/DiNC/wiki)

---

## Türkçe

Yüksek kullanılabilirlik ve otomatik yük dengeleme ile dağıtılmış sistem mimarisi.

### 🎯 Özellikler

- **Dağıtılmış Mimari**: Go tabanlı merkezi registry + Python node'lar
- **Otomatik Yük Dengeleme**: CPU eşiği (%70) aşınca peer'a yönlendir
- **Sağlık Kontrolü**: Periyodik heartbeat ve peer discovery
- **Composite Scoring**: CPU (70%) + Latency (30%) kombinasyonu
- **Redirect Loop Koruması**: X-Redirect-Count header ile sonsuz döngü engelle
- **Load Testing**: Async ve thread tabanlı test araçları


### 📋 Gereksinimler

- Python 3.9+
- Go 1.21+
- Linux/macOS (Windows WSL2 önerilir)

### 🚀 Hızlı Başlangıç

#### 1. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
go mod download
```

#### 2. Registry'i başlat (Terminal 1)

```bash
go run src/registry_server/main.go
```

#### 3. Node'ları başlat (Terminal 2 ve 3)

```bash
python3 src/node_server.py --port 8081
python3 src/node_server.py --port 8082
```

#### 4. Load test çalıştır (Terminal 4)

```bash
# Async mode (önerilen - yüksek performans)
python3 src/load_test.py --mode async --rate 50

# Veya Thread mode (basit)
python3 src/load_test.py --mode thread --rate 50
```

### 📁 Proje Yapısı

```
DiNC/
├── src/
│   ├── registry_server/
│   │   └── main.go              # Go merkezi registry (port 8000)
│   ├── node_server/
│   │   ├── templates/
│   │   │   └── status.html      # Web UI şablonu
│   │   └── static/
│   │       └── css/
│   │           └── style.css    # Cloudflare-inspired tema
│   ├── utils/
│   │   ├── state.py             # Thread-safe durum yönetimi
│   │   ├── heartbeat.py         # Periyodik registry kaydı
│   │   ├── discovery.py         # Peer keşfi ve sorgulama
│   │   └── __init__.py
│   ├── node_server.py           # Flask node uygulaması
│   └── load_test.py             # Async/Thread tabanlı load test
├── requirements.txt             # Python bağımlılıkları
├── go.mod                       # Go modül tanımı
├── .gitignore                   # Git ignore kuralları
└── README.md                    # Bu dosya
```

### 🔌 API Endpoints

#### Registry (port 8000)

- `POST /register` - Node kendisini kaydet
- `GET /nodes` - Sağlıklı node'ları listele
- `GET /health` - Registry'nin sağlığını kontrol et

#### Node (port 8081+)

- `GET /` - Ana durum sayfası (yüklü ise yönlendir)
- `GET /load` - JSON formatında CPU yükü
- `GET /ping` - Heartbeat endpoint'i
- `GET /health` - Node sağlığı

### ⚙️ Konfigürasyon

#### Node CPU Eşiği

```bash
python3 src/node_server.py --port 8081 --cpu-threshold 75.0
```

#### Load Test Parametreleri

```bash
# Async mode
python3 src/load_test.py --mode async --rate 100 --concurrent 200

# Thread mode
python3 src/load_test.py --mode thread --rate 100 --workers 20
```

### 🧪 Test

#### GitHub Actions

Push veya PR oluştur → Actions sekmesinde workflow'u izle

```bash
git push origin main
```

#### Lokal Test

```bash
# Health check
curl http://localhost:8081/health

# Load endpoint
curl http://localhost:8081/load

# Ping
curl http://localhost:8082/ping

# Redirect testi (max 3 redirect)
curl -L --max-redirs 3 http://localhost:8081/
```

### 🛡️ Redirect Loop Koruması

Her yönlendirmede `X-Redirect-Count` header'ı arttırılır:

- Count < 3: Yönlendir
- Count ≥ 3: Kendine hizmet ver (döngü engeli)

### 📊 Performans Özellikleri

| Özellik | Değer |
|---------|-------|
| Heartbeat Interval | 5 saniye |
| Peer Discovery Interval | 10 saniye |
| Peer Load Polling | 7 saniye |
| Health Check Timeout | 15 saniye |
| Score Formula | `(CPU × 0.7) + (Latency × 0.3)` |
| CPU Threshold | 70% (konfigüre edilebilir) |
| Max Redirects | 3 |

### 🚦 Scoring Sistemi

Peer seçimi basit metrikler kullanır:

1. **CPU Yükü** (%): Node'un mevcut CPU kullanımı
2. **Latency** (ms): İsteğin gidiş-dönüş süresi
3. **Score**: `(load × 0.7) + (latency × 0.3)`

**Düşük score = daha iyi peer** ✅

### 🐛 Hata Giderme

#### Registry'ye bağlanamıyorum

```bash
# Registry çalışıyor mu?
curl http://localhost:8000/health

# Portun açık olup olmadığını kontrol et
lsof -i :8000
```

#### Sonsuz redirect döngüsü

HTTP_CODE 307 + X-Redirect-Count header'ını kontrol et:

```bash
curl -v http://localhost:8081/
```

#### Peer'lar keşfedilmiyor

```bash
# Node loglarını kontrol et
tail -f /tmp/dinc*.log  # varsa

# Merkezi sunucuya kayıt kontrolü
curl http://localhost:8000/nodes
```

---

## English

A distributed system architecture with high availability and automatic load balancing.

### 🎯 Features

- **Distributed Architecture**: Go-based central registry + Python nodes
- **Automatic Load Balancing**: Redirect to peer when CPU threshold (70%) exceeded
- **Health Monitoring**: Periodic heartbeat and peer discovery
- **Composite Scoring**: CPU (70%) + Latency (30%) combination
- **Redirect Loop Protection**: Prevent infinite redirects with X-Redirect-Count header
- **Load Testing**: Async and thread-based test tools

### 📋 Requirements

- Python 3.9+
- Go 1.21+
- Linux/macOS (Windows WSL2 recommended)

### 🚀 Quick Start

#### 1. Install dependencies

```bash
pip install -r requirements.txt
go mod download
```

#### 2. Start Registry (Terminal 1)

```bash
go run src/registry_server/main.go
```

#### 3. Start Nodes (Terminal 2 and 3)

```bash
python3 src/node_server.py --port 8081
python3 src/node_server.py --port 8082
```

#### 4. Run load test (Terminal 4)

```bash
# Async mode (recommended - high performance)
python3 src/load_test.py --mode async --rate 50

# Or Thread mode (simple)
python3 src/load_test.py --mode thread --rate 50
```

### 📁 Project Structure

```
DiNC/
├── src/
│   ├── registry_server/
│   │   └── main.go              # Go central registry (port 8000)
│   ├── node_server/
│   │   ├── templates/
│   │   │   └── status.html      # Web UI template
│   │   └── static/
│   │       └── css/
│   │           └── style.css    # Cloudflare-inspired theme
│   ├── utils/
│   │   ├── state.py             # Thread-safe state management
│   │   ├── heartbeat.py         # Periodic registry registration
│   │   ├── discovery.py         # Peer discovery and polling
│   │   └── __init__.py
│   ├── node_server.py           # Flask node application
│   └── load_test.py             # Async/Thread-based load test
├── requirements.txt             # Python dependencies
├── go.mod                       # Go module definition
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

### � API Endpoints

#### Registry (port 8000)

- `POST /register` - Register node itself
- `GET /nodes` - List healthy nodes
- `GET /health` - Check registry health

#### Node (port 8081+)

- `GET /` - Main status page (redirects if overloaded)
- `GET /load` - CPU load in JSON format
- `GET /ping` - Heartbeat endpoint
- `GET /health` - Node health status

### ⚙️ Configuration

#### Node CPU Threshold

```bash
python3 src/node_server.py --port 8081 --cpu-threshold 75.0
```

#### Load Test Parameters

```bash
# Async mode
python3 src/load_test.py --mode async --rate 100 --concurrent 200

# Thread mode
python3 src/load_test.py --mode thread --rate 100 --workers 20
```

### 🧪 Testing

#### GitHub Actions

Push or create PR → Monitor workflow in Actions tab

```bash
git push origin main
```

#### Local Testing

```bash
# Health check
curl http://localhost:8081/health

# Load endpoint
curl http://localhost:8081/load

# Ping
curl http://localhost:8082/ping

# Redirect test (max 3 redirects)
curl -L --max-redirs 3 http://localhost:8081/
```

### 🛡️ Redirect Loop Protection

`X-Redirect-Count` header is incremented on each redirect:

- Count < 3: Redirect
- Count ≥ 3: Serve from self (loop protection)

### 📊 Performance Characteristics

| Feature | Value |
|---------|-------|
| Heartbeat Interval | 5 seconds |
| Peer Discovery Interval | 10 seconds |
| Peer Load Polling | 7 seconds |
| Health Check Timeout | 15 seconds |
| Score Formula | `(CPU × 0.7) + (Latency × 0.3)` |
| CPU Threshold | 70% (configurable) |
| Max Redirects | 3 |

### 🚦 Scoring System

Peer selection uses simple metrics:

1. **CPU Load** (%): Node's current CPU usage
2. **Latency** (ms): Request round-trip time
3. **Score**: `(load × 0.7) + (latency × 0.3)`

**Lower score = better peer** ✅

### 🐛 Troubleshooting

#### Cannot connect to Registry

```bash
# Is Registry running?
curl http://localhost:8000/health

# Check if port is open
lsof -i :8000
```

#### Infinite redirect loop

Check HTTP_CODE 307 + X-Redirect-Count header:

```bash
curl -v http://localhost:8081/
```

#### Peers not discovered

```bash
# Check node logs
tail -f /tmp/dinc*.log  # if exists

# Check central registry registration
curl http://localhost:8000/nodes
```

---

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

**DiNC - Dinc is Not Cloudflare**

---

## 👤 Developer

javav12
