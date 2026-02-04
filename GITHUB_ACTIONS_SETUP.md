# GitHub Actions 市场情绪监控配置说明

## 📅 运行时间

工作流将在以下北京时间自动运行（周一至周五）：

- **09:25** - 开盘时段（集合竞价后）
- **10:30** - 早盘中段
- **11:30** - 午盘收盘前
- **14:00** - 午盘后
- **15:00** - 收盘时段

## 🔧 配置说明

### 1. 工作流文件
位置：`.github/workflows/market_sentiment.yml`

### 2. 时间设置
- GitHub Actions 使用 UTC 时间
- 已自动转换为北京时间（UTC+8）
- cron 表达式格式：`分 时 日 月 星期`

### 3. 依赖安装
自动安装：
- akshare
- pandas

### 4. 手动触发
除定时运行外，也可以手动触发：
1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择 "市场情绪监控" 工作流
4. 点击 "Run workflow"

## 📊 输出说明

工作流会输出完整的市场情绪报告，包括：
- 市场宽度统计
- 主要指数表现
- 北向资金流向
- 恐慌/贪婪指数
- 网格交易建议
- 风险预警

## ⚙️ 可选配置

### 添加微信通知

1. 在 `.github/workflows/market_sentiment.yml` 中取消注释通知部分

2. 在 GitHub 仓库设置中添加 Secret：
   - 名称：`SERVERCHAN_KEY`
   - 值：你的 Server酱 SendKey

3. 创建 `send_notification.py`（参考基金监控项目）

### 保存历史数据

可以修改工作流，将报告保存到文件或数据库：
```yaml
- name: 保存报告
  run: |
    python run_sentiment_once.py > reports/$(date +%Y%m%d_%H%M).txt
```

## 🔍 调试

### 查看运行日志
1. GitHub 仓库 → Actions
2. 选择对应的工作流运行
3. 查看详细日志

### 常见问题

**Q: 为什么有时候获取不到数据？**
A: akshare 数据源偶尔会有连接问题，工作流会自动重试。

**Q: 如何调整运行频率？**
A: 修改 `.github/workflows/market_sentiment.yml` 中的 cron 表达式。

**Q: 如何禁用自动运行？**
A: 在 workflow 文件中注释或删除 `schedule` 部分，保留 `workflow_dispatch` 可手动触发。

## 📝 注意事项

1. **GitHub Actions 限制**
   - 公共仓库：免费无限制
   - 私有仓库：每月 2000 分钟

2. **数据时效性**
   - 依赖 akshare 数据源
   - 建议在交易时段运行
   - 非交易时段可能无法获取数据

3. **时区问题**
   - 已配置为北京时间
   - 如需调整，请转换为 UTC 时间

## 🚀 快速开始

1. 提交代码到 GitHub
```bash
git add .github/workflows/market_sentiment.yml
git add market_sentiment.py
git add run_sentiment_once.py
git commit -m "添加市场情绪监控 GitHub Actions"
git push
```

2. 查看 Actions 日志确认运行

3. （可选）配置通知和数据保存
