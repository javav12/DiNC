# Quick Start

## 5 Dakikada Başla

### 1️⃣ Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt
go mod download

# Opsiyonel: Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Registry Başlat (Terminal 1)

```bash
go run src/registry_server/main.go
```

Çıktı:
```
Registry server running on :8000
Health check interval: 15s
```

### 3️⃣ Node'ları Başlat (Terminal 2 & 3)

```bash
# Node 1
python3 src/node_server.py --port 8081

# Node 2
python3 src/node_server.py --port 8082
```

### 4️⃣ Web Arayüzüne Erişim

- Node 1: http://localhost:8081
- Node 2: http://localhost:8082

### 5️⃣ Load Test Çalıştır (Terminal 4)

```bash
# Async mode (önerilen)
python3 src/load_test.py --mode async --rate 50

# Veya Thread mode
python3 src/load_test.py --mode thread --rate 50
```

---

## 📊 Beklenen Çıktı

```
✓ Registry: http://localhost:8000
✓ Node 1: http://localhost:8081 (CPU: 12%)
✓ Node 2: http://localhost:8082 (CPU: 15%)
✓ Load test: 50 req/sec
```

---

## 🔧 Yapılandırma

### Node CPU Eşiği Değiştir

```bash
python3 src/node_server.py --port 8081 --cpu-threshold 80.0
```

### Load Test Hızını Ayarla

```bash
# 100 req/sec, 200 concurrent
python3 src/load_test.py --mode async --rate 100 --concurrent 200
```

---

## 🆘 Sorun Giderme

### Registry'ye bağlantı kuramıyorum

```bash
# Registry çalışıyor mu?
curl http://localhost:8000/health

# Port açık mı?
lsof -i :8000
```

### Node'lar başlamıyor

```bash
# Python sürümünü kontrol et
python3 --version  # 3.9+ olmalı

# Bağımlılıkları kontrol et
pip list | grep Flask
```

### Port zaten kullanımda

```bash
# Port'u boşalt
lsof -i :8081 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

---

## ✅ Kontrol Listesi

- [ ] Go 1.21+ yüklü mü?
- [ ] Python 3.9+ yüklü mü?
- [ ] requirements.txt yüklü mü?
- [ ] go.mod download yapıldı mı?
- [ ] Registry başladı mı?
- [ ] Node'lar başladı mı?
- [ ] Web arayüzü erişilebilir mi?

Tamamlandı! Şimdi [[Testing]] kısmına geçebilirsin. 🚀
