import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# 親ディレクトリのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ページ設定
st.set_page_config(
    page_title="返済リスト | 部活動 会計管理",
    page_icon="💸",
    layout="wide"
)

# ======================
# 🔐 認証チェック（メインページでログイン済みか確認）
# ======================
if "role" not in st.session_state:
    st.warning("⚠️ このページを表示するにはログインが必要です。メインページからログインしてください。")
    st.stop()

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ ログインしてください。")
    st.stop()

# 権限
CURRENT_ROLE = st.session_state.get("role", "guest")
IS_ADMIN = CURRENT_ROLE == "admin"

from utils.sheets import load_reimbursements, save_reimbursements, load_members

# テーマカラー
PRIMARY_COLOR = "#670317"
PRIMARY_LIGHT = "#8b1a33"
SECONDARY_COLOR = "#495057"

# 決済方法
PAYMENT_METHODS = ["現金 (財布)", "銀行口座"]

# ======================
# カスタムCSS
# ======================
st.markdown(f"""
<style>
    .app-header {{
        text-align: center;
        padding: 16px 0 20px 0;
    }}
    .app-title {{
        font-size: 2rem;
        font-weight: 800;
        color: {PRIMARY_COLOR};
        margin-bottom: 4px;
    }}
    .app-subtitle {{
        color: #666;
        font-size: 0.95rem;
    }}
    .section-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: #333;
        padding-left: 14px;
        border-left: 4px solid {PRIMARY_COLOR};
        margin-bottom: 18px;
    }}
    .card {{
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .kpi-urgent {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        border-radius: 14px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(103,3,23,0.25);
    }}
    .kpi-urgent .kpi-label {{
        color: rgba(255,255,255,0.9);
        font-size: 0.85rem;
        margin-bottom: 6px;
    }}
    .kpi-urgent .kpi-value {{
        color: #fff;
        font-size: 2.4rem;
        font-weight: 800;
    }}
    .kpi-card {{
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
        border: 1px solid #eee;
    }}
    .kpi-card .kpi-label {{
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 6px;
    }}
    .kpi-card .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {PRIMARY_COLOR};
    }}
    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 600;
    }}

    /* スマホ対応 */
    @media (max-width: 768px) {{
        .app-title {{ font-size: 1.5rem !important; }}
        .app-subtitle {{ font-size: 0.8rem !important; }}
        .section-title {{ font-size: 1rem !important; }}
        .card {{ padding: 14px !important; }}
        .kpi-urgent .kpi-value {{ font-size: 1.6rem !important; }}
        .kpi-card .kpi-value {{ font-size: 1.3rem !important; }}
        [data-testid="stMetricValue"] {{ font-size: 1.2rem !important; }}
        [data-testid="stMetricLabel"] {{ font-size: 0.7rem !important; }}
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 4px !important;
        }}
        [data-testid="column"] {{
            min-width: 45% !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 0px !important; }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.7rem !important;
            padding: 6px 6px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ======================
# ヘッダー
# ======================
st.markdown("""
<div class="app-header">
    <p class="app-title">💸 返済リスト</p>
    <p class="app-subtitle">部員が立て替えたお金の返済管理</p>
</div>
""", unsafe_allow_html=True)

# 権限表示
col_mode1, col_mode2, col_mode3 = st.columns([1, 2, 1])
with col_mode2:
    if IS_ADMIN:
        st.success("👤 管理者モード - 登録・返済処理が可能")
    else:
        st.info("👁️ 閲覧モード - データの変更はできません")

# ======================
# データ読み込み
# ======================
if 'reimbursement_data' not in st.session_state:
    st.session_state.reimbursement_data = load_reimbursements()

reimb_df = st.session_state.reimbursement_data.copy()

# ======================
# KPI表示
# ======================
if len(reimb_df) > 0:
    pending = reimb_df[reimb_df['状態'] == '未返済']
    completed = reimb_df[reimb_df['状態'] == '返済済']
    pending_total = int(pending['金額'].sum())
    completed_total = int(completed['金額'].sum())
    pending_count = len(pending)
    pending_people = pending['立替者'].nunique() if pending_count > 0 else 0
else:
    pending_total = 0
    completed_total = 0
    pending_count = 0
    pending_people = 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="kpi-urgent">
        <div class="kpi-label">💰 未返済の合計</div>
        <div class="kpi-value">¥{pending_total:,}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📋 未返済の件数</div>
        <div class="kpi-value">{pending_count} 件</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">👥 返済対象の人数</div>
        <div class="kpi-value">{pending_people} 人</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">✅ 返済済みの合計</div>
        <div class="kpi-value">¥{completed_total:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================
# タブ構成
# ======================
tab1, tab2, tab3 = st.tabs(["📋 未返済リスト", "➕ 新規登録", "✅ 返済済み履歴"])

# ======================
# タブ1: 未返済リスト
# ======================
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">📋 未返済の立替金一覧</p>', unsafe_allow_html=True)

    if len(reimb_df) > 0:
        pending_df = reimb_df[reimb_df['状態'] == '未返済'].copy()
    else:
        pending_df = pd.DataFrame(columns=['日付', '立替者', '金額', '内容', '決済方法', '状態', '返済日', '備考'])

    if len(pending_df) > 0:
        # 立替者ごとの集計
        st.markdown('<p class="section-title">👥 立替者ごとの未返済額</p>', unsafe_allow_html=True)
        summary = pending_df.groupby('立替者')['金額'].agg(['sum', 'count']).reset_index()
        summary.columns = ['立替者', '未返済合計', '件数']
        summary = summary.sort_values('未返済合計', ascending=False).reset_index(drop=True)

        summary_cols = st.columns(min(len(summary), 4))
        for i, (_, row) in enumerate(summary.iterrows()):
            if i < 4:
                with summary_cols[i % 4]:
                    st.metric(
                        f"👤 {row['立替者']}",
                        f"¥{int(row['未返済合計']):,}",
                        f"{int(row['件数'])} 件"
                    )

        st.divider()

        # 未返済リスト（編集可能テーブル）
        display_pending = pending_df[['日付', '立替者', '金額', '内容', '決済方法', '備考']].copy()
        display_pending = display_pending.sort_values('日付', ascending=False).reset_index(drop=True)

        if IS_ADMIN:
            # 返済処理用のチェックボックスを追加
            display_pending.insert(0, "返済✓", False)

            edited_pending = st.data_editor(
                display_pending,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "返済✓": st.column_config.CheckboxColumn(
                        "返済✓", help="チェックして「返済処理」ボタンを押すと返済済みになります",
                        default=False, width="small"
                    ),
                    "日付": st.column_config.TextColumn("📅 日付", width="small"),
                    "立替者": st.column_config.TextColumn("👤 立替者", width="medium"),
                    "金額": st.column_config.NumberColumn("💴 金額", format="¥%d", width="small"),
                    "内容": st.column_config.TextColumn("📝 内容", width="large"),
                    "決済方法": st.column_config.SelectboxColumn(
                        "💳 決済方法", options=PAYMENT_METHODS, width="small"
                    ),
                    "備考": st.column_config.TextColumn("📎 備考", width="medium")
                },
                key="pending_editor"
            )

            # アクションバー
            act1, act2, act3 = st.columns([1.5, 1.5, 4])
            with act1:
                repay_clicked = st.button("✅ チェック分を返済済みにする", type="primary", use_container_width=True)
            with act2:
                reload_clicked = st.button("↩️ 最新データに戻す", use_container_width=True, key="reload_pending")

            if repay_clicked:
                checked_rows = edited_pending[edited_pending["返済✓"] == True]
                if len(checked_rows) > 0:
                    today = datetime.now().strftime('%Y-%m-%d')
                    full_data = st.session_state.reimbursement_data.copy()

                    repaid_count = 0
                    repaid_total = 0
                    for _, checked_row in checked_rows.iterrows():
                        # 元データの該当行を特定（日付 + 立替者 + 金額 + 内容で一致）
                        match_mask = (
                            (full_data['日付'] == checked_row['日付']) &
                            (full_data['立替者'] == checked_row['立替者']) &
                            (full_data['金額'] == checked_row['金額']) &
                            (full_data['内容'] == checked_row['内容']) &
                            (full_data['状態'] == '未返済')
                        )
                        matched_indices = full_data[match_mask].index
                        if len(matched_indices) > 0:
                            idx = matched_indices[0]
                            full_data.at[idx, '状態'] = '返済済'
                            full_data.at[idx, '返済日'] = today
                            # 編集された備考を反映
                            full_data.at[idx, '備考'] = checked_row['備考']
                            full_data.at[idx, '決済方法'] = checked_row['決済方法']
                            repaid_count += 1
                            repaid_total += int(checked_row['金額'])

                    st.session_state.reimbursement_data = full_data
                    save_reimbursements(full_data)
                    st.success(f"✅ {repaid_count} 件（¥{repaid_total:,}）を返済済みにしました！")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("⚠️ 返済する項目にチェックを入れてください")

            if reload_clicked:
                st.session_state.reimbursement_data = load_reimbursements()
                st.rerun()
        else:
            # Guest: 閲覧のみ
            st.dataframe(
                display_pending,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "日付": st.column_config.TextColumn("📅 日付", width="small"),
                    "立替者": st.column_config.TextColumn("👤 立替者", width="medium"),
                    "金額": st.column_config.NumberColumn("💴 金額", format="¥%d", width="small"),
                    "内容": st.column_config.TextColumn("📝 内容", width="large"),
                    "決済方法": st.column_config.TextColumn("💳 決済方法", width="small"),
                    "備考": st.column_config.TextColumn("📎 備考", width="medium")
                }
            )
            st.caption("💡 返済処理には管理者権限が必要です")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0; color: #999;">
            <div style="font-size: 3rem;">🎉</div>
            <p style="font-size: 1.1rem; margin-top: 10px;">未返済の立替金はありません！</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ======================
# タブ2: 新規登録
# ======================
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">➕ 立替金の新規登録</p>', unsafe_allow_html=True)

    if not IS_ADMIN:
        st.info("🔒 新規登録には管理者権限が必要です")
    else:
        # メンバー一覧を取得
        members = load_members()
        member_names = members['名前'].tolist() if len(members) > 0 else []

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            reimb_date = st.date_input("📅 立替日", value=datetime.now(), key="reimb_date")

            if len(member_names) > 0:
                reimb_person = st.selectbox("👤 立替者", member_names, key="reimb_person")
            else:
                reimb_person = st.text_input("👤 立替者", placeholder="名前を入力", key="reimb_person_text")

            reimb_amount = st.number_input("💴 金額", min_value=0, value=0, step=100, key="reimb_amount")

        with col_right:
            reimb_content = st.text_input("📝 内容", placeholder="例: 練習試合の審判弁当代", key="reimb_content")
            reimb_method = st.selectbox("💳 返済方法", PAYMENT_METHODS, key="reimb_method")
            reimb_note = st.text_input("📎 備考", placeholder="補足情報があれば（任意）", key="reimb_note")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("✅ 立替金を登録する", type="primary", use_container_width=True, key="submit_reimb"):
            if not reimb_person or not reimb_person.strip():
                st.error("⚠️ 立替者を入力してください")
            elif reimb_amount <= 0:
                st.error("⚠️ 金額を入力してください")
            elif not reimb_content or not reimb_content.strip():
                st.error("⚠️ 内容を入力してください")
            else:
                new_entry = pd.DataFrame({
                    '日付': [reimb_date.strftime('%Y-%m-%d')],
                    '立替者': [reimb_person.strip()],
                    '金額': [reimb_amount],
                    '内容': [reimb_content.strip()],
                    '決済方法': [reimb_method],
                    '状態': ['未返済'],
                    '返済日': [''],
                    '備考': [reimb_note.strip() if reimb_note else '']
                })

                updated = pd.concat([st.session_state.reimbursement_data, new_entry], ignore_index=True)
                st.session_state.reimbursement_data = updated
                save_reimbursements(updated)
                st.success(f"✅ {reimb_person} さんの立替金 ¥{reimb_amount:,}（{reimb_content}）を登録しました！")
                st.balloons()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ======================
# タブ3: 返済済み履歴
# ======================
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">✅ 返済済みの履歴</p>', unsafe_allow_html=True)

    if len(reimb_df) > 0:
        completed_df = reimb_df[reimb_df['状態'] == '返済済'].copy()
    else:
        completed_df = pd.DataFrame(columns=['日付', '立替者', '金額', '内容', '決済方法', '状態', '返済日', '備考'])

    if len(completed_df) > 0:
        display_completed = completed_df[['日付', '立替者', '金額', '内容', '決済方法', '返済日', '備考']].copy()
        display_completed = display_completed.sort_values('返済日', ascending=False).reset_index(drop=True)

        st.dataframe(
            display_completed,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "日付": st.column_config.TextColumn("📅 立替日", width="small"),
                "立替者": st.column_config.TextColumn("👤 立替者", width="medium"),
                "金額": st.column_config.NumberColumn("💴 金額", format="¥%d", width="small"),
                "内容": st.column_config.TextColumn("📝 内容", width="large"),
                "決済方法": st.column_config.TextColumn("💳 決済方法", width="small"),
                "返済日": st.column_config.TextColumn("📅 返済日", width="small"),
                "備考": st.column_config.TextColumn("📎 備考", width="medium")
            }
        )

        # 管理者のみ: 返済済みを未返済に戻す機能
        if IS_ADMIN:
            with st.expander("🔄 返済済みを未返済に戻す"):
                st.warning("⚠️ 間違って返済済みにした場合にのみ使用してください")
                undo_options = []
                for idx, row in completed_df.iterrows():
                    label = f"{row['日付']} | {row['立替者']} | ¥{int(row['金額']):,} | {row['内容']}"
                    undo_options.append((label, idx))

                if len(undo_options) > 0:
                    selected_undo = st.selectbox(
                        "取り消す項目を選択",
                        [opt[0] for opt in undo_options],
                        key="undo_select"
                    )

                    if st.button("↩️ この項目を未返済に戻す", key="undo_repay"):
                        selected_idx = undo_options[[opt[0] for opt in undo_options].index(selected_undo)][1]
                        full_data = st.session_state.reimbursement_data.copy()
                        full_data.at[selected_idx, '状態'] = '未返済'
                        full_data.at[selected_idx, '返済日'] = ''
                        st.session_state.reimbursement_data = full_data
                        save_reimbursements(full_data)
                        st.success("↩️ 未返済に戻しました")
                        st.rerun()
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0; color: #999;">
            <div style="font-size: 3rem;">📭</div>
            <p style="font-size: 1.1rem; margin-top: 10px;">返済済みの履歴はまだありません</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# フッター
st.markdown("""
<div style="text-align: center; padding: 24px 0 12px 0; color: #999; font-size: 0.8rem;">
    返済リスト管理 v1.0 | 部活動 会計管理システム
</div>
""", unsafe_allow_html=True)
