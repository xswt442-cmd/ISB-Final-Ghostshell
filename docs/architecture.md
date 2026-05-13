# Ghostshell 木马程序 — 系统架构文档

## 一、项目概述

Ghostshell 是一个用于信息安全课程教学的远控木马程序，采用 Python 实现，通过 PyInstaller 打包为 Linux ELF 可执行文件，伪装文件名为 `things.txt`。

- **C2 控制端**：运行于 Windows 宿主机，负责监听连接、管理多个客户端、下发指令
- **Payload 被控端**：运行于 Linux 虚拟机，反向连接 C2，执行命令并回传结果

## 二、系统架构图

```
+---------------------------+                      +---------------------------+
|     C2 Server (Windows)   |                      |   Payload (Linux VM)      |
|                           |                      |                           |
|  +---------------------+  |     TCP :4444        |  +---------------------+  |
|  |     OperatorCLI     |  | <------------------> |  |  GhostshellClient    |  |
|  |  (交互式命令行界面)   |  |   JSON 消息协议      |  |  (主控制器)           |  |
|  +----------+----------+  |                      |  +--------+------------+  |
|             |              |                      |           |               |
|  +----------v----------+  |                      |  +--------+------------+  |
|  |     C2Server         |  |                      |  | 模块:               |  |
|  |  (accept 循环)        |  |                      |  | shell.py            |  |
|  +----------+----------+  |                      |  | file_transfer.py    |  |
|             |              |                      |  | keylogger.py        |  |
|  +----------v----------+  |                      |  | screenshot.py       |  |
|  | ClientHandler (×N)   |  |                      |  | persistence.py      |  |
|  | (每客户端一个线程)    |  |                      |  | disguise.py         |  |
|  +---------------------+  |                      |  +---------------------+  |
+---------------------------+                      +---------------------------+
```

## 三、通信协议设计

### 消息格式

采用**长度前缀 + JSON**的分帧方式：

```
[长度]\n[UTF-8 JSON 负载]
```

示例:
```
89\n{"type":"cmd","id":"a1b2...","timestamp":"2026-05-13T10:00:00Z","ref_id":null,"data":{"command":"ls"}}
```

### 消息信封

```json
{
    "type": "消息类型",
    "id": "UUID v4 唯一标识",
    "timestamp": "ISO-8601 UTC 时间戳",
    "ref_id": "引用消息 ID (可选)",
    "data": { }
}
```

### 消息类型表

| 方向 | type | 说明 |
|------|------|------|
| C→S | `register` | 上线注册（主机名、用户名、OS、PID、IP） |
| S→C | `cmd` | 远程执行命令 |
| C→S | `cmd_result` | 命令执行结果（stdout、stderr、exit_code） |
| S→C | `upload` | 上传文件到受害机 |
| C→S | `upload_ack` | 上传确认 |
| S→C | `download` | 从受害机下载文件 |
| C→S | `download_result` | 文件内容回传（Base64） |
| S→C | `screenshot` | 触发截图 |
| C→S | `screenshot_result` | 截图 PNG 回传（Base64） |
| S→C | `keylog_start` | 启动键盘记录 |
| S→C | `keylog_stop` | 停止键盘记录 |
| S→C | `keylog_dump` | 回传按键记录 |
| C→S | `keylog_data` | 按键数据 |
| S→C | `persist_install` | 安装 crontab 持久化 |
| S→C | `persist_remove` | 移除 crontab 持久化 |
| S→C | `cleanup` | 自毁清理 |
| S→C | `heartbeat` | 心跳检测 |
| C→S | `heartbeat_ack` | 心跳回应 |

## 四、核心模块说明

### 4.1 C2 Server（Windows 端）

| 文件 | 职责 |
|------|------|
| `server/config.py` | 绑定地址、端口、超时等常量 |
| `server/server.py` | TCP 监听器，accept 循环，客户端注册/注销 |
| `server/client_handler.py` | 每客户端一个线程，消息接收分发，结果保存到 loot/ |
| `server/cli.py` | 交互式 CLI，支持 top-level 和 interact 两种模式 |

### 4.2 Payload（Linux 端）

| 文件 | 职责 |
|------|------|
| `payload/client.py` | 主控制器，连接循环 + 消息分发 |
| `payload/connection.py` | TCP 连接 + 指数退避自动重连 |
| `payload/shell.py` | `subprocess.Popen` 远程命令执行，支持超时 kill |
| `payload/file_transfer.py` | 文件上传/下载，Base64 编码传输 |
| `payload/keylogger.py` | pynput 键盘监听，写入缓冲区文件 |
| `payload/screenshot.py` | mss 全屏截图，PNG Base64 回传 |
| `payload/persistence.py` | crontab 增删持久化 |
| `payload/disguise.py` | prctl 系统调用改进程名为 things.txt |

### 4.3 线程模型

```
Server 端:
  Main Thread (accept 循环)
     ├── ClientHandler Thread #1 (recv + dispatch)
     ├── ClientHandler Thread #2
     ├── ...
     └── OperatorCLI Thread (stdin 读取)

Payload 端:
  Main Thread (连接 + 消息循环)
     └── Keylogger Thread (daemon, 可选)
```

## 五、自动重连机制

被控端断线后采用**指数退避**算法自动重连：

- 基础延迟: 5 秒
- 最大延迟: 120 秒
- 抖动: ±20% 随机化
- 公式: `min(5 × 2^attempt, 120) + jitter`

## 六、安全与检测

以下特征可被 AV/EDR 检测（课程教学目的，非对抗用途）：

1. **网络行为**：4444 端口明文 TCP 通信，无 TLS 加密
2. **进程伪装局限**：prctl 仅改 /proc/comm，ps aux 仍显示原始进程名
3. **crontab 可查**：`crontab -l` 可直接看到持久化条目
4. **Base64 传输**：文件传输有 33% 体积膨胀，特征明显
5. **PID 文件**：`/tmp/.gs_pid` 和 `/tmp/.gs_keybuf` 路径可被扫描

## 七、改进方向

- TLS 加密通信
- DNS/HTTPS 隧道隐藏 C2 流量
- 内存执行（不落盘）
- rootkit 级进程隐藏（内核模块）
- 对抗沙箱检测（延迟执行、环境检测）
