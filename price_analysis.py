from binance import AsyncClient
from deepseek_sdk import DeepSeek
import streamlit as st
from leverage_engine import LeverageStrategyGenerator
import numpy as np
import asyncio

class CryptoAnalyzer:
    def __init__(self):
        self.deepseek = DeepSeek(api_key=st.secrets.api_keys.deepseek)
        self.client = None
        self.leverage_engine = None
        self.conversation_history = []
        
    async def connect_exchange(self):
        self.client = await AsyncClient.create(
            api_key=st.secrets.api_keys.binance_key,
            api_secret=st.secrets.api_keys.binance_secret
        )
    
    async def get_real_time_price(self, symbol="ETHUSDT"):
        """获取实时价格"""
        ticker = await self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    
    async def get_technical_indicators(self, symbol="ETHUSDT"):
        """获取技术指标（增强版）"""
        klines = await self.client.get_klines(symbol=symbol, interval='1h', limit=100)
        closes = [float(k[4]) for k in klines]
        
        # 计算关键指标
        sma_20 = sum(closes[-20:]) / 20
        rsi = self.calculate_rsi(closes)
        
        return {
            'closes': closes,
            'sma_20': sma_20,
            'rsi': rsi,
            'support': min(closes[-24:]),  # 24小时支撑
            'resistance': max(closes[-24:])  # 24小时阻力
        }
    
    def calculate_rsi(self, closes, period=14):
        """计算RSI指标"""
        deltas = np.diff(closes)
        gains = [x if x > 0 else 0 for x in deltas]
        losses = [-x if x < 0 else 0 for x in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    async def analyze_with_deepseek(self, user_query):
        """集成杠杆策略的深度分析"""
        # 获取实时数据
        current_price = await self.get_real_time_price()
        tech_data = await self.get_technical_indicators()
        
        # 初始化杠杆引擎
        if not self.leverage_engine or abs(self.leverage_engine.price - current_price) > 10:
            self.leverage_engine = LeverageStrategyGenerator(current_price)
        self.leverage_engine.update_indicators(tech_data)
        
        # 蒙特卡洛模拟
        mc_result = self.leverage_engine.monte_carlo_simulation()
        
        # 构建智能提示
        prompt = f"""
[角色设定]
你是一位专业加密货币交易员，精通杠杆交易和技术分析，当前日期：{st.session_state.current_date}

[实时市场数据]
- 当前价格: ${current_price:.2f}
- 20小时均线: ${tech_data['sma_20']:.2f}
- RSI(14): {tech_data['rsi']:.1f}
- 关键支撑: ${tech_data['support']:.2f}
- 关键阻力: ${tech_data['resistance']:.2f}
- 蒙特卡洛模拟结果: {mc_result}

[用户对话历史]
{self.format_conversation_history()}

[用户当前问题]
"{user_query}"

[你的任务]
1. 自然对话：像专业交易员一样回应用户
2. 杠杆策略分析：当用户询问交易建议时，必须包含：
   - 做多/做空方向建议
   - 详细止盈止损点位
   - 杠杆倍数建议（5x/10x/20x）
   - 仓位大小建议
   - 风险回报比
   - 爆仓价格预警
3. 胜率评估：结合蒙特卡洛模拟结果说明概率
4. 风险提示：强调杠杆交易风险
"""
        # 调用DeepSeek-V3
        response = self.deepseek.generate(
            model="deepseek-v3",
            prompt=prompt,
            max_tokens=1200,
            temperature=0.35
        )
        analysis = response.choices[0].text
        
        # 更新对话历史
        self.update_history(user_query, analysis)
        return analysis
    
    def format_conversation_history(self):
        """格式化对话历史"""
        return "\n".join([f"{'用户' if not h['ai'] else '助手'}: {h['text']}" 
                         for h in self.conversation_history[-4:]])
    
    def update_history(self, user_query, ai_response):
        """更新对话历史"""
        self.conversation_history.append({"ai": False, "text": user_query})
        self.conversation_history.append({"ai": True, "text": ai_response})
        # 保持最近6条消息
        if len(self.conversation_history) > 6:
            self.conversation_history = self.conversation_history[-6:]
