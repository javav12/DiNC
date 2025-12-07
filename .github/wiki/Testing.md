# Testing

## 🧪 Test Senaryoları

### Setup: Full Network

**Terminal 1 - Registry:**
```bash
go run src/registry_server/main.go
```

**Terminal 2-4 - Nodes:**
```bash
python3 src/node_server.py --port 8081
python3 src/node_server.py --port 8082
python3 src/node_server.py --port 8083
```

---

## 🔍 Test 1: Basic Health Check

```bash
# Registry health
curl http://localhost:8000/health

# Node health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

Expected: `{"status": "healthy"}`

---

## 📊 Test 2: Load Monitoring

```bash
# Node 1 load
curl http://localhost:8081/load

# Node 2 load
curl http://localhost:8082/load

# Node 3 load
curl http://localhost:8083/load
```

Expected: CPU load values

---

## 🔄 Test 3: Redirect Loop Protection

```bash
# Follow redirects (max 3)
curl -L --max-redirs 3 -v http://localhost:8081/

# Should not loop infinitely
# Should show X-Redirect-Count header
```

---

## 🎯 Test 4: Load Testing

### Async Mode (High Performance)

```bash
python3 src/load_test.py --mode async --rate 100 --concurrent 200
```

Monitor in another terminal:
```bash
watch -n 1 'curl -s http://localhost:8081/load'
```

### Thread Mode (Simple)

```bash
python3 src/load_test.py --mode thread --rate 50 --workers 10
```

---

## 🔴 Test 5: A_M_R Fallback

### Manual Trigger

```bash
# 1. Start A_M_R manually
curl -X POST http://localhost:8081/a_m_r/activate

# 2. Check status
curl http://localhost:8081/a_m_r/status

# 3. Get botlist
curl http://localhost:8081/a_m_r/botlist

# 4. Monitor sync
for i in {1..10}; do
  echo "=== Iteration $i ==="
  curl -s http://localhost:8081/a_m_r/botlist | jq '.count'
  sleep 2
done
```

### Automatic Trigger (Registry Failure)

```bash
# 1. Kill registry
killall go

# 2. Wait 10 seconds (heartbeat timeout)

# 3. Check A_M_R activated
curl http://localhost:8081/a_m_r/status

# 4. Nodes should be syncing
curl http://localhost:8081/a_m_r/botlist

# 5. Restart registry
go run src/registry_server/main.go

# 6. A_M_R should deactivate
```

---

## 📈 Test 6: Stress Testing

```bash
# High load
python3 src/load_test.py --mode async --rate 500 --concurrent 1000

# Monitor all nodes
while true; do
  echo "=== Node 1 ==="
  curl -s http://localhost:8081/load | jq '.cpuLoad'
  echo "=== Node 2 ==="
  curl -s http://localhost:8082/load | jq '.cpuLoad'
  sleep 1
done
```

Expected: Load balanced across nodes, some redirects

---

## 🧬 Test 7: Peer Discovery

```bash
# Get registry's node list
curl http://localhost:8000/nodes | jq .

# Should show all 3 nodes registered
```

---

## ✅ Checklist

- [ ] All health checks pass
- [ ] Load monitoring works
- [ ] Redirects don't loop
- [ ] Load test completes
- [ ] A_M_R activates on registry failure
- [ ] Stress test distributes load

Hazır! 🚀
