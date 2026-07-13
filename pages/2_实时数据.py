"""📊 全链路监控 — Metabase 动态嵌入"""

import streamlit as st
import jwt
import time

st.set_page_config(page_title="记忆银行 · 实时数据", page_icon="📊", layout="wide")

st.markdown("# 📊 Memory Bus 全链路监控")

METABASE_SECRET_KEY = "1802f07139e23eb931554f4b2cd83c6be4985fe305459b24968717b9d22652e5"
METABASE_INSTANCE = "https://metabase.git4ta.fun"

def generate_jwt_token(dashboard_id=39, expiry_minutes=10):
    payload = {
        "resource": {"dashboard": dashboard_id},
        "params": {},
        "exp": round(time.time()) + (expiry_minutes * 60)
    }
    return jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

st.caption("Token 每 10 分钟自动刷新。")

token = generate_jwt_token()
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <script defer src="{METABASE_INSTANCE}/app/embed.js"></script>
    <style>
        body {{ margin: 0; }}
        metabase-dashboard {{ width: 100%; height: 100vh; border: none; }}
    </style>
</head>
<body>
    <metabase-dashboard 
        token="{token}"
        with-title="true"
        with-downloads="true"
    ></metabase-dashboard>
</body>
</html>
"""
st.components.v1.html(html_content, height=800, scrolling=True)

st.divider()
st.markdown("### 📈 关键指标")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("已接入 Agent", "28", delta="+1")
with c2: st.metric("记忆会话", "360", delta="+12")
with c3: st.metric("知识实体", "204", delta="+8")
with c4: st.metric("链上证数", "1,024", delta="+7")

st.divider()
st.markdown("← [返回首页](/)")
