// src/registry_server/main.go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"
)

// NodeInfo, bir yan sunucunun bilgilerini tutar.
type NodeInfo struct {
	Address   string    `json:"address"`
	LastSeen  time.Time `json:"lastSeen"`
	IsHealthy bool      `json:"isHealthy"`
}

// registry, tüm yan sunucuların kaydını tutan thread-safe bir yapıdır.
var registry = struct {
	sync.RWMutex
	nodes map[string]NodeInfo
}{
	nodes: make(map[string]NodeInfo),
}

// registerHandler, bir yan sunucunun kendini kaydetmesini sağlar.
func registerHandler(w http.ResponseWriter, r *http.Request) {
	var info NodeInfo
	if err := json.NewDecoder(r.Body).Decode(&info); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	registry.Lock()
	info.LastSeen = time.Now()
	info.IsHealthy = true
	registry.nodes[info.Address] = info
	registry.Unlock()

	log.Printf("Node registered/updated: %s", info.Address)
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// listNodesHandler, tüm aktif sunucuların listesini döndürür.
func listNodesHandler(w http.ResponseWriter, r *http.Request) {
	registry.RLock()
	defer registry.RUnlock()

	// Sadece sağlıklı olanları kopyala
	healthyNodes := make([]NodeInfo, 0, len(registry.nodes))
	for _, node := range registry.nodes {
		if node.IsHealthy {
			healthyNodes = append(healthyNodes, node)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(healthyNodes)
}

// healthCheck, periyodik olarak sunucuların durumunu kontrol eder.
func healthCheck() {
	for {
		time.Sleep(10 * time.Second) // Her 10 saniyede bir kontrol et
		registry.Lock()
		for addr, info := range registry.nodes {
			// Eğer bir sunucu 15 saniyeden uzun süredir heartbeat göndermediyse,
			// onu sağlıksız olarak işaretle.
			if time.Since(info.LastSeen) > 15*time.Second {
				info.IsHealthy = false
				registry.nodes[addr] = info
				log.Printf("Node is unhealthy: %s", addr)
			}
		}
		registry.Unlock()
	}
}

func main() {
	// Arka planda sağlık kontrolünü başlat
	go healthCheck()

	http.HandleFunc("/register", registerHandler)
	http.HandleFunc("/nodes", listNodesHandler)

	port := ":8000"
	log.Printf("Registry Server http://localhost%s adresinde başlatılıyor...", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatalf("Registry sunucusu başlatılamadı: %v", err)
	}
}
