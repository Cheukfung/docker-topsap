#!/bin/bash
set -Eeuo pipefail
cd "$TOPSAP_DIR"
./sv_websrv > /tmp/sdk.log 2>&1 &
sdk_pid=$!
cleanup() {
    if kill -0 "$sdk_pid" 2>/dev/null; then
        kill "$sdk_pid"
    fi
    wait
}
trap cleanup EXIT
for ((i=0; i<30; i++)); do
    kill -0 "$sdk_pid"
    if [[ -S /tmp/TopSAP_ELE/topsap.sock ]]; then break; fi
    sleep 1
done
if ! python3 /home/work/topsap.py probe; then
    cat /tmp/sdk.log
    exit 1
fi
# No VPN credentials in CI: create an isolated TUN fixture for Dante's external
# interface validation. This does not simulate a VPN connection.
ip tuntap add dev tun0 mode tun
ip address add 192.0.2.1/32 dev tun0
ip link set dev tun0 up
if ! /usr/sbin/danted -V -f /etc/danted.conf; then
    exit 1
fi
echo 'Native SDK and SOCKS5 configuration smoke test passed'
