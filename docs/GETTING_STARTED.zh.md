# MESL Surge V6.0 — 入门

时区：下文「每天 09:00 / 21:00」指 **Asia/Shanghai（UTC+8）**。  
GitHub Actions cron（UTC）：`0 1,13 * * *` = 北京时间 09:00 / 21:00。

> 免责声明：本配置仅供技术交流与个人学习调试，不是代理服务。请遵守当地法律与各平台条款。

## 你需要准备什么

1. 已安装 **Surge iOS / Mac**
2. 一份你自己有权使用的 **Surge 专用节点订阅**
3. （可选）GitHub 账号，用于 fork 本项目或开启 Actions

## 安装步骤

### 1. 导入主配置

下载并导入我提供的 [`profiles/MESL-Surge-V6.0.share.conf`](../profiles/MESL-Surge-V6.0.share.conf)。

### 2. 替换订阅占位（必须）

主配置中有：

```text
📦 MESL节点 = select, policy-path=https://subscription.example.invalid/REPLACE_WITH_YOUR_SUBSCRIPTION, update-interval=-1
```

把占位 URL **整段**换成你自己的订阅。按需把 `your-subscribe-host.example` 换成你的订阅域名。

**安全：**

- **禁止**把含真实 token 的配置提交到公开 GitHub
- 我公开仓库里的主配置始终保持脱敏占位
- fork 后请用本地覆盖或私有位置保存真实订阅，不要把 token 推进 PR

改完后在 Surge 手动「更新」`📦 MESL节点`，确认节点列表非空。

### 3. 安装去广告模块

启用 [`profiles/MESL-AdBlock-V6.0.sgmodule`](../profiles/MESL-AdBlock-V6.0.sgmodule)。  
模块覆盖 B站/酷安开屏、淘宝/京东/小红书/高德等**精确**去广告；**不会**扩大到「MITM 全部主机」。

### 4. 信任 CA（仅在需要模块解密时）

日常不要开「捕获流量」或「MITM 全部主机名」。排障时再临时打开。

### 5. 确认 patches RULE-SET

主配置在 SKK 广告拒绝规则**之前**引用 6 个自有 list（默认 raw → 本仓库 `patches/`，`update-interval=86400`）。  
也可改成本地相对路径，例如：`RULE-SET,patches/ai-critical.list,"🤖 AI住宅",update-interval=86400`。

在 Surge 做「配置检查」，确认无红色错误。

### 6. 可选：GitHub Actions

启用 `mesl-interest-bot`（见 `docs/github-actions/` 示例）：每天北京时间 09:00 / 21:00 跑兴趣驱动补丁候选。合并前请人工审阅。

## 日常注意

| 建议 | 原因 |
|------|------|
| 不要开全局 MITM | 本方案是轻 MITM |
| 不要日常常开「捕获流量」 | 费电、易踩证书坑 |
| 不要提交真实订阅 token | 泄露等于节点被盗用 |
| 不要整包拷贝上游大 list 进仓 | 本项目只维护自有小型 patches |
| pangle 广告域不要手写放行 | 应交交广告集拒绝 |

更多：[`RULES_OVERVIEW.zh.md`](RULES_OVERVIEW.zh.md) · [`MAINTENANCE.md`](MAINTENANCE.md) · [`INTEREST_MODEL.md`](INTEREST_MODEL.md) · [`APP_POLICY_MATRIX.md`](APP_POLICY_MATRIX.md)
