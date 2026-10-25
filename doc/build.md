# 构建与验证

当前 fork 支持 linux/amd64，官方 TopSAP 版本为 3.6.3.31.2.22375。

```bash
docker build --platform linux/amd64 --build-arg TARGETARCH=amd64 -t topsap:test .
docker run --rm --cap-add NET_ADMIN --device /dev/net/tun \
  -v "$PWD/tests:/tests:ro" topsap:test bash /tests/smoke.sh
```

无需 Git LFS 或仓库内置的旧安装包。Dockerfile 通过 GitHub Release API 的固定资产 ID 下载 TopSAP 官方安装包和 sing-box 1.14.4，并校验各自的 SHA-256。使用 `Accept: application/octet-stream` 获取二进制，避免 NAS 连接 `github.com` 下载入口超时；不自动切换来源。TopSAP 官方来源记录见 Release 说明。

部署步骤与验证范围见 [usage.md](usage.md)。
