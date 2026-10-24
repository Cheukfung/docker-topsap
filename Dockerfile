FROM debian:bookworm-slim

ARG TARGETARCH
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    TOPSAP_DIR=/opt/apps/cn.com.topvpn/files \
    LD_LIBRARY_PATH=/opt/apps/cn.com.topvpn/files \
    TUN_MTU=1300

RUN test "$TARGETARCH" = amd64 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl dante-server iproute2 iptables libstdc++6 libuuid1 \
       net-tools procps python3 python3-cryptography sudo \
    && rm -rf /var/lib/apt/lists/*

# Current Linux amd64 download on https://app.topsec.com.cn/ (2026-10-24).
# Unmodified installer mirrored in this fork; official source and hash in Release notes.
# Extract only: the desktop installer starts host services and edits user profiles.
RUN curl --fail --location --show-error --connect-timeout 30 --max-time 300 \
      https://github.com/Cheukfung/docker-topsap/releases/download/topsap-3.6.3.31.2.22375/TopSAP-3.6.3.31.2.22375_amd64.deb \
      --output /tmp/topsap.deb \
    && echo '06bb0b6a422782d859765ab2dc22757e280863f145f7a8867fb1391372095842  /tmp/topsap.deb' | sha256sum --check - \
    && dpkg-deb --extract /tmp/topsap.deb / \
    && rm /tmp/topsap.deb \
    && mkdir -p /home/work /opt/sslvpn/config \
    && touch /opt/sslvpn/config/vpnclient-sysconfig /opt/sslvpn/config/resinfo-config \
             /opt/sslvpn/config/spa_dateconfig /opt/sslvpn/config/spaconfig /opt/sslvpn/config/.sysconfig

WORKDIR /home/work
COPY start.sh topsap.py ./
COPY danted.conf /etc/danted.conf
RUN chmod 755 start.sh
EXPOSE 1080
CMD ["/home/work/start.sh"]
