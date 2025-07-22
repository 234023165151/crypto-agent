import streamlit as st
import asyncio
from datetime import datetime
from price_analysis import CryptoAnalyzer

# 初始化页面
st.set_page_config(page_title="杠杆交易分析助手", layout="wide", page_icon="🚀")
st.title("💰 加密货币杠杆交易智能助手")
st.caption(f"DeepSeek-V3驱动 | 实时风险分析 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 初始化会话状态
if "analyzer" not in st.session_state:
    st.session_state.analyzer = CryptoAnalyzer()
    st.session_state.current_date = datetime.now().strftime("%Y-%m-%d")
    asyncio.run(st.session_state.analyzer.connect_exchange())
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的杠杆交易助手，请随时询问ETH价格分析或交易策略"}
    ]

# 侧边栏 - 风险偏好设置
with st.sidebar:
    st.subheader("⚙️ 交易偏好设置")
    risk_level = st.selectbox("风险承受等级", ["低风险", "中等风险", "高风险"], index=1)
    leverage_pref = st.slider("偏好杠杆倍数", 1, 20, 10)
    st.divider()
    st.info("""
    **策略说明**：
    - 低风险：5x杠杆，<3%止损
    - 中风险：10x杠杆，<5%止损
    - 高风险：20x杠杆，<8%止损
    """)

# 实时价格显示
price_col, vol_col = st.columns(2)
with price_col:
    price_placeholder = st.empty()
with vol_col:
    vol_placeholder = st.empty()

# 显示对话历史
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# 异步更新价格
async def update_market_data():
    while True:
        try:
            price = await st.session_state.analyzer.get_real_time_price()
            price_placeholder.metric("ETH/USDT 价格", f"${price:,.2f}")
            
            # 添加简单波动指示器
            change = price - (st.session_state.last_price if 'last_price' in st.session_state else price)
            vol_placeholder.metric("波动情况", 
                                  f"{'↑' if change >=0 else '↓'} ${abs(change):.2f}",
                                  delta=f"{change/price*100:.2f}%")
            st.session_state.last_price = price
        except Exception as e:
            st.error(f"数据获取错误: {str(e)}")
        await asyncio.sleep(5)

if "price_task" not in st.session_state:
    st.session_state.price_task = asyncio.create_task(update_market_data())

# 用户输入处理
if user_input := st.chat_input("输入交易问题，例如：当前适合杠杆做多吗？"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # 获取分析结果
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🧠 深度分析中..."):
            response = await st.session_state.analyzer.analyze_with_deepseek(user_input)
            st.write(response)
    
    # 添加助手消息
    st.session_state.messages.append({"role": "assistant", "content": response})

# 安全关闭
import atexit
@atexit.register
def cleanup():
    if "price_task" in st.session_state:
        st.session_state.price_task.cancel()