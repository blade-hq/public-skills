# 沙箱镜像定制

自定义 blade-agent 的 sandbox 运行环境镜像。操作前自动备份当前镜像为 `:bak` 标签，构建完成后覆盖回原镜像名，确保可随时回滚。

## 前置信息获取

```bash
# 1. 读取当前使用的镜像名
grep SANDBOX_IMAGE /home/ai/codes/blade-agent/.env

# 2. 查看本地已有的 sandbox 镜像
docker images | grep sandbox
```

将读取到的镜像全名（含 registry 和 tag）记为 `$SANDBOX_IMAGE`。

## 步骤 1：备份当前镜像

**必须先备份，再做任何修改。**

```bash
docker tag $SANDBOX_IMAGE ${SANDBOX_IMAGE%:*}:bak
```

验证备份：

```bash
docker images | grep sandbox | grep bak
```

## 步骤 2：选择构建方式

### 方式 A：docker run + commit

适合少量包安装、快速调试。

**非交互模式（推荐）：**

```bash
# 一步完成：启动容器 → 安装 → 提交 → 清理
docker run --name sandbox-customize ${SANDBOX_IMAGE%:*}:bak \
  /bin/bash -c "pip install package1 package2 && apt-get update && apt-get install -y tool1"

docker commit sandbox-customize $SANDBOX_IMAGE
docker rm sandbox-customize
```

**交互模式：**

```bash
docker run -it --name sandbox-customize ${SANDBOX_IMAGE%:*}:bak /bin/bash
# 在容器内执行安装操作，退出后：
docker commit sandbox-customize $SANDBOX_IMAGE
docker rm sandbox-customize
```

### 方式 B：Dockerfile build

适合复杂定制、需要可复现的构建记录。

```bash
mkdir -p /tmp/sandbox-custom
```

编写 `/tmp/sandbox-custom/Dockerfile`：

```dockerfile
ARG BAK_IMAGE
FROM ${BAK_IMAGE}

# 安装 Python 包
RUN pip install --no-cache-dir package1 package2

# 安装系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    some-tool \
    && rm -rf /var/lib/apt/lists/*

# 保持原始启动命令
CMD ["sleep", "infinity"]
```

构建：

```bash
docker build \
  --build-arg BAK_IMAGE=${SANDBOX_IMAGE%:*}:bak \
  -t $SANDBOX_IMAGE \
  /tmp/sandbox-custom
```

## 步骤 3：验证

```bash
# 确认镜像已更新
docker images | grep sandbox

# 验证安装结果
docker run --rm $SANDBOX_IMAGE python -c "import package1; print('OK')"
docker run --rm $SANDBOX_IMAGE which some-tool
```

## 回滚

```bash
docker tag ${SANDBOX_IMAGE%:*}:bak $SANDBOX_IMAGE
```

## 注意事项

- 备份镜像（`:bak`）在确认新镜像稳定前不要删除
- 新镜像不影响已有容器，只有新创建的容器才会使用
- 方式 A 的 commit 不保留构建记录，方式 B 更适合需要复现的场景
- 大量包安装建议用方式 B，可利用 Docker 层缓存
- 镜像内默认 pip 源是清华镜像（`PIP_INDEX_URL` 已配置），无需额外指定
