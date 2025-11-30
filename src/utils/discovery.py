"""
src/utils/discovery.py - Sunucu keşfi ve peer iletişimi.
"""
import requests
import threading
import time
import logging
from typing import List
from .state import State

logger = logging.getLogger(__name__)


class Discovery:
    """Ana sunucudan peer listesi alır ve onlarla haberleşir."""
    
    def __init__(self, state: State, main_server_addr: str, my_addr: str, interval: int = 10):
        self.state = state
        self.main_server_addr = main_server_addr
        self.my_addr = my_addr
        self.interval = interval
    
    def start(self):
        """Peer keşfi döngüsünü arka planda başlatır."""
        thread = threading.Thread(target=self._discovery_loop, daemon=True)
        thread.start()
    
    def _discovery_loop(self):
        """Periyodik olarak ana sunucudan peer listesini alır."""
        while True:
            try:
                response = requests.get(f"{self.main_server_addr}/nodes", timeout=5)
                if response.status_code == 200:
                    nodes = response.json()
                    # Kendi adresimizi hariç tut
                    peer_addrs = [n.get("address") for n in nodes if n.get("address") != self.my_addr]
                    self.state.set_peers(peer_addrs)
                    logger.info(f"Keşfedilen peer'lar: {peer_addrs}")
            except Exception as e:
                logger.error(f"Peer keşfi başarısız: {e}")
            
            time.sleep(self.interval)
    
    def fetch_peer_load(self, peer_addr: str) -> tuple[float, float]:
        """
        Bir peer'dan CPU yükünü ve gecikmesini alır.
        Dönüş: (load, latency_ms)
        """
        try:
            start_time = time.time()
            response = requests.get(f"{peer_addr}/load", timeout=3)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                load = data.get("cpuLoad", 0.0)
                return load, latency_ms
        except Exception as e:
            logger.debug(f"Peer yükü alınamadı ({peer_addr}): {e}")
        
        return 0.0, 0.0
    
    def poll_peer_loads(self, interval: int = 7):
        """Periyodik olarak tüm peer'ların yüklerini sorgulamaya başlar."""
        def _poll_loop():
            while True:
                peers = self.state.all_peers()
                for peer in peers:
                    load, latency = self.fetch_peer_load(peer.address)
                    if load > 0 or latency > 0:
                        self.state.update_peer_metrics(peer.address, load, latency)
                
                time.sleep(interval)
        
        thread = threading.Thread(target=_poll_loop, daemon=True)
        thread.start()
