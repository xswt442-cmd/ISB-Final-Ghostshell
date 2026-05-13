# 答辩 PPT 大纲 (10-12 页)

## Slide 1: 封面
- 课题名称：木马程序设计与实现 — Ghostshell
- 选题一：木马程序（方案 B: ELF 伪装文件）
- 团队成员、学号、日期

---

## Slide 2: 项目概述
- 什么是 Ghostshell：基于 Python 的远程控制程序
- 采用 C/S 架构，反向 TCP 连接
- 攻击端 Windows / 受害端 Linux VM
- 打包为 ELF 可执行文件，伪装文件名 things.txt

---

## Slide 3: 系统架构
- 架构图（从 architecture.md 复制 ASCII 图或用 draw.io 重绘）
- 组件说明：C2 Server / Payload / 通信协议
- 线程模型：Server 多线程（1 client = 1 thread），Client 双线程

---

## Slide 4: 通信协议设计
- JSON-over-TCP，长度前缀分帧
- 消息类型分类（控制类、数据类、状态类）
- 协议流程图

---

## Slide 5: C2 Server 设计
- accept 循环 + 多客户端管理
- 交互式 CLI（top-level / interact 双模式）
- 结果自动保存到 loot 目录

---

## Slide 6: Payload 功能模块
- 8 个核心模块一览
- Shell 执行 + 超时控制
- 文件双向传输（Base64 编码）

---

## Slide 7: 功能演示 (1)
- 截图演示：远程 Shell 命令执行
- 截图演示：文件上传/下载
- 截图演示：屏幕截图回传

---

## Slide 8: 功能演示 (2)
- 截图演示：键盘记录启动与数据回传
- 截图演示：持久化安装 (crontab)
- 截图演示：重启后自动重连验证

---

## Slide 9: 实验数据
- 延迟对比表（本地 vs 远程 C2）
- 图表：柱状图对比
- 延迟分析结论

---

## Slide 10: 进程伪装与自毁
- prctl 改变 /proc/comm 名称
- crontab 持久化机制
- cleanup 自毁流程（清除二进制、crontab、PID 文件）

---

## Slide 11: 防御视角
- 如何检测此类木马：
  - 网络层：异常 TCP 连接、固定心跳模式
  - 系统层：检查 crontab 异常条目
  - 文件层：/tmp 下可疑可执行文件
  - 行为层：进程名与实际可执行文件不符
- 防御措施建议

---

## Slide 12: 总结与收获
- 掌握的技术：Socket 编程、多线程、PyInstaller 打包
- 对木马工作原理的理解
- 安全防护的启示
- Q&A
