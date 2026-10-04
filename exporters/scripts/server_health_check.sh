#!/usr/bin/env bash
set -u

echo "======================================"
echo " Linux Server Health Check"
echo "======================================"
echo "Host:        $(hostname)"
echo "Time:        $(date)"
echo "Uptime:      $(uptime -p)"
echo

echo "[CPU]"
top -bn1 | grep "Cpu(s)" | sed 's/.*, *\([0-9.]*\)%* id.*/\1% idle/' || true

echo
echo "[Memory]"
free -h

echo
echo "[Disk]"
df -h --output=source,size,used,avail,pcent,target | head -n 20

echo
echo "[Load]"
cat /proc/loadavg

echo
echo "[Network]"
ip -br addr 2>/dev/null || true
echo

echo "[Node Exporter]"
if curl -fsS --max-time 2 http://localhost:9100/metrics >/dev/null; then
  echo "Node Exporter: UP"
else
  echo "Node Exporter: DOWN"
fi
