# 基金监控 GitHub Actions 自动化

这个项目使用 GitHub Actions 自动监控基金净值，并提供动态止盈建议。

## 📋 功能特性

- ✅ 每个工作日北京时间 10:00 自动执行
- ✅ 支持多只基金同时监控
- ✅ 动态计算定投成本和收益率
- ✅ 基于 MA20 均线和回撤的止盈策略
- ✅ 峰值记录持久化
- ✅ 监控结果自动保存为文本和 JSON 格式

## 🚀 快速开始

### 1. Fork 或克隆此仓库

```bash
git clone https://github.com/YOUR_USERNAME/actions_project.git
cd actions_project
```

### 2. 配置基金信息

编辑 `fund_monitor.py` 中的 `PORTFOLIO` 配置：

```python
PORTFOLIO = {
    "006282": {
        "name": "摩根欧洲",
        "init_cost": 1.7831,      # 初始成本
        "init_shares": 4767.0,    # 初始份额
        "invest_amount": 200,     # 每次定投金额
        "invest_cycle": 1,        # 定投周期(天)
        "target": 0.12,           # 目标收益率(12%)
        "callback": 0.05,         # 回撤阈值(5%)
        "start_date": "2026-02-02" # 定投开始日期
    },
    # 添加更多基金...
}
```

### 3. 推送到 GitHub

```bash
git add .
git commit -m "配置基金监控"
git push origin main
```

### 4. 启用 GitHub Actions

1. 进入仓库的 **Settings** → **Actions** → **General**
2. 确保 **Actions permissions** 设置为 "Allow all actions and reusable workflows"
3. 保存设置

### 5. 手动触发测试

1. 进入 **Actions** 标签页
2. 选择 "基金监控定时任务" 工作流
3. 点击 **Run workflow** 手动触发

## 📊 监控逻辑

| 状态 | 条件 | 建议 |
|------|------|------|
| 🚨 趋势反转(止盈) | 收益达标 + 跌破均线 + 回撤超标 | 考虑止盈 |
| ⚠️ 触发回撤 | 收益达标 + 回撤超标 | 警惕风险 |
| 🔥 强势持有 | 收益达标 + 未触发回撤 | 继续持有 |
| 🛡️ 均线下方 | 收益未达标 + 跌破均线 | 弱势观察 |
| 🟢 定投中 | 正常定投状态 | 继续定投 |

## 📁 输出文件

每次执行会生成以下文件（可在 Actions 的 Artifacts 中下载）：

- `fund_monitor_result.txt` - 可读的表格格式报告
- `fund_monitor_result.json` - 结构化 JSON 数据
- `peak_record.json` - 峰值记录（用于计算回撤）

## ⏰ 定时执行

默认配置为每个工作日北京时间 10:00 执行（UTC 02:00）。

修改 `.github/workflows/fund_monitor.yml` 中的 cron 表达式可调整执行时间：

```yaml
schedule:
  # 分 时 日 月 周
  - cron: '0 2 * * 1-5'  # 周一到周五 UTC 02:00 (北京时间 10:00)
```

## 🔧 本地测试

```bash
# 安装依赖
pip install akshare prettytable schedule pytz -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行脚本
python fund_monitor.py
```

## 📝 注意事项

1. **数据来源**: 使用 akshare 库从东方财富获取基金数据
2. **执行时间**: GitHub Actions 使用 UTC 时间，已自动转换为北京时间
3. **峰值记录**: 首次运行会初始化峰值记录，后续会持续更新
4. **工作日执行**: 仅在周一至周五执行，周末不运行

## 🛠️ 高级配置

### 📱 微信通知（Server酱）

本项目已集成 **Server酱** 微信通知功能，在触发止盈或回撤警告时自动发送微信提醒。

#### 快速配置（3分钟）

1. **获取 SendKey**
   - 访问 https://sct.ftqq.com/
   - 微信扫码登录
   - 复制您的 SendKey

2. **配置 GitHub Secret**
   - 仓库 → Settings → Secrets and variables → Actions
   - 新建 Secret：
     - Name: `SERVER_CHAN_KEY`
     - Value: 粘贴您的 SendKey

3. **关注服务号**
   - 扫描 Server酱 网站上的二维码
   - 关注"方糖服务号"接收通知

**详细配置指南**: 查看 [SERVER_CHAN_SETUP.md](SERVER_CHAN_SETUP.md)

#### 通知触发条件

仅在以下情况发送通知（避免消息过多）：
- 🚨 **趋势反转(止盈)**: 收益达标 + 跌破MA20 + 回撤超标
- ⚠️ **触发回撤**: 收益达标 + 回撤超标

### 自定义策略

修改 `generate_report()` 函数中的决策逻辑，实现自定义的止盈策略。

## 📄 许可证

MIT License
