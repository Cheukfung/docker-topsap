# docker-topsap — 新版客户端测试分支

[![Build and verify](https://github.com/Cheukfung/docker-topsap/actions/workflows/build.yml/badge.svg)](https://github.com/Cheukfung/docker-topsap/actions/workflows/build.yml)

基于 [libra146/docker-topsap](https://github.com/libra146/docker-topsap) 的 fork，更新为天融信官网当前 Linux 主下载版本 **3.6.3.31.2.22375 amd64**（2026-10-24 核对），提供 HTTP/SOCKS5 混合代理。

- 面向 **Dokploy / Docker Compose、x86_64/amd64、用户名密码登录**。
- 新版通过原生后台 Unix socket 登录，不依赖已移除的 `topvpn` 命令，也不需要桌面或交互终端。
- `TUN_MTU` 可配置，默认保持 1300；可设为 1200 对照排查长 HTTPS URL 超时。
- CI 构建镜像并启动真实原生 SDK；VPN 登录与长 URL 访问需要你的环境验证。

**部署说明：[doc/usage.md](doc/usage.md)** · [构建说明](doc/build.md) · [Compose 配置](docker-compose.yml)

本项目使用天融信官方 Linux 安装包，客户端版权归天融信所有；本项目不是天融信官方项目。原项目的声明保留如下。

## 特别声明

本仓库中涉及的任何代码，仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断。

任何用户直接或间接使用的任何代码，无论该等使用是否符合其所在国家或地区，无论该等使用或传播发生的国家或地区的法律，代码仓库的所有者及任何其他贡献者均不对该等行为产生的任何后果（包括但不限于隐私泄露）负责。

如果任何单位或个人认为该项目的代码可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关代码。


## 特别感谢

从 [docker-easyconnect](https://github.com/Hagb/docker-easyconnect/) 这个项目获得灵感，并且也参考了部分 docker 构建代码和 iptables 相关代码，特此感谢！
