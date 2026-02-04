#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪监控 - 单次执行版本
用于 GitHub Actions
"""

from market_sentiment import MarketSentimentMonitor
import sys
from datetime import datetime


def main():
    """执行一次市场情绪监控"""
    print(f"\n🚀 GitHub Actions 自动执行")
    print(f"⏰ 北京时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    try:
        monitor = MarketSentimentMonitor()
        monitor.print_report()
        
        print("\n✅ 执行成功！")
        return 0
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
