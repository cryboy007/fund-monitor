#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场情绪监控系统 - 演示版本
使用模拟数据展示完整报告格式
"""

from datetime import datetime
from typing import Dict, Tuple


class MarketSentimentMonitor:
    """A股市场情绪监控系统 - 演示版"""
    
    def __init__(self):
        self.history_days = 20
        
    def get_market_breadth_demo(self) -> Dict:
        """获取市场宽度数据（模拟数据）"""
        return {
            'total': 5200,
            'up_count': 2340,
            'down_count': 2650,
            'flat_count': 210,
            'breadth_ratio': 0.469,  # 46.9%
            'limit_up': 8,
            'limit_down': 35,
            'drop_5_pct': 856,
            'drop_8_pct': 234,
            'total_volume': 9876.54
        }
    
    def get_index_performance_demo(self) -> Dict:
        """获取主要指数表现（模拟数据）"""
        return {
            'shanghai': {'change_pct': -1.23, 'volume': 4532.12},
            'shenzhen': {'change_pct': -1.87, 'volume': 5344.42},
            'csi300': {'change_pct': -1.45, 'volume': 3876.23},
            'chinext': {'change_pct': -2.34, 'volume': 2123.56}
        }
    
    def get_north_capital_flow_demo(self) -> Dict:
        """获取北向资金流向（模拟数据）"""
        return {
            'net_flow': -38.76,  # 净流出38.76亿
            'signal': 'outflow'
        }
    
    def calculate_panic_score(self, breadth: Dict, indices: Dict, north_flow: Dict) -> Tuple[float, str]:
        """计算恐慌/贪婪评分 (0-100)"""
        if not breadth or not indices:
            return 50, "数据不足"
        
        score = 50
        
        # 1. 市场宽度贡献 (权重30%)
        breadth_score = breadth['breadth_ratio'] * 60
        score += (breadth_score - 30) * 0.3
        
        # 2. 指数表现贡献 (权重10%)
        if 'csi300' in indices:
            csi300_change = indices['csi300']['change_pct']
            score += csi300_change * 2
        
        # 3. 极端情绪惩罚 (权重15%)
        limit_down_ratio = breadth['limit_down'] / breadth['total']
        drop_5_ratio = breadth['drop_5_pct'] / breadth['total']
        
        if limit_down_ratio > 0.05:
            score -= 30
        elif limit_down_ratio > 0.02:
            score -= 15
        
        if drop_5_ratio > 0.3:
            score -= 20
        elif drop_5_ratio > 0.15:
            score -= 10
        
        # 4. 北向资金贡献 (权重25%)
        if north_flow and north_flow.get('net_flow') is not None:
            net_flow = north_flow['net_flow']
            if net_flow > 50:
                score += 15
            elif net_flow > 20:
                score += 8
            elif net_flow < -50:
                score -= 15
            elif net_flow < -20:
                score -= 8
        
        # 5. 量能异常判断 (权重20%)
        volume = breadth['total_volume']
        if 'csi300' in indices and indices['csi300']['change_pct'] < -1:
            if volume > 15000:
                score -= 10
            elif volume < 8000:
                score -= 8
        
        score = max(0, min(100, score))
        
        if score < 20:
            level = "极度恐慌 🔴🔴🔴"
        elif score < 40:
            level = "恐慌 🔴"
        elif score < 60:
            level = "中性震荡 🟡"
        elif score < 80:
            level = "贪婪 🟢"
        else:
            level = "极度贪婪 🟢🟢🟢"
        
        return round(score, 2), level
    
    def generate_grid_strategy_advice(self, score: float, breadth: Dict) -> str:
        """基于情绪分生成网格交易建议"""
        if score < 20:
            return "🔴 极度恐慌区：激进策略可分批抄底，网格下轨扩大20%，密集布单"
        elif score < 30:
            return "🔴 恐慌区：适合开启网格买入单，下轨-10%，间距2%"
        elif score < 40:
            return "🟠 弱势区：谨慎布局，网格间距放宽至3%，控制仓位50%"
        elif score < 60:
            return "🟡 震荡区：标准网格策略，上下轨±8%，间距2%"
        elif score < 70:
            return "🟢 强势区：偏向卖出网格，上轨+10%，锁定利润"
        elif score < 80:
            return "🟢 贪婪区：止盈为主，网格上轨缩小至+5%，快速平仓"
        else:
            limit_up_ratio = breadth['limit_up'] / breadth['total'] if breadth else 0
            if limit_up_ratio > 0.05:
                return "🔴 极度贪婪+涨停潮：市场过热！建议暂停网格，等待回调"
            else:
                return "🟢 极度贪婪：高位震荡，网格间距扩大至5%，防范回调"
    
    def print_report(self):
        """生成并打印市场情绪报告（演示版）"""
        print(f"\n{'='*70}")
        print(f"📊 A股市场情绪监控报告（演示版） | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        print("💡 使用模拟数据展示报告格式\n")
        
        # 获取模拟数据
        breadth = self.get_market_breadth_demo()
        indices = self.get_index_performance_demo()
        north_flow = self.get_north_capital_flow_demo()
        
        # === 1. 市场宽度 ===
        print(f"【市场宽度】")
        print(f"  上涨: {breadth['up_count']:4d} 家 | 下跌: {breadth['down_count']:4d} 家 | 平盘: {breadth['flat_count']:4d} 家")
        print(f"  涨跌比: {breadth['breadth_ratio']:.2%} | 涨停: {breadth['limit_up']:3d} | 跌停: {breadth['limit_down']:3d}")
        print(f"  跌超5%: {breadth['drop_5_pct']:4d} 家 | 跌超8%: {breadth['drop_8_pct']:4d} 家")
        print(f"  两市成交额: {breadth['total_volume']:.2f} 亿元\n")
        
        # === 2. 指数表现 ===
        print(f"【主要指数】")
        index_names = {
            'shanghai': '上证指数',
            'shenzhen': '深证成指',
            'csi300': '沪深300',
            'chinext': '创业板指'
        }
        for key, name in index_names.items():
            if key in indices:
                change = indices[key]['change_pct']
                emoji = "🔴" if change < 0 else "🟢"
                print(f"  {emoji} {name}: {change:+.2f}%")
        print()
        
        # === 3. 北向资金 ===
        if north_flow:
            flow = north_flow['net_flow']
            emoji = "💰" if flow > 0 else "💸"
            print(f"【北向资金】")
            print(f"  {emoji} 净流入: {flow:+.2f} 亿元 ({north_flow['signal']})\n")
        
        # === 4. 恐慌指数 ===
        score, level = self.calculate_panic_score(breadth, indices, north_flow)
        print(f"【恐慌/贪婪指数】")
        print(f"  综合评分: {score:.2f} / 100")
        print(f"  情绪等级: {level}\n")
        
        # === 5. 网格策略建议 ===
        advice = self.generate_grid_strategy_advice(score, breadth)
        print(f"【网格交易建议】")
        print(f"  {advice}\n")
        
        # === 6. 风险提示 ===
        warnings = []
        if breadth['limit_down'] > 100:
            warnings.append(f"⚠️  跌停家数达 {breadth['limit_down']} 家，市场恐慌严重")
        if breadth['drop_5_pct'] / breadth['total'] > 0.3:
            warnings.append(f"⚠️  超30%个股跌超5%，杀跌情绪蔓延")
        if north_flow and north_flow.get('net_flow', 0) < -100:
            warnings.append(f"⚠️  北向资金净流出超100亿，外资撤离")
        if score < 20:
            warnings.append(f"⚠️  极度恐慌，建议控制仓位，分批建仓")
        
        # 根据当前数据添加实际警告
        if breadth['limit_down'] > 30:
            warnings.append(f"⚠️  跌停家数达 {breadth['limit_down']} 家，需要警惕")
        if breadth['drop_5_pct'] / breadth['total'] > 0.15:
            warnings.append(f"⚠️  跌超5%个股占比 {breadth['drop_5_pct'] / breadth['total']:.1%}，杀跌明显")
        
        if warnings:
            print(f"【风险预警】")
            for w in warnings:
                print(f"  {w}")
            print()
        
        print(f"{'='*70}\n")
        
        # === 7. 评分说明 ===
        print("📖 评分模型说明：")
        print("  • 市场宽度 (30%)：涨跌家数比例，反映整体强弱")
        print("  • 资金流向 (25%)：北向资金净流入/流出，外资风向标")  
        print("  • 量能变化 (20%)：成交额与指数涨跌的配合关系")
        print("  • 极端情绪 (15%)：涨跌停、大跌个股占比")
        print("  • 指数表现 (10%)：沪深300等核心指数涨跌幅\n")
        
        print("✅ 演示完成！交易时段运行 market_sentiment.py 可获取实时数据")


if __name__ == "__main__":
    print("🚀 A股市场情绪监控系统 - 演示版本")
    print("="*70)
    print("📝 本演示使用模拟数据展示完整报告格式")
    print("="*70)
    
    monitor = MarketSentimentMonitor()
    
    try:
        monitor.print_report()
    except KeyboardInterrupt:
        print("\n\n⏹️  已停止")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
