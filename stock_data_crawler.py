#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场数据爬虫
数据源：东方财富网 + 新浪财经（备用）
"""

import requests
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import time


class StockDataCrawler:
    """A股数据爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.timeout = 15
        self.max_retries = 3
        
    def _request_with_retry(self, url: str, params: dict = None) -> Optional[dict]:
        """带重试的请求"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"请求失败（{self.max_retries}次重试后）: {e}")
                    return None
                time.sleep(1)
        return None
    
    def get_realtime_quotes(self) -> Optional[List[Dict]]:
        """
        获取沪深A股实时行情
        数据源：东方财富网
        """
        try:
            # 东方财富行情接口（使用HTTPS）
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            
            # 分页获取所有A股
            all_stocks = []
            page_size = 1000
            
            for page in range(1, 10):  # 最多10页
                params = {
                    'pn': page,
                    'pz': page_size,
                    'po': 1,
                    'np': 1,
                    'fields': 'f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18',
                    'fid': 'f3',
                    'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # 沪深A股
                }
                
                response = self._request_with_retry(url, params)
                if not response:
                    break
                
                try:
                    data = response.json()
                    if not data.get('data') or not data['data'].get('diff'):
                        break
                    
                    stocks = data['data']['diff']
                    all_stocks.extend(stocks)
                    
                    # 如果当前页数据少于page_size，说明已经是最后一页
                    if len(stocks) < page_size:
                        break
                except:
                    break
            
            if not all_stocks:
                return None
            
            # 转换为标准格式
            result = []
            for stock in all_stocks:
                try:
                    result.append({
                        '股票代码': stock.get('f12', ''),
                        '股票名称': stock.get('f14', ''),
                        '最新价': float(stock.get('f2', 0)) / 100 if stock.get('f2') else 0,
                        '涨跌幅': float(stock.get('f3', 0)) / 100 if stock.get('f3') else 0,
                        '涨跌额': float(stock.get('f4', 0)) / 100 if stock.get('f4') else 0,
                        '成交量': int(stock.get('f5', 0)),
                        '成交额': float(stock.get('f6', 0)),
                        '振幅': float(stock.get('f7', 0)) / 100 if stock.get('f7') else 0,
                        '最高': float(stock.get('f15', 0)) / 100 if stock.get('f15') else 0,
                        '最低': float(stock.get('f16', 0)) / 100 if stock.get('f16') else 0,
                        '开盘': float(stock.get('f17', 0)) / 100 if stock.get('f17') else 0,
                        '昨收': float(stock.get('f18', 0)) / 100 if stock.get('f18') else 0,
                    })
                except:
                    continue
            
            return result
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def get_index_quotes(self) -> Optional[Dict]:
        """
        获取主要指数实时行情
        数据源：新浪财经（更稳定）
        """
        try:
            # 指数代码映射
            index_codes = {
                's_sh000001': 'shanghai',   # 上证指数
                's_sz399001': 'shenzhen',   # 深证成指
                's_sh000300': 'csi300',     # 沪深300
                's_sz399006': 'chinext'     # 创业板指
            }
            
            # 新浪财经接口（添加防反爬headers）
            code_str = ','.join(index_codes.keys())
            url = f"https://hq.sinajs.cn/list={code_str}"
            
            # 临时修改headers
            old_referer = self.session.headers.get('Referer')
            self.session.headers.update({
                'Referer': 'https://finance.sina.com.cn/',
            })
            
            response = self._request_with_retry(url)
            
            # 恢复headers
            if old_referer:
                self.session.headers['Referer'] = old_referer
            
            if not response:
                return None
            
            response.encoding = 'gbk'
            text = response.text
            
            result = {}
            for sina_code, name in index_codes.items():
                try:
                    # 解析数据
                    pattern = f'var hq_str_{sina_code}="([^"]+)"'
                    match = re.search(pattern, text)
                    if not match:
                        continue
                    
                    data = match.group(1).split(',')
                    if len(data) < 6:
                        continue
                    
                    current_price = float(data[3])
                    prev_close = float(data[2])
                    change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    
                    result[name] = {
                        'change_pct': round(change_pct, 2),
                        'volume': float(data[5]) if len(data) > 5 else 0,
                        'current': current_price,
                        'prev_close': prev_close
                    }
                except Exception as e:
                    continue
            
            return result if result else None
        except Exception as e:
            print(f"获取指数行情失败: {e}")
            return None
    
    def get_north_capital_flow(self) -> Optional[Dict]:
        """
        获取北向资金流向
        数据源：东方财富网
        """
        try:
            # 东方财富北向资金接口（使用HTTPS）
            url = "https://push2.eastmoney.com/api/qt/kamt.rtmin/get"
            params = {
                'fields1': 'f1,f2,f3,f4',
                'fields2': 'f51,f52,f53,f54,f56',
                'ut': 'b2884a393a59ad64002292a3e90d46a5',
                'cb': 'jQuery183003743205523978607_' + str(int(time.time() * 1000)),
            }
            
            response = self._request_with_retry(url, params)
            if not response:
                return {'net_flow': 0, 'signal': 'unknown'}
            
            try:
                # 移除JSONP回调
                text = response.text
                json_str = re.search(r'\((.+)\)', text)
                if not json_str:
                    return {'net_flow': 0, 'signal': 'unknown'}
                
                data = json.loads(json_str.group(1))
                if not data.get('data'):
                    return {'net_flow': 0, 'signal': 'unknown'}
                
                # 获取最新数据
                north_data = data['data']
                
                # 北向资金净流入（单位：亿元）
                # 处理可能是list的情况
                net_value = north_data.get('s2c', 0)
                if isinstance(net_value, list) and len(net_value) > 0:
                    net_value = net_value[-1]  # 取最后一个值
                net_flow = float(net_value) / 10000 if net_value else 0
                
                return {
                    'net_flow': round(net_flow, 2),
                    'signal': 'inflow' if net_flow > 0 else 'outflow',
                    'shanghai': float(north_data.get('s2n', 0)) / 10000,  # 沪股通
                    'shenzhen': float(north_data.get('s2s', 0)) / 10000   # 深股通
                }
            except Exception as e:
                print(f"解析北向资金数据失败: {e}")
                return {'net_flow': 0, 'signal': 'unknown'}
        except Exception as e:
            print(f"获取北向资金失败: {e}")
            return {'net_flow': 0, 'signal': 'unknown'}


def test_crawler():
    """测试爬虫功能"""
    print("🚀 测试数据爬虫\n")
    print("="*70)
    
    crawler = StockDataCrawler()
    
    # 1. 测试实时行情
    print("\n1️⃣ 测试实时行情获取...")
    quotes = crawler.get_realtime_quotes()
    if quotes:
        print(f"   ✅ 成功！获取到 {len(quotes)} 只股票数据")
        print(f"   前3只股票：")
        for stock in quotes[:3]:
            print(f"      {stock['股票代码']} {stock['股票名称']}: {stock['最新价']:.2f} ({stock['涨跌幅']:+.2f}%)")
    else:
        print("   ❌ 失败")
    
    # 2. 测试指数行情
    print("\n2️⃣ 测试指数行情获取...")
    indices = crawler.get_index_quotes()
    if indices:
        print(f"   ✅ 成功！获取到 {len(indices)} 个指数")
        index_names = {
            'shanghai': '上证指数',
            'shenzhen': '深证成指',
            'csi300': '沪深300',
            'chinext': '创业板指'
        }
        for key, name in index_names.items():
            if key in indices:
                print(f"      {name}: {indices[key]['change_pct']:+.2f}%")
    else:
        print("   ❌ 失败")
    
    # 3. 测试北向资金
    print("\n3️⃣ 测试北向资金获取...")
    north = crawler.get_north_capital_flow()
    if north and north['net_flow'] != 0:
        print(f"   ✅ 成功！")
        print(f"      净流入: {north['net_flow']:+.2f} 亿元")
        if 'shanghai' in north:
            print(f"      沪股通: {north['shanghai']:+.2f} 亿元")
            print(f"      深股通: {north['shenzhen']:+.2f} 亿元")
    else:
        print("   ⚠️  未获取到数据（可能非交易时段）")
    
    print("\n" + "="*70)
    print("✅ 测试完成！")


if __name__ == "__main__":
    test_crawler()
