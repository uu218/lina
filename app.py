import streamlit as st
import json
import os

# 设置页面宽屏显示
st.set_page_config(page_title="AI 申论批改工作台", layout="wide")

st.title("📝 AI 申论批改结果分析")

# 读取生成的 JSON 文件
json_file = "evaluation_result_all.json"

if not os.path.exists(json_file):
    st.warning("暂未找到批改结果文件，请先运行 main.py 生成数据。")
else:
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    if not results:
        st.info("数据文件为空。")
    
    # 侧边栏：题目导航
    st.sidebar.header("导航栏")
    selected_q_idx = st.sidebar.selectbox(
        "选择要查看的题目：", 
        range(len(results)), 
        format_func=lambda x: f"第 {x+1} 题: {results[x]['题目'][:10]}..."
    )
    
    # 获取当前选中的题目数据
    current_data = results[selected_q_idx]
    report = current_data['最终批改报告']
    
    # === 顶部概览区 ===
    st.header(current_data['题目'])
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric(label="最终得分", value=report['total_score'])
    with col2:
        st.info(f"**专家总评：**\n{report['summary_feedback']}")
        
    st.divider()

    # === 中部详情区：各维度打分 ===
    st.subheader("📊 采分点明细")
    for dim in report['dimension_grades']:
        with st.expander(f"{dim['dimension_name']} (得分: {dim['score']})", expanded=True):
            st.write(f"*{dim['comments']}*")
            
            # 遍历该维度下的所有采分点
            for point in dim['match_details']:
                if point['is_matched']:
                    st.success(f"✅ **命中 | 得分: {point['score_awarded']}**")
                    st.write(f"**你的原文:** {point['evidence']}")
                else:
                    st.error(f"❌ **未命中 | 得分: 0**")
                    st.write(f"**扣分原因:** {point['reason']}")
                st.markdown("---")

    # === 底部建议区 ===
    st.subheader("💡 升格修改建议")
    for i, suggestion in enumerate(report['upgrade_suggestions'], 1):
        st.write(f"{i}. {suggestion}")