#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金监控脚本 - GitHub Actions 版本
适用于定时任务执行，每次运行输出当前状态
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from prettytable import PrettyTable
import pytz
import json
import os
import requests
import numpy as np

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

# 止损配置
STOP_LOSS_THRESHOLD = -0.20  # 止损线 -20%
EMERGENCY_STOP_LOSS = -0.30  # 紧急止损 -30%

# 缓存配置
CACHE_DIR = "cache"


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


def get_cache_key(code, indicator):
    """生成缓存键"""
    from datetime import date
    today = date.today().isoformat()
    return f"{code}_{indicator}_{today}"


def get_cached_data(code, indicator):
    """获取缓存数据（优化 7）"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache_key = get_cache_key(code, indicator)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
    
    if os.path.exists(cache_file):
        try:
            return pd.read_pickle(cache_file)
        except Exception as e:
            print(f"⚠️ 读取缓存失败: {e}")
    
    # 获取新数据
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator=indicator)
        # 保存缓存
        try:
            df.to_pickle(cache_file)
        except:
            pass
        return df
    except Exception as e:
        print(f"⚠️ 获取数据失败: {e}")
        return None


def get_nav_and_ma(code):
    """获取基金净值和20日均线"""
    try:
        df = get_cached_data(code, "单位净值走势")
        if df is None:
            return None, None
        
        df['单位净值'] = df['单位净值'].astype(float)
        ma20 = df['单位净值'].rolling(window=20).mean().iloc[-1]
        curr_nav = df.iloc[-1]['单位净值']
        return curr_nav, ma20
    except Exception as e:
        print(f"⚠️ 获取基金 {code} 数据失败: {e}")
        return None, None


def simulate_investment(info, curr_nav):
    """简单定投模拟（降级方案）"""
    start_dt = datetime.strptime(info['start_date'], '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(TZ_CHINA)
    today = get_now_beijing()
    
    days_passed = (today.date() - start_dt.date()).days
    times = (days_passed // info['invest_cycle']) + 1 if days_passed >= 0 else 0
    
    new_shares = info['init_shares'] + (times * info['invest_amount'] / curr_nav)
    total_spent = (info['init_shares'] * info['init_cost']) + (times * info['invest_amount'])
    avg_cost = total_spent / new_shares
    return new_shares, avg_cost


def simulate_investment_accurate(info, code, curr_nav):
    """精确的定投模拟（优化 1：基于历史净值）"""
    try:
        df = get_cached_data(code, "单位净值走势")
        if df is None:
            return simulate_investment(info, curr_nav)
        
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df['单位净值'] = df['单位净值'].astype(float)
        df = df.sort_values('净值日期')
        
        start_date = pd.to_datetime(info['start_date'])
        total_shares = info['init_shares']
        total_cost = info['init_shares'] * info['init_cost']
        
        # 获取当前日期（不带时区）
        today = pd.Timestamp.now().normalize()
        
        # 模拟每次定投
        current_date = start_date + pd.Timedelta(days=info['invest_cycle'])
        while current_date <= today:
            # 找到最近的交易日净值
            available_navs = df[df['净值日期'] <= current_date]
            if len(available_navs) > 0:
                nav_on_date = available_navs.iloc[-1]['单位净值']
                shares_bought = info['invest_amount'] / nav_on_date
                total_shares += shares_bought
                total_cost += info['invest_amount']
            
            current_date += pd.Timedelta(days=info['invest_cycle'])
        
        avg_cost = total_cost / total_shares if total_shares > 0 else info['init_cost']
        return total_shares, avg_cost
    except Exception as e:
        print(f"⚠️ 精确定投模拟失败，使用简单模式: {e}")
        return simulate_investment(info, curr_nav)


def calculate_risk_metrics(code, days=60):
    """计算夏普比率和波动率（优化 2）"""
    try:
        df = get_cached_data(code, "单位净值走势")
        if df is None:
            return 0, 0, 0
        
        df['单位净值'] = df['单位净值'].astype(float)
        df['return'] = df['单位净值'].pct_change()
        
        recent_returns = df['return'].tail(days).dropna()
        
        if len(recent_returns) < 10:
            return 0, 0, 0
        
        # 年化收益率
        avg_return = recent_returns.mean() * 252
        # 年化波动率
        volatility = recent_returns.std() * np.sqrt(252)
        # 夏普比率（假设无风险利率 2.5%）
        sharpe = (avg_return - 0.025) / volatility if volatility > 0 else 0
        
        return sharpe, volatility, avg_return
    except Exception as e:
        print(f"⚠️ 计算风险指标失败: {e}")
        return 0, 0, 0


def get_dynamic_thresholds(volatility, base_target, base_callback):
    """根据波动率动态调整止盈阈值（优化 4）"""
    if volatility > 0.3:  # 高波动（年化 > 30%）
        # 波动大，提高止盈目标，放宽回撤容忍
        return base_target * 1.5, base_callback * 1.5
    elif volatility < 0.15:  # 低波动（年化 < 15%）
        # 波动小，降低止盈目标，收紧回撤容忍
        return base_target * 0.8, base_callback * 0.8
    else:
        return base_target, base_callback


def analyze_portfolio_correlation():
    """分析投资组合相关性（优化 3）"""
    try:
        nav_data = {}
        for code, info in PORTFOLIO.items():
            df = get_cached_data(code, "单位净值走势")
            if df is None:
                continue
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df = df.set_index('净值日期')
            nav_data[info['name']] = df['单位净值'].astype(float)
        
        if len(nav_data) < 2:
            return None, []
        
        # 合并数据并计算相关性
        nav_df = pd.DataFrame(nav_data).dropna()
        corr_matrix = nav_df.pct_change().corr()
        
        # 检测高相关性
        high_corr_pairs = []
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                corr_value = corr_matrix.iloc[i, j]
                if corr_value > 0.8:
                    high_corr_pairs.append({
                        'fund1': corr_matrix.index[i],
                        'fund2': corr_matrix.columns[j],
                        'correlation': corr_value
                    })
        
        return corr_matrix, high_corr_pairs
    except Exception as e:
        print(f"⚠️ 相关性分析失败: {e}")
        return None, []


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
    
    # 添加更多列显示风险指标
    table = PrettyTable()
    table.field_names = ["基金名称", "当前净值", "MA20", "动态成本", "收益率", "盈利金额", "回撤", "夏普比率", "波动率", "操作建议"]
    table.align["基金名称"] = "l"
    
    results = []
    
    # 先分析组合相关性
    print("\n🔍 分析投资组合相关性...")
    corr_matrix, high_corr_pairs = analyze_portfolio_correlation()
    
    for code, info in PORTFOLIO.items():
        curr_nav, ma20 = get_nav_and_ma(code)
        if curr_nav is None:
            continue
        
        # 更新峰值
        if curr_nav > peak_record.get(code, 0):
            peak_record[code] = curr_nav
        
        # 使用精确定投模拟（优化 1）
        curr_shares, curr_cost = simulate_investment_accurate(info, code, curr_nav)
        profit_rate = (curr_nav - curr_cost) / curr_cost
        drawdown = (peak_record[code] - curr_nav) / peak_record[code] if peak_record[code] > 0 else 0
        profit_amount = (curr_nav - curr_cost) * curr_shares
        
        # 计算风险指标（优化 2）
        sharpe, volatility, ann_return = calculate_risk_metrics(code)
        
        # 动态调整阈值（优化 4）
        dynamic_target, dynamic_callback = get_dynamic_thresholds(
            volatility, info['target'], info['callback']
        )
        
        is_broken_ma = curr_nav < ma20
        
        # 增强决策逻辑（包含优化 5：止损）
        if profit_rate <= EMERGENCY_STOP_LOSS:
            advice = "🛑 紧急止损"
            alert_level = "critical"
        elif profit_rate <= STOP_LOSS_THRESHOLD:
            if is_broken_ma:
                advice = "🛑 止损建议"
                alert_level = "high"
            else:
                advice = "⚠️ 接近止损"
                alert_level = "medium"
        elif profit_rate >= dynamic_target:
            # 使用动态阈值
            if drawdown >= dynamic_callback and is_broken_ma:
                advice = "🚨 趋势反转(止盈)"
                alert_level = "high"
            elif drawdown >= dynamic_callback:
                advice = "⚠️ 触发回撤"
                alert_level = "medium"
            else:
                # 根据夏普比率调整建议
                if sharpe > 1.5:
                    advice = "🔥 强势持有(高质量)"
                else:
                    advice = "🔥 强势持有"
                alert_level = "low"
        elif is_broken_ma:
            advice = "🛡️ 均线下方"
            alert_level = "low"
        else:
            advice = "🟢 定投中"
            alert_level = "low"
        
        table.add_row([
            info['name'], 
            f"{curr_nav:.4f}", 
            f"{ma20:.4f}", 
            f"{curr_cost:.4f}",
            f"{profit_rate:.2%}", 
            f"{profit_amount:.2f}", 
            f"{drawdown:.2%}",
            f"{sharpe:.2f}",
            f"{volatility:.1%}",
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
            "sharpe": sharpe,
            "volatility": volatility,
            "advice": advice,
            "alert_level": alert_level
        })
    
    # 保存更新后的峰值记录
    save_peak_record(peak_record)
    
    # 输出报告
    print(f"\n📊 增强型动态止盈监控 | 北京时间 (UTC+8): {get_now_beijing().strftime('%Y-%m-%d %H:%M:%S')}")
    print(table)
    
    # 输出相关性警告
    if high_corr_pairs:
        print("\n⚠️ 高相关性警告：")
        for pair in high_corr_pairs:
            print(f"  • {pair['fund1']} 和 {pair['fund2']} 相关性: {pair['correlation']:.2%}")
        print("  建议：考虑替换其中一只基金以提高分散度")
    
    print("\n📖 逻辑说明看板：")
    help_table = PrettyTable()
    help_table.field_names = ["优先级", "状态显示", "背后逻辑"]
    help_table.add_row(["0", "🛑 紧急止损", "亏损 ≥ 30% (保护本金)"])
    help_table.add_row(["1", "🛑 止损建议", "亏损 ≥ 20% + 跌破均线 (风险控制)"])
    help_table.add_row(["2", "🚨 趋势反转", "收益达标 + 跌破均线 + 回撤超标 (锁定利润)"])
    help_table.add_row(["3", "⚠️ 触发回撤", "收益达标 + 回撤超标 (警惕)"])
    help_table.add_row(["4", "🔥 强势持有", "收益达标 + 未触发回撤 (继续持有)"])
    help_table.add_row(["5", "🛡️ 均线下方", "收益未达标 + 跌破均线 (弱势观察)"])
    help_table.add_row(["6", "🟢 定投中", "正常定投状态"])
    print(help_table)
    
    print("\n💡 优化说明：")
    print("  ✅ 精确定投模拟：基于历史净值计算真实成本")
    print("  ✅ 止损保护：-20% 止损，-30% 紧急止损")
    print("  ✅ 夏普比率：评估风险调整后收益质量")
    print("  ✅ 动态阈值：根据波动率自动调整止盈参数")
    print("  ✅ 数据缓存：提高运行速度")
    
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
    
    # 检查是否需要发送通知（包含止损信号）
    alert_funds = [r for r in results if r['alert_level'] in ['critical', 'high']]
    
    if alert_funds:
        # 构建通知内容
        notification_title = f"📊 基金监控提醒 ({len(alert_funds)}只基金)"
        notification_content = f"## 📊 基金监控提醒\n\n"
        notification_content += f"**时间**: {get_now_beijing().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for fund in alert_funds:
            if fund['advice'].startswith("🛑"):
                icon = "🛑"
            elif fund['advice'] == "🚨 趋势反转(止盈)":
                icon = "🚨"
            else:
                icon = "⚠️"
            
            notification_content += f"### {icon} {fund['name']} - {fund['advice']}\n"
            notification_content += f"- 当前净值: **{fund['nav']:.4f}**\n"
            notification_content += f"- 动态成本: {fund['cost']:.4f}\n"
            notification_content += f"- 收益率: **{fund['profit_rate']:.2%}**\n"
            notification_content += f"- 盈利金额: **{fund['profit_amount']:.2f}元**\n"
            notification_content += f"- 回撤: {fund['drawdown']:.2%}\n"
            notification_content += f"- 夏普比率: {fund['sharpe']:.2f}\n"
            
            if fund['advice'].startswith("🛑"):
                notification_content += f"\n**建议**: 立即止损，保护本金\n"
            elif fund['advice'] == "🚨 趋势反转(止盈)":
                notification_content += f"\n**建议**: 考虑止盈锁定利润\n"
            else:
                notification_content += f"\n**建议**: 警惕回撤风险\n"
            
            notification_content += "\n---\n\n"
        
        notification_content += f"[查看详细报告](https://github.com/cryboy007/fund-monitor/actions)"
        
        # 发送通知
        send_serverchan_notification(notification_title, notification_content)
    else:
        print("\n💡 当前无需发送通知（未触发止盈、止损或回撤警告）")


if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
