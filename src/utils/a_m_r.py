"""
src/utils/a_m_r.py - Attack Mode Request (A_M_R)
Registry düştüğünde node'lar P2P ağ kurarak birbirlerine bilgi paylaşır.

Modülü:
- botlist_share: Aktif node'ları paylaş
- peer_discovery: Registry olmadan node keşfi
- state_sync: Durumları senkronize et
"""
import threading
import time
import requests
import logging
from typing import List, Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AMRClient:
    """Attack Mode Request - P2P node iletişimi"""
    
    def __init__(self, my_address: str, known_peers: List[str] = None):
        """
        Args:
            my_address: Bu node'un adresi (http://host:port)
            known_peers: Bilinen peer'ların adresleri
        """
        self.my_address = my_address
        self.active_peers: Set[str] = set(known_peers or [])
        self.active_peers.discard(my_address)  # Kendisini çıkar
        
        self.lock = threading.RLock()
        self.running = False
        self.threads: List[threading.Thread] = []
        
        logger.info(f"🔴 A_M_R initialized for {my_address}")
    
    def start(self, interval: int = 5):
        """P2P keşfi başlat"""
        if self.running:
            logger.warning("A_M_R already running")
            return
        
        self.running = True
        logger.info(f"🔴 A_M_R mode ACTIVATED (interval={interval}s)")
        
        # P2P botlist polling thread'i
        thread = threading.Thread(
            target=self._botlist_sync_loop,
            args=(interval,),
            daemon=True
        )
        thread.start()
        self.threads.append(thread)
        
        # P2P health check thread'i
        health_thread = threading.Thread(
            target=self._peer_health_loop,
            args=(interval * 2,),
            daemon=True
        )
        health_thread.start()
        self.threads.append(health_thread)
    
    def stop(self):
        """P2P modunu durdur"""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=2)
        logger.info("🟢 A_M_R mode DEACTIVATED")
    
    def add_peer(self, peer_address: str):
        """Yeni peer ekle"""
        if peer_address != self.my_address:
            with self.lock:
                self.active_peers.add(peer_address)
            logger.info(f"➕ Peer eklendi: {peer_address}")
    
    def get_active_peers(self) -> List[str]:
        """Aktif peer'ları döndür"""
        with self.lock:
            return list(self.active_peers)
    
    def _botlist_sync_loop(self, interval: int):
        """
        Periyodik olarak peer'lardan botlist (aktif node listesi) al.
        Her peer'ın bildiği node'ları toplayıp birleştir.
        """
        logger.info("🤖 Botlist sync loop başladı")
        
        while self.running:
            try:
                peers = self.get_active_peers()
                
                for peer_addr in peers[:]:  # Copy üzerinde iterate et
                    if not self.running:
                        break
                    
                    try:
                        # Peer'ın botlist'ini iste
                        response = requests.get(
                            f"{peer_addr}/a_m_r/botlist",
                            timeout=3
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            botlist = data.get("peers", [])
                            
                            # Yeni peer'ları ekle
                            for new_peer in botlist:
                                if new_peer not in self.active_peers:
                                    self.add_peer(new_peer)
                            
                            logger.debug(f"📋 {peer_addr} -> {len(botlist)} peer")
                    except Exception as e:
                        logger.debug(f"❌ Botlist error ({peer_addr}): {e}")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Botlist sync error: {e}")
                time.sleep(interval)
    
    def _peer_health_loop(self, interval: int):
        """
        Periyodik olarak peer'ların sağlığını kontrol et.
        Ölü peer'ları listeden çıkar.
        """
        logger.info("❤️  Peer health check loop başladı")
        
        while self.running:
            try:
                peers = self.get_active_peers()
                dead_peers = []
                
                for peer_addr in peers:
                    try:
                        response = requests.get(
                            f"{peer_addr}/health",
                            timeout=2
                        )
                        
                        if response.status_code != 200:
                            dead_peers.append(peer_addr)
                    except:
                        dead_peers.append(peer_addr)
                
                # Ölü peer'ları çıkar
                with self.lock:
                    for dead_peer in dead_peers:
                        if dead_peer in self.active_peers:
                            self.active_peers.discard(dead_peer)
                            logger.warning(f"💀 Dead peer removed: {dead_peer}")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(interval)
    
    def get_stats(self) -> Dict:
        """A_M_R durumunu rapor et"""
        peers = self.get_active_peers()
        return {
            "mode": "A_M_R",
            "status": "active" if self.running else "inactive",
            "my_address": self.my_address,
            "active_peers_count": len(peers),
            "active_peers": peers,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Flask Integration - Node'a eklemek için
# ============================================================================

def register_a_m_r_routes(app, a_m_r_client: AMRClient):
    """
    Flask app'a A_M_R route'larını ekle
    
    Usage:
        a_m_r = AMRClient(my_address, initial_peers)
        register_a_m_r_routes(app, a_m_r)
    """
    
    @app.route("/a_m_r/status", methods=["GET"])
    def a_m_r_status():
        """A_M_R modunun durumunu döndür"""
        from flask import jsonify
        return jsonify(a_m_r_client.get_stats()), 200
    
    @app.route("/a_m_r/botlist", methods=["GET"])
    def a_m_r_botlist():
        """Bu node'un bildiği aktif peer'ları döndür"""
        from flask import jsonify
        peers = a_m_r_client.get_active_peers()
        return jsonify({
            "address": a_m_r_client.my_address,
            "peers": peers,
            "count": len(peers),
            "timestamp": datetime.now().isoformat()
        }), 200
    
    @app.route("/a_m_r/sync", methods=["POST"])
    def a_m_r_sync():
        """Dış kaynaktan peer'ları senkronize et"""
        from flask import request, jsonify
        
        try:
            data = request.get_json()
            new_peers = data.get("peers", [])
            
            added = 0
            for peer in new_peers:
                if peer != a_m_r_client.my_address:
                    a_m_r_client.add_peer(peer)
                    added += 1
            
            return jsonify({
                "status": "synced",
                "added": added,
                "total_peers": len(a_m_r_client.get_active_peers())
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    @app.route("/a_m_r/activate", methods=["POST"])
    def a_m_r_activate():
        """A_M_R modunu manuel başlat (registry düştüğünde otomatik olur)"""
        from flask import jsonify
        
        a_m_r_client.start(interval=5)
        return jsonify({
            "status": "activated",
            "message": "A_M_R mode is now active (P2P)",
            "peers": a_m_r_client.get_active_peers()
        }), 200
    
    @app.route("/a_m_r/deactivate", methods=["POST"])
    def a_m_r_deactivate():
        """A_M_R modunu durdur (registry geri geldiğinde)"""
        from flask import jsonify
        
        a_m_r_client.stop()
        return jsonify({
            "status": "deactivated",
            "message": "A_M_R mode is now inactive"
        }), 200


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Basit test
    a_m_r = AMRClient(
        my_address="http://localhost:8081",
        known_peers=[
            "http://localhost:8082",
            "http://localhost:8083"
        ]
    )
    
    print("Initial peers:", a_m_r.get_active_peers())
    print("Stats:", a_m_r.get_stats())
    print("\n✅ A_M_R modülü çalışıyor!")
