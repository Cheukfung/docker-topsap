#!/bin/bash
set -Eeuo pipefail
umask 077

: "${SERVER_ADDRESS:?Set SERVER_ADDRESS to the VPN gateway host:port}"
: "${USER_NAME:?Set USER_NAME}"
: "${PASSWORD:?Set PASSWORD}"
: "${TOPSAP_DIR:?Set TOPSAP_DIR}"
: "${TUN_MTU:?Set TUN_MTU}"
[[ -c /dev/net/tun ]] || { echo 'Missing /dev/net/tun; configure devices in Compose' >&2; exit 1; }

pids=()
cleanup() {
    trap - EXIT
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    wait
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

cd "$TOPSAP_DIR"
./sv_websrv > /home/work/sv_websrv.log 2>&1 &
vpn_pid=$!
pids+=("$vpn_pid")
for ((i=0; i<30; i++)); do
    kill -0 "$vpn_pid"
    if [[ -S /tmp/TopSAP_ELE/topsap.sock ]]; then
        break
    fi
    sleep 1
done
[[ -S /tmp/TopSAP_ELE/topsap.sock ]] || { echo 'TopSAP control socket did not start; inspect /home/work/sv_websrv.log' >&2; exit 1; }

python3 /home/work/topsap.py
ip link set dev tun0 mtu "$TUN_MTU"
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
danted -f /etc/danted.conf &
pids+=("$!")
gost -L socks5://:1080 -F socks5://127.0.0.1:1081 &
pids+=("$!")
gost -L http://:1082 -F socks5://127.0.0.1:1081 &
pids+=("$!")
echo "SOCKS5 proxy on container port 1080, HTTP proxy on 1082; tun0 MTU=$TUN_MTU"
wait -n "${pids[@]}"
echo 'A required service exited; stopping the container' >&2
exit 1
