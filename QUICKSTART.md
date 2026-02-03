# 快速开始指南

## 📦 项目已准备就绪！

您的基金监控项目已经配置完成，包含以下文件：

```
actions_project/
├── .github/
│   └── workflows/
│       └── fund_monitor.yml      # GitHub Actions 工作流配置
├── fund_monitor.py                # 主监控脚本
├── peak_record.json               # 峰值记录（自动更新）
├── requirements.txt               # Python 依赖
├── .gitignore                     # Git 忽略配置
└── README.md                      # 详细文档
```

## 🚀 立即部署到 GitHub

### 步骤 1: 初始化 Git 仓库（如果还未初始化）

```bash
cd d:\AI\actions_project
git init
git add .
git commit -m "初始化基金监控项目"
```

### 步骤 2: 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称: `fund-monitor` 或任意名称
3. 设置为 **Public** 或 **Private**（都可以）
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

### 步骤 3: 推送代码到 GitHub

```bash
# 替换为您的 GitHub 仓库地址
git remote add origin https://github.com/YOUR_USERNAME/fund-monitor.git
git branch -M main
git push -u origin main
```

### 步骤 4: 启用 GitHub Actions

1. 进入您的 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 如果提示启用 Actions，点击 "I understand my workflows, go ahead and enable them"

### 步骤 5: 手动测试运行

1. 在 **Actions** 页面，选择 "基金监控定时任务"
2. 点击右侧的 **Run workflow** 下拉菜单
3. 点击绿色的 **Run workflow** 按钮
4. 等待几分钟，查看运行结果

### 步骤 6: 查看结果

1. 点击刚才运行的工作流
2. 点击 "fund-monitor" 任务
3. 展开 "运行基金监控脚本" 步骤查看输出
4. 在页面底部的 **Artifacts** 区域下载结果文件

## ⚙️ 自定义配置

### 修改基金列表

编辑 `fund_monitor.py` 中的 `PORTFOLIO` 字典：

```python
PORTFOLIO = {
    "基金代码": {
        "name": "基金名称",
        "init_cost": 1.5000,      # 初始成本价
        "init_shares": 1000.0,    # 初始持有份额
        "invest_amount": 100,     # 每次定投金额
        "invest_cycle": 1,        # 定投周期(天)
        "target": 0.15,           # 目标收益率 15%
        "callback": 0.05,         # 回撤阈值 5%
        "start_date": "2026-02-03" # 定投开始日期
    }
}
```

### 修改执行时间

编辑 `.github/workflows/fund_monitor.yml`：

```yaml
schedule:
  # 每天 UTC 02:00 (北京时间 10:00)
  - cron: '0 2 * * 1-5'
  
  # 示例：改为每天 UTC 01:00 (北京时间 09:00)
  # - cron: '0 1 * * 1-5'
  
  # 示例：每天两次 09:00 和 15:00
  # - cron: '0 1,7 * * 1-5'
```

**Cron 表达式格式**: `分 时 日 月 周`
- `0 2 * * 1-5` = 每周一到周五的 UTC 02:00

## 📊 本地测试

在推送到 GitHub 之前，可以本地测试：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python fund_monitor.py

# 查看结果
type fund_monitor_result.txt
```

## 🔔 添加通知（可选）

### 方式 1: 邮件通知

在 `.github/workflows/fund_monitor.yml` 中添加邮件步骤：

```yaml
- name: 发送邮件通知
  if: always()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: 基金监控报告 - ${{ github.run_number }}
    body: file://fund_monitor_result.txt
    to: your-email@example.com
    from: GitHub Actions
```

### 方式 2: 企业微信机器人

在脚本中添加 webhook 调用（需要修改 `fund_monitor.py`）。

## 📝 常见问题

### Q: 为什么 Actions 没有自动运行？
A: 检查以下几点：
1. 确保仓库的 Actions 已启用
2. 确认 cron 时间设置正确（注意 UTC 时区）
3. 首次推送后可能需要手动触发一次

### Q: 如何查看历史运行记录？
A: 进入 Actions 标签页，可以看到所有运行历史和结果。

### Q: 峰值记录会丢失吗？
A: `peak_record.json` 会在每次运行后更新并提交到仓库，不会丢失。

### Q: 可以监控多少只基金？
A: 理论上无限制，但建议不超过 20 只，以确保脚本在 GitHub Actions 的时间限制内完成。

## 🎯 下一步

- ✅ 定期检查 Actions 运行结果
- ✅ 根据市场情况调整止盈参数
- ✅ 添加更多基金到监控列表
- ✅ 考虑添加通知功能

## 📞 需要帮助？

查看完整文档: [README.md](README.md)
