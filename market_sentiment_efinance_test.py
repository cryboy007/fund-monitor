#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场情绪监控系统 - efinance测试版
"""

import efinance as ef
from datetime import datetime


def test_efinance():
    """测试 efinance 数据获取"""
    print("🔍 测试 efinance 数据源\n")
    
    # 1. 测试实时行情
    print("1️⃣ 测试实时行情获取...")
    try:
        df = ef.stock.get_realtime_quotes()
        if df is not None and not df.empty:
            # 过滤A股
            df_a = df[df['股票代码'].str.match(r'^(00|30|60|68)\d{4}$')]
            print(f"   ✅ 成功！获取到 {len(df_a)} 只A股数据")
            print(f"   数据示例：\n{df_a[['股票名称', '股票代码', '最新价', '涨跌幅']].head(3)}\n")
        else:
            print("   ❌ 未获取到数据\n")
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")
    
    # 2. 测试指数数据
    print("2️⃣ 测试指数数据获取...")
    try:
        index_codes = {
            '1.000001': '上证指数',
            '0.399001': '深证成指',
            '1.000300': '沪深300',
            '0.399006': '创业板指'
        }
        
        for code, name in index_codes.items():
            try:
                df = ef.stock.get_quote_history(code, klt=101)
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    print(f"   ✅ {name}: {latest['涨跌幅']:+.2f}%")
            except Exception as e:
                print(f"   ❌ {name}: {e}")
        print()
    except Exception as e:
        print(f"   ❌ 整体失败: {e}\n")
    
    # 3. 测试北向资金
    print("3️⃣ 测试北向资金数据...")
    try:
        # 尝试不同的可能接口
        methods = [
            ('get_quote_history', 'HK_FUND_NORTHBOUND_FLOW'),
            ('get_history_bill', 'HK_FUND'),
        ]
        
        success = False
        for method_name, symbol in methods:
            try:
                if hasattr(ef.stock, method_name):
                    method = getattr(ef.stock, method_name)
                    df = method(symbol, klt=101)
                    if df is not None and not df.empty:
                        print(f"   ✅ 方法 {method_name} 成功")
                        print(f"   数据列: {list(df.columns)}")
                        print(f"   最新数据:\n{df.tail(1)}")
                        success = True
                        break
            except:
                continue
        
        if not success:
            print("   ⚠️  未找到北向资金数据，将使用默认值")
        print()
    except Exception as e:
        print(f"   ❌ 失败: {e}\n")
    
    print("=" * 70)
    print("✅ 测试完成！")
    print("\n💡 如果上述测试成功，说明 efinance 可以正常使用")


if __name__ == "__main__":
    print("🚀 efinance 数据源测试")
    print("="*70)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    test_efinance()
