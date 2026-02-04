import akshare as ak
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class MarketSentimentMonitor:
    """A股市场情绪监控系统"""
    
    def __init__(self):
        self.history_days = 20  # 历史对比天数
        
    def get_market_breadth(self) -> Dict:
        """获取市场宽度数据（涨跌分布）"""
        try:
            df = ak.stock_zh_a_spot_em()
            total = len(df)
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = total - up_count - down_count
            
            # 涨跌停统计
            limit_up = len(df[df['涨跌幅'] >= 9.9])
            limit_down = len(df[df['涨跌幅'] <= -9.9])
            
            # 个股跌幅分布
            drop_5 = len(df[df['涨跌幅'] <= -5])
            drop_8 = len(df[df['涨跌幅'] <= -8])
            
            # 总成交额（亿元）
            total_volume = df['成交额'].sum() / 100000000
            
            return {
                'total': total,
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'breadth_ratio': up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5,
                'limit_up': limit_up,
                'limit_down': limit_down,
                'drop_5_pct': drop_5,
                'drop_8_pct': drop_8,
                'total_volume': total_volume
            }
        except Exception as e:
            print(f"市场宽度数据获取失败: {e}")
            return None
    
    def get_index_performance(self) -> Dict:
        """获取主要指数表现"""
        try:
            df = ak.stock_zh_index_spot_em(symbol="核心指数")
            
            indices = {
                '000001': 'shanghai',  # 上证指数
                '399001': 'shenzhen',  # 深证成指
                '000300': 'csi300',    # 沪深300
                '399006': 'chinext'    # 创业板指
            }
            
            result = {}
            for code, name in indices.items():
                row = df[df['代码'] == code]
                if not row.empty:
                    result[name] = {
                        'change_pct': float(row['涨跌幅'].values[0]),
                        'volume': float(row['成交额'].values[0]) / 100000000  # 转为亿元
                    }
            
            return result
        except Exception as e:
            print(f"指数数据获取失败: {e}")
            return None
    
    def get_north_capital_flow(self) -> Dict:
        """获取北向资金流向"""
        try:
            # 获取实时北向资金流向
            df = ak.stock_em_hsgt_north_net_flow_in(indicator="沪深港通")
            if df.empty:
                return None
            
            latest = df.iloc[0]
            net_flow = float(latest['北上资金'])  # 单位：万元
            
            return {
                'net_flow': net_flow / 10000,  # 转为亿元
                'signal': 'inflow' if net_flow > 0 else 'outflow'
            }
        except Exception as e:
            print(f"北向资金数据获取失败: {e}")
            return None
    
    def calculate_panic_score(self, breadth: Dict, indices: Dict, north_flow: Dict) -> Tuple[float, str]:
        """
        计算恐慌/贪婪评分 (0-100)
        0-20: 极度恐慌
        20-40: 恐慌
        40-60: 中性震荡
        60-80: 贪婪
        80-100: 极度贪婪
        """
        if not breadth or not indices:
            return 50, "数据不足"
        
        score = 50  # 基础分
        
        # 1. 市场宽度贡献 (权重30%)
        breadth_score = breadth['breadth_ratio'] * 60  # 0.5对应30分
        score += (breadth_score - 30) * 0.3
        
        # 2. 指数表现贡献 (权重10%)
        if 'csi300' in indices:
            csi300_change = indices['csi300']['change_pct']
            score += csi300_change * 2
        
        # 3. 极端情绪惩罚 (权重15%)
        limit_down_ratio = breadth['limit_down'] / breadth['total']
        drop_5_ratio = breadth['drop_5_pct'] / breadth['total']
        
        # 跌停家数超5%，极度恐慌
        if limit_down_ratio > 0.05:
            score -= 30
        elif limit_down_ratio > 0.02:
            score -= 15
        
        # 跌超5%家数占比
        if drop_5_ratio > 0.3:
            score -= 20
        elif drop_5_ratio > 0.15:
            score -= 10
        
        # 4. 北向资金贡献 (权重25%)
        if north_flow:
            net_flow = north_flow['net_flow']
            # 流入>50亿加分，流出>50亿扣分
            if net_flow > 50:
                score += 15
            elif net_flow > 20:
                score += 8
            elif net_flow < -50:
                score -= 15
            elif net_flow < -20:
                score -= 8
        
        # 5. 量能异常判断 (权重20%)
        # 缩量下跌 = 恐慌，放量下跌 = 恐慌性抛盘
        volume = breadth['total_volume']
        if 'csi300' in indices and indices['csi300']['change_pct'] < -1:
            if volume > 15000:  # 两市成交超1.5万亿且下跌，恐慌抛售
                score -= 10
            elif volume < 8000:  # 两市成交不足8000亿且下跌，量能衰竭
                score -= 8
        
        # 限制分数范围
        score = max(0, min(100, score))
        
        # 情绪等级判断
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
        """生成并打印市场情绪报告"""
        print(f"\n{'='*70}")
        print(f"📊 A股市场情绪监控报告 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # 获取数据
        breadth = self.get_market_breadth()
        indices = self.get_index_performance()
        north_flow = self.get_north_capital_flow()
        
        if not breadth:
            print("❌ 数据获取失败，请稍后重试")
            return
        
        # === 1. 市场宽度 ===
        print(f"【市场宽度】")
        print(f"  上涨: {breadth['up_count']:4d} 家 | 下跌: {breadth['down_count']:4d} 家 | 平盘: {breadth['flat_count']:4d} 家")
        print(f"  涨跌比: {breadth['breadth_ratio']:.2%} | 涨停: {breadth['limit_up']:3d} | 跌停: {breadth['limit_down']:3d}")
        print(f"  跌超5%: {breadth['drop_5_pct']:4d} 家 | 跌超8%: {breadth['drop_8_pct']:4d} 家")
        print(f"  两市成交额: {breadth['total_volume']:.2f} 亿元\n")
        
        # === 2. 指数表现 ===
        if indices:
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
        if north_flow and north_flow['net_flow'] < -100:
            warnings.append(f"⚠️  北向资金净流出超100亿，外资撤离")
        if score < 20:
            warnings.append(f"⚠️  极度恐慌，建议控制仓位，分批建仓")
        
        if warnings:
            print(f"【风险预警】")
            for w in warnings:
                print(f"  {w}")
            print()
        
        print(f"{'='*70}\n")


def is_trading_time() -> bool:
    """判断是否处于交易时段"""
    now = datetime.now()
    
    # 周末不交易
    if now.weekday() >= 5:
        return False
    
    current_time = now.strftime("%H:%M")
    
    # A股交易时间段
    # 9:30-11:30 (开盘期间延长2分钟获取开盘数据)
    # 13:00-15:00 (收盘期间延长2分钟获取收盘数据)
    if "09:25" <= current_time <= "11:32" or "13:00" <= current_time <= "15:02":
        return True
    
    return False


def main():
    """主函数"""
    monitor = MarketSentimentMonitor()
    
    print("🚀 A股市场情绪监控系统已启动...")
    print(f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 监控时段: 周一至周五 09:25-11:32, 13:00-15:02")
    print(f"🔄 更新频率: 交易时段每小时，非交易时段每10分钟检查\n")
    
    while True:
        try:
            if is_trading_time():
                monitor.print_report()
                # 交易时段每小时执行一次
                time.sleep(3600)
            else:
                now = datetime.now()
                print(f"[{now.strftime('%H:%M:%S')}] 当前非交易时段，脚本休眠中...")
                # 非交易时段每10分钟检查一次
                time.sleep(600)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  监控系统已停止")
            break
        except Exception as e:
            print(f"\n❌ 系统异常: {e}")
            print("⏸️  等待60秒后重试...\n")
            time.sleep(60)


if __name__ == "__main__":
    main()
