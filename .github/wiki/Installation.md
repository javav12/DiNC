# Installation

## 📦 Kurulum Adımları

### Ön Gereksinimler

- **Go**: 1.21 veya üzeri
- **Python**: 3.9 veya üzeri
- **pip**: Python paket yöneticisi
- **git**: Sürüm kontrolü

### Kontrolü

```bash
go version    # Go 1.21+
python3 --version  # Python 3.9+
pip --version      # pip var mı?
git --version      # git var mı?
```

---

## 🚀 Step-by-Step

### 1. Repository'yi Clone Et

```bash
git clone https://github.com/javav12/DiNC.git
cd DiNC
```

### 2. Python Bağımlılıklarını Yükle

```bash
# Virtual environment (opsiyonel ama önerilen)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# veya
venv\Scripts\activate  # Windows

# Paketleri yükle
pip install -r requirements.txt
```

### 3. Go Bağımlılıklarını İndir

```bash
go mod download
```

### 4. Yüklemeyi Doğrula

```bash
# Python
python3 -c "from src.utils import AMRClient; print('✅ DiNC ready')"

# Go
go run src/registry_server/main.go --help
```

---

## 🐳 Docker ile Kurulum (Opsiyonel)

```bash
# Dockerfile oluştur
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
CMD ["python3", "src/node_server.py", "--port", "8081"]
EOF

# Image oluştur
docker build -t dinc:latest .

# Container başlat
docker run -p 8081:8081 dinc:latest
```

---

## 📋 Kontrol Listesi

- [ ] Go 1.21+ yüklü mü?
- [ ] Python 3.9+ yüklü mü?
- [ ] Repository klonlandı mı?
- [ ] `requirements.txt` yüklendi mi?
- [ ] `go mod download` çalıştırıldı mı?
- [ ] Test çalıştırıldı mı?

---

## 🔗 Sonraki Adımlar

- [[Quick Start|Quick-Start]] - Hızlı başlangıç
- [[Architecture|Architecture]] - Sistem mimarisi
- [[Testing|Testing]] - Test etme

Başlamaya hazır mısın? 🚀
