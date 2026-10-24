# Dokploy 部署（amd64 测试版）

此 fork 使用天融信官网当前 Linux 主下载按钮提供的 **3.6.3.31.2.22375 amd64** 安装包（核对日期：2026-10-24）。支持用户名、密码认证。短信、扫码、图形验证码和证书登录尚未适配。当前版本不支持 arm64。

新版包已移除 `topvpn`，通过原生 `sv_websrv` 的 Unix socket 调用官方 SDK。登录字段、密码 RSA 编码和状态查询依据安装包自带的 `sv_init.js`；不运行 Electron 图形界面。

## Dokploy

1. 新建 **Compose** 服务，选择 **Docker Compose** 类型。
2. Git 来源选择 `Cheukfung/docker-topsap`，分支 `main`，Compose Path 填 `docker-compose.yml`。
3. 在 Environment 填入以下配置，然后部署：

```dotenv
SERVER_ADDRESS=vpn.example.com:443
USER_NAME=你的用户名
PASSWORD=你的密码
TUN_MTU=1300
PROXY_BIND_IP=192.168.0.233
SOCKS_PORT=1088
```

`SERVER_ADDRESS` 填 `主机名:端口` 或 `IP:端口`，不带 `https://` 和路径。账号密码不要提交到 Git。包含 `$`、`#` 等字符时，按 dotenv 格式用单引号包住整个值。

宿主机必须有 `/dev/net/tun`。Compose 已声明 `NET_ADMIN` 和设备映射，无须 privileged。使用 Docker Compose 模式；Stack 模式不适用于这里的设备映射和源码构建。不要为 混合代理服务添加 HTTP 域名代理。

默认 HTTP/SOCKS5 混合代理绑定 NAS 的内网地址 `192.168.0.233:1088`，局域网设备直接连接这个地址，两种协议共用一个端口，无须 SSH 隧道。`PROXY_BIND_IP` 可指定 NAS 的其他内网地址，`SOCKS_PORT` 可修改端口。旧的 `SOCKS_BIND_IP` 变量不再生效。

```bash
curl -v --noproxy '' --proxy socks5h://192.168.0.233:1088 \
  --connect-timeout 10 --max-time 30 '完整HTTPS地址'
curl -v --noproxy '' --proxy http://192.168.0.233:1088 \
  --connect-timeout 10 --max-time 30 '完整HTTPS地址'
```

HTTP 代理支持 HTTPS CONNECT。GOST 自动识别协议，经本地 Dante 转发；Dante 的出口绑定 `tun0`。该代理没有认证，端口仅供可信网络访问。

## 超长 URL 对照测试

先保持 `TUN_MTU=1300` 测试同一 URL；若仍超时，再改为 `1200` 并重新部署。这是 MTU 对照实验，客户端升级本身不保证解决原问题。

登录失败会退出，保留错误码，不会切回旧客户端或反复尝试密码。测试版 `restart: "no"`，避免错误凭据重复登录；修正配置后手动重新部署。

Dokploy 日志显示登录阶段和 SDK 错误码。需要排查原生启动错误时，在容器终端查看 `/home/work/sv_websrv.log`。官方 SDK 的日志可能包含账号信息，分享前脱敏。

## 本地构建

```bash
cp .env.example .env
# 编辑 .env
docker compose -f docker-compose.yml up -d --build
docker compose -f docker-compose.yml logs -f
```

构建会从本 fork 的 GitHub Release 下载未经修改的官方固定版本安装包并校验 SHA-256；下载失败或校验不符会直接停止。基础镜像为 Debian Bookworm。包通过 `dpkg-deb --extract` 解压，不执行会修改用户桌面、注册系统服务和启动 cron 的桌面安装脚本。

## 验证边界

GitHub Actions 验证 amd64 镜像构建、Compose 配置、原生 SDK 的实际启动与本地接口响应、Dante 配置和 HTTP/SOCKS5 同端口转发，以及 Unix socket 半关闭和分段响应处理。CI 不持有你的 VPN 凭据，不验证登录、网关兼容性或长 URL 连通性；这些需在 Dokploy 部署后测试。

安装包镜像：[fork Release](https://github.com/Cheukfung/docker-topsap/releases/tag/topsap-3.6.3.31.2.22375)。GitHub runner 无法连接官网下载站，构建统一使用此镜像，不自动切换下载来源。

官方来源：[下载首页](https://app.topsec.com.cn/) · [固定版本安装包](https://app.topsec.com.cn/linux/general/x86_64/deb/TopSAP-3.6.3.31.2.22375_amd64.deb)。
