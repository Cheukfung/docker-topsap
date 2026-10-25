#!/bin/bash
set -Eeuo pipefail
iptables --version | grep -F "(legacy)"
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
cd "$TOPSAP_DIR"
./sv_websrv > /tmp/sdk.log 2>&1 &
sdk_pid=$!
proxy_pid=
cleanup() {
    if [[ -n "$proxy_pid" ]] && kill -0 "$proxy_pid" 2>/dev/null; then
        kill "$proxy_pid"
    fi
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
# No VPN credentials in CI: create a TUN fixture for configuration validation.
# This does not simulate a VPN connection.
ip tuntap add dev tun0 mode tun
ip address add 192.0.2.1/32 dev tun0
ip link set dev tun0 up
sing-box check -c /etc/sing-box.json
# Only the transfer fixture uses loopback; production binds its egress to tun0.
sed 's/"tun0"/"lo"/' /etc/sing-box.json > /tmp/sing-box-test.json
sing-box run -c /tmp/sing-box-test.json &
proxy_pid=$!
python3 /tests/proxy_transfer.py
echo 'Native SDK, JavaScript-object response parser, and split SOCKS5/HTTP proxy tests passed'
