# DiNC - Distributed Node Coordinator

Yüksek kullanılabilirlik ve otomatik yük dengeleme ile dağıtılmış sistem mimarisi.

## 🎯 Özellikler

- **Dağıtılmış Mimari**: Go tabanlı merkezi registry + Python node'lar
- **Otomatik Yük Dengeleme**: CPU eşiği (%70) aşınca peer'a yönlendir
- **Sağlık Kontrolü**: Periyodik heartbeat ve peer discovery
- **Composite Scoring**: CPU (70%) + Latency (30%) kombinasyonu
- **Redirect Loop Koruması**: X-Redirect-Count header ile sonsuz döngü engelle
- **Load Testing**: Async ve thread tabanlı test araçları
- **CI/CD Entegrasyonu**: GitHub Actions workflow

## 📋 Gereksinimler

- Python 3.9+
- Go 1.21+
- Linux/macOS (Windows WSL2 önerilir)

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
go mod download
```

### 2. Registry'i başlat (Node 1)

```bash
go run src/registry_server/main.go
```

### 3. Node'ları başlat (Node 2 ve 3)

```bash
python3 src/node_server.py --port 8081
python3 src/node_server.py --port 8082
```

### 4. Load test çalıştır (Terminal)

```bash
# Async mode (önerilen - yüksek performans)
python3 src/load_test.py --mode async --rate 50

# Veya Thread mode (basit)
python3 src/load_test.py --mode thread --rate 50
```

## 📁 Proje Yapısı

```
DiNC/
├── .github/
│   └── workflows/
│       └── test.yml              # GitHub Actions CI/CD
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

## 🔌 API Endpoints

### Registry (port 8000)

- `POST /register` - Node kendisini kaydet
- `GET /nodes` - Sağlıklı node'ları listele
- `GET /health` - Registry'nin sağlığını kontrol et

### Node (port 8081+)

- `GET /` - Ana durum sayfası (yüklü ise yönlendir)
- `GET /load` - JSON formatında CPU yükü
- `GET /ping` - Heartbeat endpoint'i
- `GET /health` - Node sağlığı

## ⚙️ Konfigürasyon

### Node CPU Eşiği

```bash
python3 src/node_server.py --port 8081 --cpu-threshold 75.0
```

### Load Test Parametreleri

```bash
# Async mode
python3 src/load_test.py --mode async --rate 100 --concurrent 200

# Thread mode
python3 src/load_test.py --mode thread --rate 100 --workers 20
```

### Lokal Test

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

## 🛡️ Redirect Loop Koruması

Her yönlendirmede `X-Redirect-Count` header'ı arttırılır:

- Count < 3: Yönlendir
- Count ≥ 3: Kendine hizmet ver (döngü engeli)

## 📊 Performans Özellikleri

| Özellik | Değer |
|---------|-------|
| Heartbeat Interval | 5 saniye |
| Peer Discovery Interval | 10 saniye |
| Peer Load Polling | 7 saniye |
| Health Check Timeout | 15 saniye |
| Score Formula | `(CPU × 0.7) + (Latency × 0.3)` |
| CPU Threshold | 70% (konfigüre edilebilir) |
| Max Redirects | 3 |

## 🚦 Scoring Sistemi

Peer seçimi basit metrikler kullanır:

1. **CPU Yükü** (%): Node'un mevcut CPU kullanımı
2. **Latency** (ms): İsteğin gidiş-dönüş süresi
3. **Score**: `(load × 0.7) + (latency × 0.3)`

**Düşük score = daha iyi peer** ✅

## 🐛 Hata Giderme

### Registry'ye bağlanamıyorum

```bash
# Registry çalışıyor mu?
curl http://localhost:8000/health

# Portun açık olup olmadığını kontrol et
lsof -i :8000
```

### Sonsuz redirect döngüsü

HTTP_CODE 307 + X-Redirect-Count header'ını kontrol et:

```bash
curl -v http://localhost:8081/
```

### Peer'lar keşfedilmiyor

```bash
# Node loglarını kontrol et
tail -f /tmp/dinc*.log  # varsa

# Merkezi sunucuya kayıt kontrolü
curl http://localhost:8000/nodes
```

## 📝 Lisans

GPL

## 👤 Geliştirici
javav12




DiNC - Dinc is Not Cloudflare
