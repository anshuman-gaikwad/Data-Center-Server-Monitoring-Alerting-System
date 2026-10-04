#!/usr/bin/env bash
set -e

VERSION="1.9.0"
ARCH="linux-amd64"
USER_NAME="node_exporter"

echo "Installing Node Exporter ${VERSION}..."

sudo useradd --no-create-home --shell /usr/sbin/nologin ${USER_NAME} 2>/dev/null || true

cd /tmp
curl -LO "https://github.com/prometheus/node_exporter/releases/download/v${VERSION}/node_exporter-${VERSION}.${ARCH}.tar.gz"
tar xvf "node_exporter-${VERSION}.${ARCH}.tar.gz"
sudo cp "node_exporter-${VERSION}.${ARCH}/node_exporter" /usr/local/bin/

sudo tee /etc/systemd/system/node_exporter.service >/dev/null <<EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=${USER_NAME}
Group=${USER_NAME}
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
sudo systemctl status node_exporter --no-pager

echo
echo "Node Exporter is available on port 9100."
