"""
src/load_test.py - Otomatik Load Test Orchestrator (Async + Thread Hybrid)
8081'e istek atar, 8082 tarafında bir paket geldiğinde otomatik durur.

Kullanım:
  python3 src/load_test.py --rate 50 --mode async
  python3 src/load_test.py --rate 50 --mode thread
"""
import requests
import threading
import time
import logging
import asyncio
from datetime import datetime

# Async mode için aiohttp'i isteğe bağlı yükle
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoadTestThread:
    """Thread tabanlı load test (yüksek concurrency için)."""
    
    def __init__(self, attack_target="http://localhost:8081", 
                 finish_detector="http://localhost:8082",
                 request_rate=50, workers=10):
        self.attack_target = attack_target
        self.finish_detector = finish_detector
        self.request_rate = request_rate
        self.workers = workers
        
        self.running = False
        self.requests_sent = 0
        self.requests_failed = 0
        self.requests_to_finish = 0
        self.start_time = None
        self.threads = []
        self.lock = threading.Lock()
    
    def send_request(self):
        """Tek bir isteği gönder."""
        try:
            response = requests.get(self.attack_target, timeout=2)
            with self.lock:
                self.requests_sent += 1
            logger.debug(f"  ➜ Istek #{self.requests_sent}: {response.status_code}")
        except Exception as e:
            with self.lock:
                self.requests_failed += 1
            logger.debug(f"  ✗ Istek hatası: {e}")
    
    def worker_loop(self, requests_per_worker):
        """Her worker belirli sayıda istek gönderir."""
        for _ in range(requests_per_worker):
            if not self.running:
                break
            self.send_request()
    
    def attack_loop(self):
        """Periyodik olarak worker thread'ler oluştur."""
        logger.info(f"🎯 Attack başladı: {self.attack_target} ({self.request_rate} req/sec, {self.workers} workers)")
        
        while self.running:
            requests_per_worker = max(1, self.request_rate // self.workers)
            
            # Worker thread'ler oluştur
            worker_threads = []
            for _ in range(self.workers):
                t = threading.Thread(target=self.worker_loop, args=(requests_per_worker,), daemon=True)
                t.start()
                worker_threads.append(t)
            
            # Tüm worker'ları bekle
            for t in worker_threads:
                t.join(timeout=1.0)
            
            time.sleep(1.0)
    
    def detect_finish(self):
        """8082'den paket algılaması yapıyor."""
        logger.info(f"🔍 Finish detector başladı: {self.finish_detector}")
        
        while self.running:
            try:
                response = requests.get(f"{self.finish_detector}/ping", timeout=2)
                if response.status_code == 200:
                    with self.lock:
                        self.requests_to_finish += 1
                    logger.info(f"✨ 8082'de paket algılandı! (Toplam: {self.requests_to_finish})")
                    
                    # Birinci paket geldiğinde durma sinyali
                    if self.requests_to_finish >= 1:
                        logger.info("🛑 BITIŞE ULAŞILDI! Test otomatik sonlanıyor...")
                        self.running = False
                        break
            except Exception as e:
                logger.debug(f"  Detector: {e}")
            
            time.sleep(0.5)
    
    def start(self):
        """Attack ve detection'ı başlatır."""
        if self.running:
            logger.warning("Test zaten çalışıyor!")
            return
        
        self.running = True
        self.requests_sent = 0
        self.requests_failed = 0
        self.requests_to_finish = 0
        self.start_time = time.time()
        
        # Threads'i başlat
        attack_thread = threading.Thread(target=self.attack_loop, daemon=True)
        detector_thread = threading.Thread(target=self.detect_finish, daemon=True)
        
        attack_thread.start()
        detector_thread.start()
        
        self.threads = [attack_thread, detector_thread]
        
        logger.info("=" * 60)
        logger.info("TEST BAŞLATILDI (THREAD MODE)")
        logger.info("=" * 60)
    
    def wait_for_finish(self):
        """Test bitene kadar bekle."""
        while self.running:
            time.sleep(0.1)
    
    def stop(self):
        """Testi manuel durdur."""
        self.running = False
        for t in self.threads:
            t.join(timeout=2)
    
    def report(self):
        """Test raporunu yazdır."""
        elapsed = time.time() - self.start_time
        rate = self.requests_sent / elapsed if elapsed > 0 else 0
        
        print()
        print("=" * 60)
        print("TEST RAPORU (THREAD MODE)")
        print("=" * 60)
        print(f"⏱️  Süre: {elapsed:.2f} saniye")
        print(f"📤 8081'e gönderilen istekler: {self.requests_sent}")
        print(f"❌ Başarısız istekler: {self.requests_failed}")
        print(f"📥 8082'den algılanan paketler: {self.requests_to_finish}")
        print(f"📊 Ortalama hız: {rate:.2f} req/sec")
        print("=" * 60)
        print()


class LoadTestAsync:
    """Async tabanlı load test (en yüksek performans)."""
    
    def __init__(self, attack_target="http://localhost:8081", 
                 finish_detector="http://localhost:8082",
                 request_rate=50, concurrent=100):
        if not HAS_AIOHTTP:
            raise ImportError("Async mode için 'pip install aiohttp' çalıştırın")
        
        self.attack_target = attack_target
        self.finish_detector = finish_detector
        self.request_rate = request_rate
        self.concurrent = concurrent
        
        self.running = False
        self.requests_sent = 0
        self.requests_failed = 0
        self.requests_to_finish = 0
        self.start_time = None
        self.lock = asyncio.Lock()
    
    async def send_request(self, session):
        """Async isteği gönder."""
        try:
            async with session.get(self.attack_target, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 200:
                    self.requests_sent += 1
                    logger.debug(f"  ➜ Istek #{self.requests_sent}")
        except Exception as e:
            self.requests_failed += 1
            logger.debug(f"  ✗ Istek hatası: {e}")
    
    async def attack_loop(self):
        """Async attack loop - belirtilen rate'te istek gönder."""
        logger.info(f"🎯 Attack başladı: {self.attack_target} ({self.request_rate} req/sec, concurrent={self.concurrent})")
        
        async with aiohttp.ClientSession() as session:
            while self.running:
                tasks = []
                
                # Her saniyede request_rate kadar istek oluştur
                for _ in range(self.request_rate):
                    if not self.running:
                        break
                    tasks.append(self.send_request(session))
                    
                    # Concurrency limitini kontrol et
                    if len(tasks) >= self.concurrent:
                        await asyncio.gather(*tasks)
                        tasks = []
                
                # Kalan taskları bitmesini bekle
                if tasks:
                    await asyncio.gather(*tasks)
                
                await asyncio.sleep(1.0)
    
    async def detect_finish(self):
        """Async finish detection."""
        logger.info(f"🔍 Finish detector başladı: {self.finish_detector}")
        
        async with aiohttp.ClientSession() as session:
            while self.running:
                try:
                    async with session.get(f"{self.finish_detector}/ping", timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            self.requests_to_finish += 1
                            logger.info(f"✨ 8082'de paket algılandı! (Toplam: {self.requests_to_finish})")
                            
                            if self.requests_to_finish >= 1:
                                logger.info("🛑 BITIŞE ULAŞILDI! Test otomatik sonlanıyor...")
                                self.running = False
                                return
                except Exception as e:
                    logger.debug(f"  Detector: {e}")
                
                await asyncio.sleep(0.5)
    
    async def start_async(self):
        """Attack ve detection'ı paralel olarak başlatır."""
        self.running = True
        self.requests_sent = 0
        self.requests_failed = 0
        self.requests_to_finish = 0
        self.start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("TEST BAŞLATILDI (ASYNC MODE)")
        logger.info("=" * 60)
        
        # Attack ve detection'ı paralel çalıştır
        await asyncio.gather(
            self.attack_loop(),
            self.detect_finish()
        )
    
    def start(self):
        """Async event loop'unu başlat."""
        asyncio.run(self.start_async())
    
    def report(self):
        """Test raporunu yazdır."""
        elapsed = time.time() - self.start_time
        rate = self.requests_sent / elapsed if elapsed > 0 else 0
        
        print()
        print("=" * 60)
        print("TEST RAPORU (ASYNC MODE)")
        print("=" * 60)
        print(f"⏱️  Süre: {elapsed:.2f} saniye")
        print(f"📤 8081'e gönderilen istekler: {self.requests_sent}")
        print(f"❌ Başarısız istekler: {self.requests_failed}")
        print(f"📥 8082'den algılanan paketler: {self.requests_to_finish}")
        print(f"📊 Ortalama hız: {rate:.2f} req/sec")
        print("=" * 60)
        print()



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DiNC Load Test - 8081 Attack → 8082 Finish")
    parser.add_argument("--rate", type=int, default=50, help="İstek/saniye (varsayılan: 50)")
    parser.add_argument("--mode", type=str, choices=["async", "thread"], default="async", 
                       help="Mode: async (yüksek perf) ya da thread (basit)")
    parser.add_argument("--workers", type=int, default=10, help="Thread mode'da worker sayısı")
    parser.add_argument("--concurrent", type=int, default=100, help="Async mode'da concurrent istek sayısı")
    args = parser.parse_args()
    
    # Mode'a göre test oluştur
    if args.mode == "async":
        test = LoadTestAsync(request_rate=args.rate, concurrent=args.concurrent)
    else:
        test = LoadTestThread(request_rate=args.rate, workers=args.workers)
    
    try:
        test.start()
        if args.mode == "thread":
            test.wait_for_finish()
    except KeyboardInterrupt:
        logger.info("⌨️  Kullanıcı tarafından durduruldu")
    finally:
        if args.mode == "thread":
            test.stop()
        test.report()
