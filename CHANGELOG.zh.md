[English](CHANGELOG.md) | 简体中文

# 变更日志

littledl 的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循[语义化版本](https://semver.org/spec/v2.0.0.html)。

## 1.1.0 - 2026-06-26

### 变更

- FUSION 巡航期改为 IDM 式平稳：新增带宽天花板锁定，接近上限时锁定并发数 hold 一段时间（消除"加-减-加"锯齿）；所有判断统一改用平滑速度而非瞬时速度，避免单次掉速误判
- 智能重切改为分阶段差异化：PROBE/RAMP 阶段不重切，CRUISE 阶段只切严重慢块且冷却翻倍，TAIL 阶段保持激进抢占
- RAMP 爬升限制单轮增幅（`fusion_ramp_max_step`），并发以平滑阶梯增长而非翻倍，减少爬升后的速度回落

### 新增

- 新增配置项：`fusion_ramp_max_step`、`fusion_ceiling_lock_duration`、`fusion_cruise_resplit_threshold`

## 1.0.0 - 2026-06-23

### 新增

- 原子化分块下载：数据通过单个 OS 文件描述符写入预分配的 `.part` 文件，定位写入由锁串行化，成功后原子重命名为最终文件名
- 布局感知续传：持久化的分片字节区间被精确还原（含重切分片），续传前校验 ETag/Last-Modified 兼容性
- FUSION 四阶段自适应调度器（PROBE -> RAMP -> CRUISE -> TAIL），含带宽天花板估算、P50 速度与边际收益检测
- 智能策略选择：根据文件大小、服务器能力与网络状况自动选择，默认 FUSION 风格
- 统一回调系统：单文件与批量下载均支持 event、dict、kwargs、legacy 四种回调签名
- 批量下载：全局分块预算、域亲和调度、自适应并发与 rich 进度界面
- 认证（Basic、Bearer、Digest、API Key、OAuth2）、代理（系统、PAC、SOCKS5）、限速、哈希校验、文件复用与多源故障切换
- 通过 `importlib.metadata` 统一包版本来源，体现在 `__version__` 与默认 User-Agent

### 移除

- 未使用的并行实现与失效导出，将公共 API 收敛到实际使用的组件
