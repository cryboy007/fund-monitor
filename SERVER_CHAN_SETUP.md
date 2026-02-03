# Server酱微信通知配置指南

## 📱 什么是 Server酱？

Server酱是一个免费的微信推送服务，可以将消息推送到您的微信服务号。无需创建群聊，个人即可使用。

## 🚀 快速配置（3分钟搞定）

### 步骤 1: 获取 SendKey

1. 访问 Server酱官网：https://sct.ftqq.com/
2. 点击右上角"登入"，使用**微信扫码登录**
3. 登录后，在首页找到您的 **SendKey**（格式：`SCTxxxxxxxxxxxxxx`）
4. 复制这个 SendKey

### 步骤 2: 关注服务号

1. 在 Server酱 网站上找到"消息通道"
2. 扫描二维码关注**"方糖服务号"**
3. 关注后，您将通过这个服务号接收通知

### 步骤 3: 在 GitHub 配置 Secret

1. 打开您的 GitHub 仓库：https://github.com/cryboy007/fund-monitor
2. 点击 **Settings**（设置）
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 填写信息：
   - **Name**: `SERVER_CHAN_KEY`
   - **Value**: 粘贴您刚才复制的 SendKey
6. 点击 **Add secret**

### 步骤 4: 测试通知

#### 方法 1: 在 Server酱 网站测试

1. 在 Server酱 网站首页
2. 找到"快速测试"区域
3. 点击"发送测试消息"
4. 检查微信是否收到通知

#### 方法 2: 本地测试（可选）

```bash
# 设置环境变量（Windows PowerShell）
$env:SERVER_CHAN_KEY="你的SendKey"

# 运行脚本
python fund_monitor.py
```

#### 方法 3: GitHub Actions 测试

1. 进入仓库的 **Actions** 标签
2. 选择"基金监控定时任务"
3. 点击 **Run workflow** → **Run workflow**
4. 等待运行完成，检查微信是否收到通知

## 📊 通知触发条件

只有在以下情况下才会发送微信通知（避免消息过多）：

| 信号 | 说明 | 示例 |
|------|------|------|
| 🚨 **趋势反转(止盈)** | 收益达标 + 跌破MA20 + 回撤超标 | 建议考虑止盈 |
| ⚠️ **触发回撤** | 收益达标 + 回撤超标 | 警惕回撤风险 |

其他状态（🔥强势持有、🟢定投中、🛡️均线下方）**不会发送通知**。

## 📱 通知消息示例

您将收到类似这样的微信消息：

```
📊 基金监控提醒 (1只基金)

时间: 2026-02-03 10:00:00

🚨 摩根欧洲 - 趋势反转(止盈)
- 当前净值: 1.8330
- 动态成本: 1.7853
- 收益率: 2.67%
- 盈利金额: 237.87元
- 回撤: 5.2%

建议: 考虑止盈锁定利润

---
查看详细报告
```

## ❓ 常见问题

### Q: SendKey 在哪里找？
A: 登录 https://sct.ftqq.com/ 后，在首页顶部就能看到您的 SendKey。

### Q: 为什么没有收到通知？
A: 检查以下几点：
1. 确认已关注"方糖服务号"
2. 确认 GitHub Secret 配置正确（名称必须是 `SERVER_CHAN_KEY`）
3. 确认当前基金状态是否触发了通知条件（止盈或回撤）
4. 查看 GitHub Actions 运行日志，看是否有错误信息

### Q: Server酱 免费吗？
A: 是的，Server酱提供免费版本，每天可发送 5 条消息，对于基金监控完全够用。

### Q: 可以自定义通知内容吗？
A: 可以！编辑 `fund_monitor.py` 中的 `send_serverchan_notification()` 函数和通知内容构建部分。

### Q: 如果不想收到某些通知怎么办？
A: 修改 `fund_monitor.py` 中的这一行：
```python
alert_funds = [r for r in results if r['advice'] in ['🚨 趋势反转(止盈)', '⚠️ 触发回撤']]
```
移除不想接收的信号类型即可。

## 🔒 安全说明

- SendKey 是您的私密信息，不要分享给他人
- GitHub Secrets 是加密存储的，安全可靠
- Server酱 只能发送消息到您自己的微信，无法被他人滥用

## 🎯 下一步

配置完成后：
1. ✅ 等待每个工作日 10:00 自动运行
2. ✅ 或手动触发 GitHub Actions 测试
3. ✅ 根据通知及时调整投资策略

---

**官方文档**: https://sct.ftqq.com/forward  
**问题反馈**: https://github.com/cryboy007/fund-monitor/issues
