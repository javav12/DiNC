"""
src/utils/state.py - Ağ durumunu thread-safe şekilde yönetir.
"""
import threading
from typing import List, Dict, Optional


class Peer:
    """Ağdaki başka bir sunucunun durumu."""
    
    def __init__(self, address: str):
        self.address = address
        self.load = 0.0          # CPU yükü (%)
        self.latency = 0.0       # Ağ gecikmesi (ms)
        self.score = 9999.0      # Sağlık skoru (düşük daha iyi)
    
    def update_metrics(self, load: float, latency: float):
        """Yük ve gecikme metriklerini günceller ve skoru hesaplar."""
        self.load = load
        self.latency = latency
        # Basit skorlama: %70 yük, %30 gecikme
        self.score = (load * 0.7) + (latency * 0.3)
    
    def to_dict(self):
        """Peer'ı sözlüğe dönüştürür (JSON serializable)."""
        return {
            "address": self.address,
            "load": round(self.load, 2),
            "latency": round(self.latency, 2),
            "score": round(self.score, 2),
        }


class State:
    """Sunucunun bildiği tüm ağ durumunu thread-safe şekilde yönetir."""
    
    def __init__(self, cpu_threshold: float = 70.0):
        self.lock = threading.RLock()
        self.peers: Dict[str, Peer] = {}
        self.cpu_threshold = cpu_threshold  # %70 varsayılan
        self.my_cpu_load = 0.0  # Bu sunucunun CPU yükü
    
    def set_my_cpu_load(self, load: float):
        """Bu sunucunun CPU yükünü ayarla."""
        with self.lock:
            self.my_cpu_load = load
    
    def is_overloaded(self) -> bool:
        """Bu sunucu aşırı yüklü mü?"""
        with self.lock:
            return self.my_cpu_load > self.cpu_threshold
    
    def all_peers(self) -> List[Peer]:
        """Tüm bilinen peer'ları döndürür."""
        with self.lock:
            return list(self.peers.values())
    
    def update_peer_metrics(self, address: str, load: float, latency: float):
        """Bir peer'ın metriklerini günceller."""
        with self.lock:
            if address in self.peers:
                self.peers[address].update_metrics(load, latency)
    
    def set_peers(self, peer_addresses: List[str]):
        """Peer listesini günceller (eski olanları siler, yenilerini ekler)."""
        with self.lock:
            # Yeni peer'ları işaretle
            new_peers_set = set(peer_addresses)
            
            # Yeni peer'ları ekle
            for addr in peer_addresses:
                if addr not in self.peers:
                    self.peers[addr] = Peer(addr)
            
            # Eski peer'ları sil
            to_delete = [addr for addr in self.peers if addr not in new_peers_set]
            for addr in to_delete:
                del self.peers[addr]
    
    def best_peer(self) -> Optional[Peer]:
        """En düşük skora sahip (en sağlıklı) peer'ı döndürür."""
        with self.lock:
            if not self.peers:
                return None
            
            # Sadece metrikleri güncellenenler arasından seç
            valid_peers = [p for p in self.peers.values() if p.load > 0 or p.latency > 0]
            if not valid_peers:
                return None
            
            # En düşük skora sahip olanı döndür
            return min(valid_peers, key=lambda p: p.score)
    
    def get_peer(self, address: str) -> Optional[Peer]:
        """Belirli bir peer'ı adresiyle döndürür."""
        with self.lock:
            return self.peers.get(address)
