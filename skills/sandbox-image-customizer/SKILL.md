---
name: sandbox-image-customizer
description: >
  自定义 blade-agent sandbox 镜像。支持两种方式：
  1. docker run 进入容器安装依赖后 commit
  2. 编写 Dockerfile 基于备份镜像 build
  操作前自动备份当前镜像为 :bak 标签，构建完成后覆盖回原镜像名。
  当用户需要给沙盒安装新的 Python 包、系统工具、或自定义沙盒环境时使用本技能。
---

# Sandbox 镜像自定义

本技能用于自定义 blade-agent 的 sandbox 运行环境镜像。所有操作基于当前生产镜像的备份（`:bak`），构建完成后覆盖回原镜像名，确保可随时回滚。

## 前置信息获取

开始前必须确认以下信息：

```bash
# 1. 读取当前使用的镜像名（从 blade-agent 的 .env 中获取）
grep '^SANDBOX_IMAGE=' /home/ai/codes/blade-agent/.env

# 2. 查看本地已有的 sandbox 镜像
docker images | grep sandbox
```

将读取到的镜像全名（含 registry 和 tag）记为 `$SANDBOX_IMAGE`。

> **当前环境**：`SANDBOX_IMAGE=192.168.130.23:5000/bladeai/blade-sandbox:v0.0.9`（私有 registry）。
> 镜像名包含端口号（`5000`），`${SANDBOX_IMAGE%:*}` 能正确截取到 tag 前的部分。

## 步骤 1：备份当前镜像

**必须先备份，再做任何修改。**

```bash
# 给当前镜像打 bak 标签
docker tag $SANDBOX_IMAGE ${SANDBOX_IMAGE%:*}:bak
```

验证备份：
```bash
docker images | grep sandbox | grep bak
```

## 步骤 2：选择构建方式

根据用户需求选择合适的方式。

---

### 方式 A：docker run + commit（适合少量包安装、快速调试）

适用场景：安装几个 pip 包、apt 包、修改配置文件等简单操作。

```bash
# 1. 从 bak 镜像启动临时容器
docker run -it --name sandbox-customize ${SANDBOX_IMAGE%:*}:bak /bin/bash

# 2. 在容器内执行安装操作（示例）
# pip install some-package
# apt-get update && apt-get install -y some-tool
# ... 用户指定的操作 ...

# 3. 退出容器（Ctrl+D 或 exit）

# 4. 提交为原镜像名
docker commit sandbox-customize $SANDBOX_IMAGE

# 5. 清理临时容器
docker rm sandbox-customize
```

**非交互模式**（推荐，可脚本化）：

```bash
# 一步完成：启动容器 → 安装 → 提交 → 清理
docker run --name sandbox-customize ${SANDBOX_IMAGE%:*}:bak \
  /bin/bash -c "pip install package1 package2 && apt-get update && apt-get install -y tool1"

docker commit sandbox-customize $SANDBOX_IMAGE
docker rm sandbox-customize
```

---

### 方式 B：Dockerfile build（适合复杂定制、可复现构建）

适用场景：需要多步骤构建、COPY 本地文件、设置环境变量、需要可复现的构建记录。

**1. 创建 Dockerfile**

在技能目录下创建构建文件：

```bash
# 构建目录
mkdir -p /tmp/sandbox-custom
```

编写 `/tmp/sandbox-custom/Dockerfile`：

```dockerfile
# 基于备份镜像
ARG BAK_IMAGE
FROM ${BAK_IMAGE}

# === 用户自定义内容 ===
# 示例：安装 Python 包
RUN pip install --no-cache-dir package1 package2

# 示例：安装系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    some-tool \
    && rm -rf /var/lib/apt/lists/*

# 示例：拷贝配置文件
# COPY some-config /etc/some-config

# 示例：设置环境变量
# ENV MY_VAR=value

# 保持原始启动命令
CMD ["sleep", "infinity"]
```

**2. 构建并覆盖原镜像**

```bash
docker build \
  --build-arg BAK_IMAGE=${SANDBOX_IMAGE%:*}:bak \
  -t $SANDBOX_IMAGE \
  /tmp/sandbox-custom
```

**3. 清理构建目录**（可选）

```bash
rm -rf /tmp/sandbox-custom
```

## 步骤 3：验证

```bash
# 1. 确认镜像已更新（检查 IMAGE ID 和 SIZE 变化）
docker images | grep sandbox

# 2. 快速验证安装结果
docker run --rm $SANDBOX_IMAGE python -c "import package1; print('OK')"
# 或
docker run --rm $SANDBOX_IMAGE which some-tool
```

## 回滚

如果新镜像有问题，从 bak 恢复：

```bash
docker tag ${SANDBOX_IMAGE%:*}:bak $SANDBOX_IMAGE
```

## 重要注意事项

- **备份镜像（:bak）在确认新镜像稳定前不要删除**
- 如果 blade-agent 有正在运行的 sandbox 容器，新镜像**不会影响已有容器**，只有新创建的容器才会用新镜像
- 方式 A 的 commit 不会保留 Dockerfile 的构建记录，方式 B 更适合需要复现的场景
- 安装大量包时建议用方式 B，可以利用 Docker 层缓存
- 镜像内默认 pip 源是清华镜像（`PIP_INDEX_URL` 已配置），无需额外指定

## AI 执行流程

当用户请求自定义沙盒镜像时，按以下流程操作：

1. **读取 `.env`** 获取 `SANDBOX_IMAGE` 的值
2. **确认需求**：用户要安装什么包/工具？是否需要 COPY 文件？
3. **判断方式**：
   - 仅安装几个 pip/apt 包 → 方式 A（非交互模式）
   - 需要 COPY 文件、多步骤、或用户指定 Dockerfile → 方式 B
4. **执行备份**（步骤 1）
5. **执行构建**（步骤 2）
6. **执行验证**（步骤 3）
7. **报告结果**：告知用户镜像已更新，以及如何回滚
