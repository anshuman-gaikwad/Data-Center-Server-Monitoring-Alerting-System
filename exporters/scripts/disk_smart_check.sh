#!/usr/bin/env bash
set -u

if ! command -v smartctl >/dev/null 2>&1; then
  echo "smartctl not installed."
  echo "Install with: sudo apt install smartmontools"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo for complete SMART information."
  exit 1
fi

echo "Disk SMART health summary"
echo "--------------------------"

for disk in /dev/sd? /dev/nvme?n1; do
  [ -e "$disk" ] || continue
  echo
  echo "Device: $disk"
  smartctl -H "$disk" 2>/dev/null | grep -E "SMART overall-health|SMART Health Status|result" || true
done
