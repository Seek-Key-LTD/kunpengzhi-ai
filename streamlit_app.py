"""
记忆银行 — Memory Bank
=======================
鲲鹏志 AI · 深度发布展示平台
Streamlit v1.0
"""

import streamlit as st

st.set_page_config(
    page_title="记忆银行 · Memory Bank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1E88E5, #7C4DFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-title">🏦 记忆银行</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">'
        '从人类文明到智能体记忆 · 四层架构全景展示'
        '</div>',
        unsafe_allow_html=True
    )

st.divider()

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

with c1:
    st.markdown("### 📖 记忆银行叙事")
    st.markdown("从 4 本文明著作到智能体记忆管线——故事的起源、架构与实践。")
    if st.button("进入 →", key="btn1", use_container_width=True):
        st.switch_page("pages/1_记忆银行.py")

with c2:
    st.markdown("### 📊 全链路监控")
    st.markdown("Memory Bus 管线实时数据：mem0 → Neo4j → gbrain → DEX 确权。")
    if st.button("查看面板 →", key="btn2", use_container_width=True):
        st.switch_page("pages/2_实时数据.py")

with c3:
    st.markdown("### 🎭 八仙辩论 Demo")
    st.markdown("吕洞宾等八仙辩论书中观点——大模型智能体实时演绎。")
    if st.button("开始辩论 →", key="btn3", use_container_width=True):
        st.switch_page("pages/3_八仙辩论_Demo.py")

with c4:
    st.markdown("### 🔗 链上确权")
    st.markdown("Base Sepolia 链上存证：每一份记忆哈希上链，不可篡改。")
    if st.button("查看存证 →", key="btn4", use_container_width=True):
        st.switch_page("pages/4_链上确权.py")

st.divider()
st.markdown(
    "<div style='text-align:center;color:#999;font-size:0.85rem;padding:2rem 0;'>"
    "鲲鹏志 AI · 深度发布 · 2026"
    "</div>",
    unsafe_allow_html=True
)
