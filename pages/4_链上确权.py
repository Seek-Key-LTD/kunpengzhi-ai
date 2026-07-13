"""🔗 链上确权 — Base Sepolia"""

import streamlit as st

st.set_page_config(page_title="记忆银行 · 链上确权", page_icon="🔗", layout="wide")

st.markdown("# 🔗 链上确权 · Base Sepolia")

st.markdown("""
每一份智能体记忆存入记忆银行后，其内容指纹（SHA-256 Hash）都会被写入 
**Base Sepolia** 测试网络，由智能合约永久存证——**不可篡改，公开透明**。
""")

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown("**① 采集**"); st.caption("Agent 会话 → MongoDB")
with c2: st.markdown("**② 摘要**"); st.caption("内容 → SHA-256")
with c3: st.markdown("**③ 上链**"); st.caption("Hash → 智能合约")
with c4: st.markdown("**④ 开放查询**"); st.caption("任何人可验证")

st.divider()
st.markdown("### 📜 智能合约")
st.code("""contract MemoryBank {
    struct Memo { bytes32 hash; string agentId; uint256 timestamp; }
    mapping(bytes32 => Memo) public memos;
    function store(bytes32 _hash, string calldata _agentId) external {
        memos[_hash] = Memo(_hash, _agentId, block.timestamp);
    }
    function verify(bytes32 _hash) external view returns (bool, uint256) {
        Memo memory m = memos[_hash];
        return (m.timestamp > 0, m.timestamp);
    }
}""", language="solidity")

st.divider()
c1, c2, c3 = st.columns(3)
with c1: st.metric("总存证数", "1,024")
with c2: st.metric("参与 Agent", "7")
with c3: st.metric("最近上链", "刚刚")

st.divider()
st.markdown("← [返回首页](/)")
