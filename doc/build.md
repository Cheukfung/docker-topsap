# 构建与验证

当前 fork 支持 linux/amd64，官方 TopSAP 版本为 3.6.3.31.2.22375。

```bash
docker build --platform linux/amd64 --build-arg TARGETARCH=amd64 -t topsap:test .
docker run --rm --cap-add NET_ADMIN --device /dev/net/tun \
  -v "$PWD/tests:/tests:ro" topsap:test bash /tests/smoke.sh
```

无需 Git LFS 或仓库内置的旧安装包。Dockerfile 从本 fork 的 GitHub Release 下载未经修改的官方安装包，并校验 SHA-256；官方来源记录见 Release 说明。

部署步骤与验证范围见 [usage.md](usage.md)。
