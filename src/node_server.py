"""
src/node_server.py - Yan sunucu (Node).
Merkezi sunucuya kendisini kaydeder, diğer sunucuları keşfeder ve yönlendirir.
Registry düştüğünde A_M_R (Attack Mode Request) P2P ağına geçer.
"""
from flask import Flask, render_template, jsonify, redirect, request
import psutil
import socket
import logging
import sys
import argparse

# Proje modüllerini içe aktar
sys.path.insert(0, "/home/javav12/Belgeler/DiNC/src")
from utils import State, Heartbeat, Discovery, AMRClient, register_a_m_r_routes

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask uygulaması
app = Flask(__name__, 
    template_folder="/home/javav12/Belgeler/DiNC/src/node_server/templates",
    static_folder="/home/javav12/Belgeler/DiNC/src/node_server/static")

# Global durum ve konfigürasyon
state = None
heartbeat = None
discovery = None
my_addr = None
a_m_r = None  # Attack Mode Request P2P client


def get_cpu_load():
    """Anlık CPU yükünü yüzde olarak döndürür."""
    return psutil.cpu_percent(interval=0.5)


@app.route("/", methods=["GET"])
def index():
    """Ana durum sayfası."""
    # Redirect döngüsünü önle: redirect_count header'ını kontrol et
    redirect_count = int(request.headers.get("X-Redirect-Count", 0))
    
    # Çok fazla yönlendirme = döngü, durdurun!
    if redirect_count >= 3:
        logger.warning(f"⚠️  Redirect döngüsü algılandı ({redirect_count} redirects)! Kendime hizmet veriyorum.")
        # Kendisine hizmet ver
    else:
        cpu_load = get_cpu_load()
        
        # State'i güncelle
        state.set_my_cpu_load(cpu_load)
        
        # Eğer bu node aşırı yüklüyse, en iyi peer'a yönlendir
        if state.is_overloaded():
            best_peer = state.best_peer()
            if best_peer and best_peer.address != my_addr:
                logger.info(f"Aşırı yüklü node ({cpu_load:.2f}%), {best_peer.address} adresine yönlendiriliyor (count={redirect_count})")
                
                # Redirect header'ını increment et
                response = redirect(f"{best_peer.address}/", code=307)
                response.headers["X-Redirect-Count"] = str(redirect_count + 1)
                return response
    
    cpu_load = get_cpu_load()
    peers = [p.to_dict() for p in state.all_peers()]
    best = state.best_peer()
    best_peer_info = best.to_dict() if best else None
    
    return render_template("status.html",
        my_addr=my_addr,
        my_load=cpu_load,
        peers=peers,
        best_peer=best_peer_info,
        is_overloaded=state.is_overloaded(),
        threshold=state.cpu_threshold
    )


@app.route("/load", methods=["GET"])
def load():
    """JSON formatında CPU yükünü döndürür."""
    cpu_load = get_cpu_load()
    return jsonify({
        "address": my_addr,
        "cpuLoad": round(cpu_load, 2)
    }), 200


@app.route("/redirect", methods=["GET"])
def redirect_to_best():
    """
    İsteği en sağlıklı peer'a yönlendirir.
    Hiç peer yoksa kendisine hizmet ver.
    """
    best_peer = state.best_peer()
    if best_peer:
        # Eğer kendisi en iyiyse, kendisine servis ver
        if best_peer.address == my_addr:
            return jsonify({"redirected_to": my_addr, "message": "Ben en iyiyim!"}), 200
        else:
            # Diğer peer'a yönlendir
            return redirect(f"{best_peer.address}/", code=307)
    else:
        # Hiç peer yoksa kendisini döndür
        return jsonify({"redirected_to": my_addr, "message": "Başka sunucu yok."}), 200


@app.route("/health", methods=["GET"])
def health():
    """Node'un sağlığını kontrol etmek için."""
    return jsonify({"status": "healthy"}), 200


@app.route("/ping", methods=["GET"])
def ping():
    """Load test tarafından istekleri algılamak için kullanılan endpoint."""
    return jsonify({"status": "pong", "address": my_addr}), 200


def initialize(port, main_server, cpu_threshold=70.0):
    """Node'u başlat ve arka plan görevlerini tetikle."""
    global state, heartbeat, discovery, my_addr, a_m_r
    
    # Konfigürasyonu ayarla
    hostname = socket.gethostname()
    my_addr = f"http://{hostname}:{port}"
    
    logger.info(f"Node başlatılıyor: {my_addr}")
    logger.info(f"Ana Sunucu: {main_server}")
    logger.info(f"CPU Eşiği: {cpu_threshold}%")
    
    # State, Heartbeat ve Discovery'i oluştur
    state = State(cpu_threshold=cpu_threshold)
    heartbeat = Heartbeat(main_server, my_addr, interval=5)
    discovery = Discovery(state, main_server, my_addr, interval=10)
    
    # A_M_R (Attack Mode Request) P2P client'ı oluştur
    a_m_r = AMRClient(my_addr, known_peers=[])
    register_a_m_r_routes(app, a_m_r)
    logger.info("✓ A_M_R (P2P fallback) kuruldu")
    
    # Arka plan görevlerini başlat
    heartbeat.start()
    logger.info("✓ Heartbeat başlatıldı")
    
    discovery.start()
    logger.info("✓ Peer keşfi başlatıldı")
    
    discovery.poll_peer_loads(interval=7)
    logger.info("✓ Peer yükü sorgulaması başlatıldı")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DiNC - Yan Sunucu (Node)")
    parser.add_argument("--port", type=str, default="8081", help="Sunucunun portu")
    parser.add_argument("--main-server", type=str, default="http://localhost:8000", help="Merkezi sunucunun adresi")
    parser.add_argument("--cpu-threshold", type=float, default=70.0, help="CPU eşiği (%)")
    
    args = parser.parse_args()
    
    # Node'u başlat
    initialize(args.port, args.main_server, args.cpu_threshold)
    
    print()
    print("=" * 60)
    print("DiNC - Yan Sunucu (Node)")
    print("=" * 60)
    print(f"Node Adresi: {my_addr}")
    print(f"Ana Sunucu: {args.main_server}")
    print(f"Web Arayüzü: http://localhost:{args.port}")
    print("=" * 60)
    print()
    
    # Flask uygulamasını başlat
    app.run(host="0.0.0.0", port=int(args.port), debug=False)
