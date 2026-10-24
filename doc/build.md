# 构建与验证

当前 fork 支持 linux/amd64，官方 TopSAP 版本为 3.6.3.31.2.22375。

```bash
docker build --platform linux/amd64 --build-arg TARGETARCH=amd64 -t topsap:test .
docker run --rm --cap-add NET_ADMIN --device /dev/net/tun \
  -v "$PWD/tests:/tests:ro" topsap:test bash /tests/smoke.sh
```

无需 Git LFS 或仓库内置的旧安装包。Dockerfile 从天融信官网固定 URL 下载并校验 SHA-256。

部署步骤与验证范围见 [usage.md](usage.md)。
