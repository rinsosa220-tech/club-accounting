import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# 親ディレクトリのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sheets import (
    load_collection, save_collection, 
    load_transport_balance, save_transport_balance
)

# ページ設定
st.set_page_config(
    page_title="徴収管理 | 部活動 会計管理",
    page_icon="👥",
    layout="wide"
)

# 認証チェック
if "role" not in st.session_state or "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ このページを表示するにはログインが必要です。メインページからログインしてください。")
    st.stop()

CURRENT_ROLE = st.session_state.get("role", "guest")
IS_ADMIN = CURRENT_ROLE == "admin"

def add_transport_balance_entry(date, item, income, expense, wallet='現金'):
    """交通費会計に1行追加（財布別残高対応）"""
    df = load_transport_balance()
    if len(df) > 0 and '財布' not in df.columns:
        df['財布'] = '現金'
    wallet_df = df[df['財布'] == wallet] if len(df) > 0 else pd.DataFrame()
    current = int(wallet_df['残高'].iloc[-1]) if len(wallet_df) > 0 else 0
    new_balance = current + income - expense
    new_entry = pd.DataFrame({
        '日付': [date], '項目': [item], '財布': [wallet],
        '収入': [income], '支出': [expense], '残高': [new_balance]
    })
    df = pd.concat([df, new_entry], ignore_index=True)
    save_transport_balance(df)
    return new_balance

PRIMARY_COLOR = "#670317"
PRIMARY_LIGHT = "#8b1a33"

# CSS
st.markdown(f"""
<style>
    .app-header {{ text-align: center; padding: 16px 0 20px 0; }}
    .app-title {{ font-size: 2rem; font-weight: 800; color: {PRIMARY_COLOR}; margin-bottom: 4px; }}
    .app-subtitle {{ color: #666; font-size: 0.95rem; }}
    .section-title {{ font-size: 1.15rem; font-weight: 700; color: #333;
        padding-left: 14px; border-left: 4px solid {PRIMARY_COLOR}; margin-bottom: 18px; }}
    .card {{ background: #fff; border-radius: 16px; padding: 24px;
        margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    .stButton > button {{ border-radius: 10px !important; font-weight: 600; }}

    .kpi-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }}
    .kpi-card-main {{ background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        border-radius: 14px; padding: 20px 12px; text-align: center; box-shadow: 0 6px 16px rgba(103,3,23,0.25); }}
    .kpi-card-main .kpi-label {{ color: rgba(255,255,255,0.9); font-size: 0.8rem; margin-bottom: 6px; }}
    .kpi-card-main .kpi-value {{ color: #fff; font-size: 1.8rem; font-weight: 800; white-space: nowrap; }}
    .kpi-card-sub {{ background: #fff; border-radius: 14px; padding: 18px 10px; text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06); border: 1px solid #eee; }}
    .kpi-card-sub .kpi-label {{ font-size: 0.8rem; color: #666; margin-bottom: 6px; }}
    .kpi-card-sub .kpi-value {{ font-size: 1.5rem; font-weight: 800; color: {PRIMARY_COLOR}; white-space: nowrap; }}

    @media (max-width: 768px) {{
        .app-title {{ font-size: 1.5rem !important; }}
        .app-subtitle {{ font-size: 0.8rem !important; }}
        .section-title {{ font-size: 1rem !important; }}
        .card {{ padding: 14px !important; }}
        .kpi-grid {{ grid-template-columns: repeat(1, 1fr) !important; gap: 8px !important; }}
    }}
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown("""
<div class="app-header">
    <p class="app-title">👥 部員徴収管理</p>
    <p class="app-subtitle">遠征費などの部員からの集金を管理します</p>
</div>
""", unsafe_allow_html=True)

col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
with col_m2:
    if IS_ADMIN:
        st.success("👤 管理者モード - 編集が可能")
    else:
        st.info("👁️ 閲覧モード - データの変更はできません")

# データ読み込み
if 'tc_collection' not in st.session_state:
    st.session_state.tc_collection = load_collection()

coll_df = st.session_state.tc_collection.copy()
if len(coll_df) > 0:
    coll_df['名前'] = coll_df['名前'].fillna('').astype(str)
    ev_cols = [c for c in coll_df.columns if c != '名前']
    for c in ev_cols:
        coll_df[c] = pd.to_numeric(coll_df[c], errors='coerce').fillna(0).astype(int)
    
    coll_df['未払計'] = coll_df[ev_cols].sum(axis=1) if len(ev_cols) > 0 else 0
    total_unpaid = coll_df['未払計'].sum()
    unpaid_count = len(coll_df[coll_df['未払計'] > 0])
    total_count = len(coll_df)
    paid_rate = (total_count - unpaid_count) / total_count if total_count > 0 else 0
else:
    ev_cols = []
    total_unpaid = 0
    unpaid_count = 0
    total_count = 0
    paid_rate = 0

# KPI表示
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card-main">
        <div class="kpi-label">💴 未回収総額</div>
        <div class="kpi-value">¥{total_unpaid:,}</div>
    </div>
    <div class="kpi-card-sub">
        <div class="kpi-label">👥 未払者</div>
        <div class="kpi-value">{unpaid_count} / {total_count} 名</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">📊 徴収データ</p>', unsafe_allow_html=True)
    
    if IS_ADMIN:
        with st.expander("➕ 新しい遠征（列）を追加する"):
            new_event_name = st.text_input("遠征名 (例: 春季大会)")
            if st.button("追加"):
                if new_event_name and new_event_name not in coll_df.columns:
                    st.session_state.tc_collection[new_event_name] = 0
                    save_collection(st.session_state.tc_collection)
                    st.success(f"{new_event_name} を追加しました！")
                    st.rerun()
                elif new_event_name in coll_df.columns:
                    st.warning("その遠征名は既に存在します。")

    if len(coll_df) > 0:
        disp_cols = ['名前'] + ev_cols + ['未払計']
        disp_coll = coll_df[disp_cols].copy()
        
        col_cfg = {
            "名前": st.column_config.TextColumn("👤 名前", disabled=True, width="medium"),
            "未払計": st.column_config.NumberColumn("📊 未払計", format="¥%d", disabled=True, width="small"),
        }
        for c in ev_cols:
            col_cfg[c] = st.column_config.NumberColumn(c, format="¥%d", step=100, width="small")

        if IS_ADMIN:
            edited_coll = st.data_editor(disp_coll, use_container_width=True, hide_index=True,
                height=500, column_config=col_cfg, key="coll_editor_tc")

            cc1, cc2, _ = st.columns([1, 1, 4])
            with cc1:
                if st.button("💾 徴収状況を保存", type="primary", use_container_width=True):
                    save_data = st.session_state.tc_collection.copy()
                    for c in ev_cols:
                        if c in edited_coll.columns:
                            save_data[c] = edited_coll[c]
                    save_collection(save_data)
                    del st.session_state['tc_collection']
                    st.success("✅ 保存しました")
                    st.rerun()
            with cc2:
                if st.button("↩️ 元に戻す", use_container_width=True):
                    del st.session_state['tc_collection']
                    st.rerun()
        else:
            st.dataframe(disp_coll, use_container_width=True, hide_index=True, height=500, column_config=col_cfg)
    else:
        st.info("📭 データがありません")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # 徴収完了処理
    if len(ev_cols) > 0 and IS_ADMIN:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">✅ 徴収完了処理</p>', unsafe_allow_html=True)

        sel_event = st.selectbox("イベント選択", ev_cols, key="complete_event_tc")
        st.caption("全員から徴収が完了したら、ボタンを押して未払い残高をリセットします。交通費の財布への計上は別途手動で行ってください。")

        if st.button("✅ 全員徴収完了として記録", type="primary", use_container_width=True):
            c_data = st.session_state.tc_collection.copy()
            collected = int(pd.to_numeric(c_data[sel_event], errors='coerce').fillna(0).sum())
            c_data[sel_event] = 0
            save_collection(c_data)
            
            # キャッシュクリア
            if 'tc_collection' in st.session_state:
                del st.session_state['tc_collection']
            st.success(f"✅ {sel_event}の徴収完了処理を行いました（計: ¥{collected:,}）")
            st.balloons()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 部員別の未払い詳細
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">⚠️ 未払い者リスト</p>', unsafe_allow_html=True)
    if len(coll_df) > 0 and len(ev_cols) > 0:
        unpaid_members = coll_df[coll_df['未払計'] > 0][['名前', '未払計']].sort_values('未払計', ascending=False)
        if len(unpaid_members) > 0:
            for _, row in unpaid_members.iterrows():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:10px 16px;margin-bottom:6px;background:#fff5f5;border-radius:10px;
                    border-left:4px solid {PRIMARY_COLOR};">
                    <span style="font-weight:600;">👤 {row['名前']}</span>
                    <span style="font-weight:800;color:{PRIMARY_COLOR};">¥{int(row['未払計']):,}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;padding:20px;color:#999;">🎉 全員徴収済み</div>', unsafe_allow_html=True)
    else:
        st.info("データがありません")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;padding:24px 0 12px 0;color:#999;font-size:0.8rem;">
    部員徴収管理 v1.0 | 部活動 会計管理システム
</div>
""", unsafe_allow_html=True)
