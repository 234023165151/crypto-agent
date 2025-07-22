import numpy as np
from scipy.stats import norm

class LeverageStrategyGenerator:
    def __init__(self, current_price):
        self.price = current_price
        self.indicators = {}
        
    def update_indicators(self, indicators):
        """更新技术指标数据"""
        self.indicators = indicators
        
    def calculate_volatility(self, closes):
        """计算价格波动率（关键风险指标）"""
        returns = np.diff(np.log(closes))
        return np.std(returns) * np.sqrt(365)  # 年化波动率
        
    def generate_strategy(self, risk_level='medium'):
        """
        生成杠杆交易策略
        risk_level: low/medium/high
        """
        # 风险参数配置
        risk_params = {
            'low': {'leverage': 5, 'win_rate': 0.65, 'stop_loss_pct': 0.03},
            'medium': {'leverage': 10, 'win_rate': 0.55, 'stop_loss_pct': 0.05},
            'high': {'leverage': 20, 'win_rate': 0.45, 'stop_loss_pct': 0.08}
        }
        params = risk_params[risk_level]
        
        # 计算关键价位
        direction = "多头" if self.price > self.indicators['sma_20'] else "空头"
        entry = self.price
        stop_loss = entry * (1 - params['stop_loss_pct']) if direction == "多头" else entry * (1 + params['stop_loss_pct'])
        
        # 止盈目标（基于波动率）
        volatility = self.calculate_volatility(self.indicators['closes'])
        take_profit_pct = min(0.15, volatility * 2)  # 动态止盈比例
        take_profit = entry * (1 + take_profit_pct) if direction == "多头" else entry * (1 - take_profit_pct)
        
        # 仓位管理计算
        risk_per_trade = 0.01  # 每笔交易风险1%本金
        position_size = (risk_per_trade * 100) / (abs(entry - stop_loss) * entry
        
        return {
            'direction': direction,
            'entry_price': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'leverage': params['leverage'],
            'position_size': f"{position_size:.2f} ETH",
            'win_rate': f"{params['win_rate']*100}%",
            'risk_reward': f"1:{round(take_profit_pct/params['stop_loss_pct'], 1)}",
            'liquidation_price': self.calculate_liquidation(entry, stop_loss, params['leverage'], direction)
        }
    
    def calculate_liquidation(self, entry, stop_loss, leverage, direction):
        """计算爆仓价格"""
        if direction == "多头":
            return entry * (1 - 0.9 / leverage)  # 维持保证金率90%
        else:
            return entry * (1 + 0.9 / leverage)
    
    def monte_carlo_simulation(self, n_simulations=1000):
        """蒙特卡洛模拟策略表现"""
        # 基于历史波动率模拟价格路径
        returns = np.diff(np.log(self.indicators['closes']))
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        simulated_profits = []
        for _ in range(n_simulations):
            rand_return = np.random.normal(mean_return, std_return)
            sim_price = self.price * np.exp(rand_return)
            profit = (sim_price - self.price) / self.price
            simulated_profits.append(profit)
        
        return {
            'avg_return': f"{np.mean(simulated_profits)*100:.2f}%",
            'success_rate': f"{np.mean(np.array(simulated_profits) > 0)*100:.1f}%"
        }