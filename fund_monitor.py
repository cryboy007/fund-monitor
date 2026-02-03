#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金监控脚本 - GitHub Actions 版本
适用于定时任务执行，每次运行输出当前状态
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable
import pytz
import json
import os
import requests

# ===================== 配置区 =====================
# 设置北京时区
TZ_CHINA = pytz.timezone('Asia/Shanghai')

PORTFOLIO = {
    "006282": {
        "name": "摩根欧洲",
        "init_cost": 1.7831, 
        "init_shares": 4767.0,
        "invest_amount": 200, 
        "invest_cycle": 1,
        "target": 0.12, 
        "callback": 0.05, 
        "start_date": "2026-02-02"
    },
    "017091": {
        "name": "纳指科技",
        "init_cost": 2.3589, 
        "init_shares": 1992.0,
        "invest_amount": 100, 
        "invest_cycle": 1,
        "target": 0.15, 
        "callback": 0.06, 
        "start_date": "2026-02-02"
    },
    "539003": {
        "name": "建信富时100",
        "init_cost": 1.3569, 
        "init_shares": 5361.8,
        "invest_amount": 10, 
        "invest_cycle": 1,
        "target": 0.15, 
        "callback": 0.06, 
        "start_date": "2026-02-02"
    },
    "019449": {
        "name": "摩根日本",
        "init_cost": 1.9332, 
        "init_shares": 5845.22,
        "invest_amount": 500, 
        "invest_cycle": 14,
        "target": 0.15, 
        "callback": 0.06, 
        "start_date": "2026-02-02"
    }
}

# 峰值记录文件路径
PEAK_RECORD_FILE = "peak_record.json"


def load_peak_record():
    """从文件加载峰值记录"""
    if os.path.exists(PEAK_RECORD_FILE):
        try:
            with open(PEAK_RECORD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载峰值记录失败: {e}")
    return {code: 0.0 for code in PORTFOLIO}


def save_peak_record(peak_record):
    """保存峰值记录到文件"""
    try:
        with open(PEAK_RECORD_FILE, 'w', encoding='utf-8') as f:
            json.dump(peak_record, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存峰值记录失败: {e}")


def get_now_beijing():
    """获取当前的北京时间"""
    return datetime.now(TZ_CHINA)


def get_nav_and_ma(code):
    """获取基金净值和20日均线"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        df['单位净值'] = df['单位净值'].astype(float)
        ma20 = df['单位净值'].rolling(window=20).mean().iloc[-1]
        curr_nav = df.iloc[-1]['单位净值']
        return curr_nav, ma20
    except Exception as e:
        print(f"⚠️ 获取基金 {code} 数据失败: {e}")
        return None, None


def simulate_investment(info, curr_nav):
    """模拟定投计算"""
    start_dt = datetime.strptime(info['start_date'], '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(TZ_CHINA)
    today = get_now_beijing()
    
    days_passed = (today.date() - start_dt.date()).days
    times = (days_passed // info['invest_cycle']) + 1 if days_passed >= 0 else 0
    
    new_shares = info['init_shares'] + (times * info['invest_amount'] / curr_nav)
    total_spent = (info['init_shares'] * info['init_cost']) + (times * info['invest_amount'])
    avg_cost = total_spent / new_shares
    return new_shares, avg_cost


def send_serverchan_notification(title, content):
    """
    发送 Server酱 通知到微信
    
    Args:
        title: 通知标题
        content: 通知内容（支持 Markdown）
    """
    sendkey = os.environ.get('SERVER_CHAN_KEY')
    if not sendkey:
        print("⚠️ 未配置 SERVER_CHAN_KEY，跳过通知发送")
        return False
    
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    
    try:
        response = requests.post(url, data={
            "title": title,
            "desp": content
        }, timeout=10)
        
        result = response.json()
        if result.get('code') == 0:
            print(f"✅ Server酱通知发送成功")
            return True
        else:
            print(f"⚠️ Server酱通知发送失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ Server酱通知发送异常: {e}")
        return False


def generate_report():
    """生成监控报告"""
    peak_record = load_peak_record()
    
    table = PrettyTable()
    table.field_names = ["基金名称", "当前净值", "MA20", "动态成本", "收益率", "盈利金额", "回撤", "操作建议"]
    table.align["基金名称"] = "l"
    
    results = []
    
    for code, info in PORTFOLIO.items():
        curr_nav, ma20 = get_nav_and_ma(code)
        if curr_nav is None:
            continue
        
        # 更新峰值
        if curr_nav > peak_record.get(code, 0):
            peak_record[code] = curr_nav
        
        curr_shares, curr_cost = simulate_investment(info, curr_nav)
        profit_rate = (curr_nav - curr_cost) / curr_cost
        drawdown = (peak_record[code] - curr_nav) / peak_record[code] if peak_record[code] > 0 else 0
        profit_amount = (curr_nav - curr_cost) * curr_shares
        
        is_broken_ma = curr_nav < ma20
        
        # 决策逻辑
        if profit_rate >= info['target']:
            if drawdown >= info['callback'] and is_broken_ma:
                advice = "🚨 趋势反转(止盈)"
            elif drawdown >= info['callback']:
                advice = "⚠️ 触发回撤"
            else:
                advice = "🔥 强势持有"
        elif is_broken_ma:
            advice = "🛡️ 均线下方"
        else:
            advice = "🟢 定投中"
        
        table.add_row([
            info['name'], 
            f"{curr_nav:.4f}", 
            f"{ma20:.4f}", 
            f"{curr_cost:.4f}",
            f"{profit_rate:.2%}", 
            f"{profit_amount:.2f}", 
            f"{drawdown:.2%}", 
            advice
        ])
        
        results.append({
            "code": code,
            "name": info['name'],
            "nav": curr_nav,
            "ma20": ma20,
            "cost": curr_cost,
            "profit_rate": profit_rate,
            "profit_amount": profit_amount,
            "drawdown": drawdown,
            "advice": advice
        })
    
    # 保存更新后的峰值记录
    save_peak_record(peak_record)
    
    # 输出报告
    print(f"\n📊 增强型动态止盈监控 | 北京时间 (UTC+8): {get_now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    print(table)
    
    print("\n📖 逻辑说明看板：")
    help_table = PrettyTable()
    help_table.field_names = ["优先级", "状态显示", "背后逻辑"]
    help_table.add_row(["1", "🚨 趋势反转", "收益达标 + 跌破均线 + 回撤超标 (锁定利润)"])
    help_table.add_row(["2", "⚠️ 触发回撤", "收益达标 + 回撤超标 (警惕)"])
    help_table.add_row(["3", "🔥 强势持有", "收益达标 + 未触发回撤 (继续持有)"])
    help_table.add_row(["4", "🛡️ 均线下方", "收益未达标 + 跌破均线 (弱势观察)"])
    help_table.add_row(["5", "🟢 定投中", "正常定投状态"])
    print(help_table)
    
    # 保存结果到文件
    with open('fund_monitor_result.txt', 'w', encoding='utf-8') as f:
        f.write(f"📊 增强型动态止盈监控 | 北京时间: {get_now_beijing().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(str(table))
        f.write("\n\n")
        f.write(str(help_table))
    
    # 保存 JSON 格式结果
    with open('fund_monitor_result.json', 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": get_now_beijing().isoformat(),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 监控完成，结果已保存到 fund_monitor_result.txt 和 fund_monitor_result.json")
    
    # 检查是否需要发送通知
    alert_funds = [r for r in results if r['advice'] in ['🚨 趋势反转(止盈)', '⚠️ 触发回撤']]
    
    if alert_funds:
        # 构建通知内容
        notification_title = f"📊 基金监控提醒 ({len(alert_funds)}只基金)"
        notification_content = f"## 📊 基金监控提醒\n\n"
        notification_content += f"**时间**: {get_now_beijing().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for fund in alert_funds:
            icon = "🚨" if fund['advice'] == "🚨 趋势反转(止盈)" else "⚠️"
            notification_content += f"### {icon} {fund['name']} - {fund['advice']}\n"
            notification_content += f"- 当前净值: **{fund['nav']:.4f}**\n"
            notification_content += f"- 动态成本: {fund['cost']:.4f}\n"
            notification_content += f"- 收益率: **{fund['profit_rate']:.2%}**\n"
            notification_content += f"- 盈利金额: **{fund['profit_amount']:.2f}元**\n"
            notification_content += f"- 回撤: {fund['drawdown']:.2%}\n"
            
            if fund['advice'] == "🚨 趋势反转(止盈)":
                notification_content += f"\n**建议**: 考虑止盈锁定利润\n"
            else:
                notification_content += f"\n**建议**: 警惕回撤风险\n"
            
            notification_content += "\n---\n\n"
        
        notification_content += f"[查看详细报告](https://github.com/cryboy007/fund-monitor/actions)"
        
        # 发送通知
        send_serverchan_notification(notification_title, notification_content)
    else:
        print("\n💡 当前无需发送通知（未触发止盈或回撤警告）")


if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
