"""
src/utils/heartbeat.py - Ana sunucuya periyodik kalp atışı gönderir.
"""
import requests
import threading
import time
import logging

logger = logging.getLogger(__name__)


class Heartbeat:
    """Ana sunucuya periyodik olarak kayıt ve "hayattayım" mesajı gönderir."""
    
    def __init__(self, main_server_addr: str, my_addr: str, interval: int = 5):
        self.main_server_addr = main_server_addr
        self.my_addr = my_addr
        self.interval = interval
    
    def start(self):
        """Heartbeat döngüsünü arka planda başlatır."""
        # İlk kayıt hemen yap
        self._send()
        
        # Sonrasında periyodik olarak gönder
        thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        thread.start()
    
    def _send(self):
        """Ana sunucuya bir heartbeat isteği gönderir."""
        try:
            payload = {"address": self.my_addr}
            response = requests.post(
                f"{self.main_server_addr}/register",
                json=payload,
                timeout=3
            )
            if response.status_code == 200:
                logger.debug(f"Heartbeat gönderildi: {self.my_addr}")
            else:
                logger.warning(f"Heartbeat ana sunucudan hata aldı: {response.status_code}")
        except Exception as e:
            logger.error(f"Heartbeat gönderilemedi: {e}")
    
    def _heartbeat_loop(self):
        """Periyodik olarak heartbeat gönderir."""
        while True:
            time.sleep(self.interval)
            self._send()
