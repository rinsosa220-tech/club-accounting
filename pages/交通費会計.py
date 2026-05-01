import streamlit as st
import pandas as pd
from datetime import datetime
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="交通費会計 | 部活動 会計管理", page_icon="🚗", layout="wide")

# 認証チェック
if "role" not in st.session_state:
    st.warning("⚠️ メインページからログインしてください。")
    st.stop()
if not st.session_state.get("authenticated", False):
    st.warning("⚠️ ログインしてください。")
    st.stop()

CURRENT_ROLE = st.session_state.get("role", "guest")
IS_ADMIN = CURRENT_ROLE == "admin"

from utils.sheets import (
    load_transport_balance, save_transport_balance,
    load_collection, save_collection,
    load_drivers, load_members,
    load_sheet_as_dataframe, save_dataframe_to_sheet
)

# ドライバー返済管理（直接定義 - 互換性のため）
SHEET_DRIVER_PAYMENTS = 'driver_payments'

def load_driver_payments():
    df = load_sheet_as_dataframe(
        SHEET_DRIVER_PAYMENTS,
        ['日付', '遠征名', 'ドライバー', '金額', '状態', '返済日', '備考']
    )
    if len(df) > 0:
        df['日付'] = df['日付'].fillna('').astype(str)
        df['遠征名'] = df['遠征名'].fillna('').astype(str)
        df['ドライバー'] = df['ドライバー'].fillna('').astype(str)
        df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0).astype(int)
        df['状態'] = df['状態'].fillna('未返済').astype(str)
        df['返済日'] = df['返済日'].fillna('').astype(str)
        df['備考'] = df['備考'].fillna('').astype(str)
    return df

def save_driver_payments(df):
    return save_dataframe_to_sheet(df, SHEET_DRIVER_PAYMENTS)

def add_transport_balance_entry(date, item, income, expense, wallet='現金'):
    """交通費会計に1行追加（財布別残高対応）"""
    df = load_transport_balance()
    # 「財布」列がない場合の互換対応
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

# ドライバー10人のフルネームリスト
DRIVER_LIST = [
    "飯尾　郁夢", "新井　稜平", "田中　宏季", "阪井　裕貴", "小泉　諭示",
    "白井　悠也", "吉田　倫太郎", "山本　晃輔", "森　尊慈", "植村　亮"
]

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

    /* KPIグリッド */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }}
    .kpi-card-main {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        border-radius: 14px; padding: 20px 12px; text-align: center;
        box-shadow: 0 6px 16px rgba(103,3,23,0.25);
    }}
    .kpi-card-main .kpi-label {{ color: rgba(255,255,255,0.9); font-size: 0.8rem; margin-bottom: 6px; }}
    .kpi-card-main .kpi-value {{ color: #fff; font-size: 1.8rem; font-weight: 800; white-space: nowrap; }}
    .kpi-card-sub {{
        background: #fff; border-radius: 14px; padding: 18px 10px; text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06); border: 1px solid #eee;
    }}
    .kpi-card-sub .kpi-label {{ font-size: 0.8rem; color: #666; margin-bottom: 6px; }}
    .kpi-card-sub .kpi-value {{ font-size: 1.5rem; font-weight: 800; color: {PRIMARY_COLOR}; white-space: nowrap; }}

    /* スマホ対応 */
    @media (max-width: 768px) {{
        .app-title {{ font-size: 1.5rem !important; }}
        .app-subtitle {{ font-size: 0.8rem !important; }}
        .section-title {{ font-size: 1rem !important; }}
        .card {{ padding: 14px !important; }}
        .kpi-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }}
        .kpi-card-main {{ padding: 14px 8px !important; }}
        .kpi-card-main .kpi-value {{ font-size: 1.4rem !important; }}
        .kpi-card-sub {{ padding: 12px 8px !important; }}
        .kpi-card-sub .kpi-value {{ font-size: 1.15rem !important; }}
        .kpi-card-sub .kpi-label, .kpi-card-main .kpi-label {{ font-size: 0.7rem !important; }}
        .driver-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 6px !important;
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.2rem !important; }}
        [data-testid="stMetricLabel"] {{ font-size: 0.7rem !important; }}
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 8px !important;
        }}
        [data-testid="column"] {{
            min-width: 100% !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 0px !important; }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.7rem !important;
            padding: 6px 6px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown("""
<div class="app-header">
    <p class="app-title">🚗 交通費会計</p>
    <p class="app-subtitle">交通費用財布の収支 • ドライバー返済 • 部員徴収</p>
</div>
""", unsafe_allow_html=True)

col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
with col_m2:
    if IS_ADMIN:
        st.success("👤 管理者モード")
    else:
        st.info("👁️ 閲覧モード")

# データ読み込み（session_stateでキャッシュしてAPI呼び出しを削減）
try:
    if 'tc_balance' not in st.session_state:
        st.session_state.tc_balance = load_transport_balance()
    if 'tc_driver_pay' not in st.session_state:
        st.session_state.tc_driver_pay = load_driver_payments()
    if 'tc_collection' not in st.session_state:
        st.session_state.tc_collection = load_collection()
except Exception as e:
    st.error(f"⚠️ データの読み込みに失敗しました。ページを再読み込みしてください。\n\nエラー: {e}")
    st.stop()

balance_df = st.session_state.tc_balance
driver_pay_df = st.session_state.tc_driver_pay
collection_df = st.session_state.tc_collection

# KPI計算
# 財布別の残高計算
def calc_wallet_balance(df, wallet_name):
    w = df[df['財布'] == wallet_name] if len(df) > 0 and '財布' in df.columns else pd.DataFrame()
    return int(w['残高'].iloc[-1]) if len(w) > 0 else 0

cash_balance = calc_wallet_balance(balance_df, '現金')
paypay_balance = calc_wallet_balance(balance_df, 'PayPay')
total_balance = cash_balance + paypay_balance

total_income = int(balance_df['収入'].sum()) if len(balance_df) > 0 else 0
total_expense = int(balance_df['支出'].sum()) if len(balance_df) > 0 else 0

pending_driver = driver_pay_df[driver_pay_df['状態'] == '未返済'] if len(driver_pay_df) > 0 else pd.DataFrame()
driver_owed = int(pending_driver['金額'].sum()) if len(pending_driver) > 0 else 0

event_cols = [c for c in collection_df.columns if c != '名前'] if len(collection_df) > 0 else []
member_owed = 0
if len(collection_df) > 0 and len(event_cols) > 0:
    for c in event_cols:
        collection_df[c] = pd.to_numeric(collection_df[c], errors='coerce').fillna(0)
    member_owed = int(collection_df[event_cols].sum().sum())

# KPI表示（CSSグリッドで重なり防止）
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card-main">
        <div class="kpi-label">💰 合計残高</div>
        <div class="kpi-value">¥{total_balance:,}</div>
    </div>
    <div class="kpi-card-sub">
        <div class="kpi-label">💵 現金</div>
        <div class="kpi-value">¥{cash_balance:,}</div>
    </div>
    <div class="kpi-card-sub">
        <div class="kpi-label">📱 PayPay</div>
        <div class="kpi-value">¥{paypay_balance:,}</div>
    </div>
    <div class="kpi-card-sub">
        <div class="kpi-label">🚗 ドライバー未返済</div>
        <div class="kpi-value">¥{driver_owed:,}</div>
    </div>
    <div class="kpi-card-sub">
        <div class="kpi-label">👥 部員未徴収</div>
        <div class="kpi-value">¥{member_owed:,}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# タブ構成
# ============================================================
tab1, tab2, tab3 = st.tabs(["💰 収支台帳", "🚗 ドライバー返済", "👥 部員徴収"])

# ============================================================
# タブ1: 収支台帳
# ============================================================
with tab1:
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">📒 交通費 収支台帳</p>', unsafe_allow_html=True)

        if len(balance_df) > 0:
            # フィルタ
            filter_wallet = st.radio("表示する財布", ["すべて", "💵 現金", "📱 PayPay"], horizontal=True, key="filter_wallet")
            disp_bal = balance_df.copy()
            if filter_wallet == "💵 現金":
                disp_bal = disp_bal[disp_bal['財布'] == '現金']
            elif filter_wallet == "📱 PayPay":
                disp_bal = disp_bal[disp_bal['財布'] == 'PayPay']
            disp_bal = disp_bal.reset_index(drop=True)

            disp_bal['収入'] = disp_bal['収入'].astype(int)
            disp_bal['支出'] = disp_bal['支出'].astype(int)
            disp_bal['残高'] = disp_bal['残高'].astype(int)

            wallet_options = ['現金', 'PayPay']

            if IS_ADMIN:
                edited_bal = st.data_editor(
                    disp_bal, use_container_width=True, hide_index=True, height=420,
                    column_config={
                        "日付": st.column_config.TextColumn("📅 日付", width="small"),
                        "項目": st.column_config.TextColumn("📝 項目", width="large"),
                        "財布": st.column_config.SelectboxColumn("💳 財布", options=wallet_options, width="small"),
                        "収入": st.column_config.NumberColumn("📈 収入", format="¥%d", width="small"),
                        "支出": st.column_config.NumberColumn("📉 支出", format="¥%d", width="small"),
                        "残高": st.column_config.NumberColumn("💰 残高", format="¥%d", width="small", disabled=True),
                    },
                    key="bal_editor"
                )
                bc1, bc2, _ = st.columns([1, 1, 4])
                with bc1:
                    if st.button("💾 台帳を保存", type="primary", use_container_width=True, key="save_bal"):
                        # 保存前に財布ごとの残高を再計算
                        save_df = edited_bal.copy()
                        save_df['収入'] = pd.to_numeric(save_df['収入'], errors='coerce').fillna(0).astype(int)
                        save_df['支出'] = pd.to_numeric(save_df['支出'], errors='coerce').fillna(0).astype(int)
                        if '財布' not in save_df.columns:
                            save_df['財布'] = '現金'
                        save_df['財布'] = save_df['財布'].fillna('現金').replace('', '現金')
                        # 財布ごとに残高を積み上げ計算
                        save_df['残高'] = 0
                        for wallet_name in save_df['財布'].unique():
                            mask = save_df['財布'] == wallet_name
                            net = (save_df.loc[mask, '収入'] - save_df.loc[mask, '支出']).cumsum()
                            save_df.loc[mask, '残高'] = net
                        save_transport_balance(save_df)
                        del st.session_state['tc_balance']
                        st.success("✅ 残高を再計算して保存しました")
                        st.rerun()
                with bc2:
                    if st.button("↩️ 元に戻す", use_container_width=True, key="reload_bal"):
                        del st.session_state['tc_balance']
                        st.rerun()
            else:
                st.dataframe(disp_bal, use_container_width=True, hide_index=True, height=420,
                    column_config={
                        "財布": st.column_config.TextColumn("💳 財布"),
                        "収入": st.column_config.NumberColumn("📈 収入", format="¥%d"),
                        "支出": st.column_config.NumberColumn("📉 支出", format="¥%d"),
                        "残高": st.column_config.NumberColumn("💰 残高", format="¥%d"),
                    })
        else:
            st.info("📭 取引履歴がありません")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # 記帳フォーム
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">➕ 新規記帳</p>', unsafe_allow_html=True)

        if IS_ADMIN:
            entry_date = st.date_input("📅 日付", datetime.now(), key="bal_date")
            entry_wallet = st.selectbox("💳 財布", ["現金", "PayPay"], key="bal_wallet")
            entry_item = st.text_input("📝 項目", placeholder="例: 10月遠征 徴収完了", key="bal_item")
            entry_type = st.radio("種別", ["収入", "支出"], horizontal=True, key="bal_type")
            entry_amount = st.number_input("💴 金額", min_value=0, value=0, step=100, key="bal_amount")

            if st.button("✅ 記帳する", type="primary", use_container_width=True, key="add_bal"):
                if entry_amount > 0 and entry_item:
                    inc = entry_amount if entry_type == "収入" else 0
                    exp = entry_amount if entry_type == "支出" else 0
                    add_transport_balance_entry(entry_date.strftime('%Y-%m-%d'), entry_item, inc, exp, entry_wallet)
                    del st.session_state['tc_balance']
                    st.success(f"✅ {entry_wallet} に ¥{entry_amount:,} を記帳しました")
                    st.rerun()
                else:
                    st.warning("⚠️ 項目と金額を入力してください")
        else:
            st.info("🔒 記帳には管理者権限が必要です")

        st.markdown('</div>', unsafe_allow_html=True)

        # 資金移動フォーム
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🔄 資金移動（現金 ⇔ PayPay）</p>', unsafe_allow_html=True)

        if IS_ADMIN:
            mv_date = st.date_input("📅 日付", datetime.now(), key="mv_date")
            mv_direction = st.radio("移動方向", ["現金 → PayPay", "PayPay → 現金"], horizontal=True, key="mv_dir")
            mv_amount = st.number_input("💴 移動金額", min_value=0, value=0, step=100, key="mv_amount")
            mv_note = st.text_input("📎 備考", placeholder="任意", key="mv_note")

            if st.button("🔄 資金を移動する", type="primary", use_container_width=True, key="do_mv"):
                if mv_amount > 0:
                    date_str = mv_date.strftime('%Y-%m-%d')
                    note_text = f" ({mv_note})" if mv_note else ""
                    if mv_direction == "現金 → PayPay":
                        src, dst = "現金", "PayPay"
                    else:
                        src, dst = "PayPay", "現金"

                    item_src = f"資金移動 → {dst}{note_text}"
                    item_dst = f"資金移動 ← {src}{note_text}"

                    # 移動元から支出
                    add_transport_balance_entry(date_str, item_src, 0, mv_amount, src)
                    # 移動先に収入
                    add_transport_balance_entry(date_str, item_dst, mv_amount, 0, dst)
                    del st.session_state['tc_balance']
                    st.success(f"✅ {src} → {dst} に ¥{mv_amount:,} を移動しました")
                    st.rerun()
                else:
                    st.warning("⚠️ 金額を入力してください")
        else:
            st.info("🔒 管理者権限が必要です")

        st.markdown('</div>', unsafe_allow_html=True)

        # サマリー
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">📊 財布別サマリー</p>', unsafe_allow_html=True)
        st.metric("💵 現金 残高", f"¥{cash_balance:,}")
        st.metric("📱 PayPay 残高", f"¥{paypay_balance:,}")
        st.divider()
        st.metric("💰 合計残高", f"¥{total_balance:,}")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# タブ2: ドライバー返済
# ============================================================
with tab2:
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🚗 ドライバーへの未返済リスト</p>', unsafe_allow_html=True)

        if len(driver_pay_df) > 0:
            pending_dp = driver_pay_df[driver_pay_df['状態'] == '未返済'].copy()
        else:
            pending_dp = pd.DataFrame(columns=['日付', '遠征名', 'ドライバー', '金額', '状態', '返済日', '備考'])

        # 全ドライバー一覧ダッシュボード（未返済がなくても¥0で表示）
        driver_names = DRIVER_LIST

        if len(driver_names) > 0:
            # ドライバーごとの未返済額を集計
            if len(pending_dp) > 0:
                drv_agg = pending_dp.groupby('ドライバー')['金額'].agg(['sum', 'count']).reset_index()
                drv_agg.columns = ['ドライバー', '未返済合計', '件数']
            else:
                drv_agg = pd.DataFrame(columns=['ドライバー', '未返済合計', '件数'])

            # 全ドライバーのDataFrameを作成（未登録は¥0）
            all_drv_df = pd.DataFrame({'ドライバー': driver_names})
            all_drv_df = all_drv_df.merge(drv_agg, on='ドライバー', how='left')
            all_drv_df['未返済合計'] = all_drv_df['未返済合計'].fillna(0).astype(int)
            all_drv_df['件数'] = all_drv_df['件数'].fillna(0).astype(int)
            all_drv_df = all_drv_df.sort_values('未返済合計', ascending=False).reset_index(drop=True)

            st.markdown('<p class="section-title">👥 ドライバー別 未返済額</p>', unsafe_allow_html=True)

            # CSSグリッドで全ドライバーを表示（スマホでは2列に折り返し）
            cards_html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px;" class="driver-grid">'
            for _, r in all_drv_df.iterrows():
                amt = int(r['未返済合計'])
                cnt = int(r['件数'])
                short_name = r['ドライバー'].split('　')[0] if '　' in r['ドライバー'] else r['ドライバー']
                if amt > 0:
                    cards_html += f"""
                    <div style="background:linear-gradient(135deg,{PRIMARY_COLOR} 0%,{PRIMARY_LIGHT} 100%);
                        border-radius:12px;padding:12px 5px;text-align:center;
                        box-shadow:0 4px 12px rgba(103,3,23,0.2);">
                        <div style="color:rgba(255,255,255,0.85);font-size:0.75rem;">🚗 {short_name}</div>
                        <div style="color:#fff;font-size:1.1rem;font-weight:800;white-space:nowrap;">¥{amt:,}</div>
                        <div style="color:rgba(255,255,255,0.7);font-size:0.7rem;">{cnt}件</div>
                    </div>"""
                else:
                    cards_html += f"""
                    <div style="background:#f8f9fa;border-radius:12px;padding:12px 5px;
                        text-align:center;border:1px solid #e9ecef;">
                        <div style="color:#999;font-size:0.75rem;">🚗 {short_name}</div>
                        <div style="color:#28a745;font-size:1.1rem;font-weight:800;white-space:nowrap;">¥0</div>
                        <div style="color:#999;font-size:0.7rem;">返済なし</div>
                    </div>"""
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            st.divider()

        if len(pending_dp) > 0:
            disp_dp = pending_dp[['日付', '遠征名', 'ドライバー', '金額', '備考']].sort_values('日付', ascending=False).reset_index(drop=True)

            if IS_ADMIN:
                disp_dp.insert(0, "返済✓", False)
                edited_dp = st.data_editor(disp_dp, use_container_width=True, hide_index=True, height=350,
                    column_config={
                        "返済✓": st.column_config.CheckboxColumn("返済✓", default=False, width="small"),
                        "日付": st.column_config.TextColumn("📅 日付", width="small"),
                        "遠征名": st.column_config.TextColumn("📝 遠征名", width="medium"),
                        "ドライバー": st.column_config.TextColumn("🚗 ドライバー", width="medium"),
                        "金額": st.column_config.NumberColumn("💴 金額", format="¥%d", width="small"),
                        "備考": st.column_config.TextColumn("📎 備考", width="medium"),
                    }, key="dp_editor")

                dp1, dp2, _ = st.columns([1.5, 1, 3.5])
                with dp1:
                    if st.button("✅ チェック分を返済済みにする", type="primary", use_container_width=True, key="repay_drv"):
                        checked = edited_dp[edited_dp["返済✓"] == True]
                        if len(checked) > 0:
                            today = datetime.now().strftime('%Y-%m-%d')
                            full = st.session_state.tc_driver_pay.copy()
                            cnt = 0
                            for _, cr in checked.iterrows():
                                m = (full['日付'] == cr['日付']) & (full['ドライバー'] == cr['ドライバー']) & (full['金額'] == cr['金額']) & (full['遠征名'] == cr['遠征名']) & (full['状態'] == '未返済')
                                idx = full[m].index
                                if len(idx) > 0:
                                    full.at[idx[0], '状態'] = '返済済'
                                    full.at[idx[0], '返済日'] = today
                                    cnt += 1
                            save_driver_payments(full)
                            del st.session_state['tc_driver_pay']
                            st.success(f"✅ {cnt}件を返済済みにしました")
                            st.rerun()
                        else:
                            st.warning("⚠️ チェックを入れてください")
                with dp2:
                    if st.button("↩️ 元に戻す", use_container_width=True, key="reload_dp"):
                        del st.session_state['tc_driver_pay']
                        st.rerun()
            else:
                st.dataframe(disp_dp, use_container_width=True, hide_index=True, height=350,
                    column_config={"金額": st.column_config.NumberColumn("💴 金額", format="¥%d")})
        else:
            if len(driver_names) == 0:
                st.markdown('<div style="text-align:center;padding:40px 0;color:#999;"><div style="font-size:3rem;">🎉</div><p>未返済のドライバー立替はありません</p></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">➕ ドライバー返済を登録</p>', unsafe_allow_html=True)

        if IS_ADMIN:
            dp_date = st.date_input("📅 日付", datetime.now(), key="dp_date")
            dp_event = st.text_input("📝 遠征名", placeholder="例: 10月練習試合", key="dp_event")
            dp_driver = st.selectbox("🚗 ドライバー", DRIVER_LIST, key="dp_driver")
            dp_amount = st.number_input("💴 金額", min_value=0, value=0, step=100, key="dp_amount")
            dp_note = st.text_input("📎 備考", placeholder="任意", key="dp_note")

            if st.button("✅ 登録する", type="primary", use_container_width=True, key="add_dp"):
                if dp_driver and dp_amount > 0 and dp_event:
                    new = pd.DataFrame({
                        '日付': [dp_date.strftime('%Y-%m-%d')], '遠征名': [dp_event],
                        'ドライバー': [dp_driver], '金額': [dp_amount],
                        '状態': ['未返済'], '返済日': [''], '備考': [dp_note or '']
                    })
                    updated = pd.concat([st.session_state.tc_driver_pay, new], ignore_index=True)
                    save_driver_payments(updated)
                    del st.session_state['tc_driver_pay']
                    st.success(f"✅ {dp_driver} さんへの ¥{dp_amount:,} を登録しました")
                    st.rerun()
                else:
                    st.warning("⚠️ 遠征名・ドライバー・金額を入力してください")
        else:
            st.info("🔒 管理者権限が必要です")
        st.markdown('</div>', unsafe_allow_html=True)

        # 返済済み履歴
        if len(driver_pay_df) > 0:
            completed_dp = driver_pay_df[driver_pay_df['状態'] == '返済済']
            if len(completed_dp) > 0:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">✅ 返済済み履歴</p>', unsafe_allow_html=True)
                st.dataframe(
                    completed_dp[['日付', '遠征名', 'ドライバー', '金額', '返済日']].sort_values('返済日', ascending=False).reset_index(drop=True),
                    use_container_width=True, hide_index=True, height=250,
                    column_config={"金額": st.column_config.NumberColumn("💴", format="¥%d")}
                )
                st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# タブ3: 部員徴収
# ============================================================
with tab3:
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">👥 部員からの徴収状況</p>', unsafe_allow_html=True)

        coll_df = st.session_state.tc_collection.copy()

        if len(coll_df) > 0 and len(coll_df.columns) > 1:
            coll_df['名前'] = coll_df['名前'].fillna('').astype(str)
            ev_cols = [c for c in coll_df.columns if c != '名前']

            if len(ev_cols) > 0:
                for c in ev_cols:
                    coll_df[c] = pd.to_numeric(coll_df[c], errors='coerce').fillna(0).astype(int)

                coll_df['未払計'] = coll_df[ev_cols].sum(axis=1)
                total_unpaid = coll_df['未払計'].sum()
                unpaid_count = len(coll_df[coll_df['未払計'] > 0])
                total_count = len(coll_df)
                paid_rate = (total_count - unpaid_count) / total_count if total_count > 0 else 0

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("💴 未回収総額", f"¥{total_unpaid:,}")
                with mc2:
                    st.metric("👥 未払者", f"{unpaid_count} / {total_count} 名")
                with mc3:
                    st.metric("📈 回収完了率", f"{paid_rate*100:.0f}%")
                st.divider()

                max_due = coll_df['未払計'].max() if coll_df['未払計'].max() > 0 else 1
                coll_df['回収率'] = 1.0 - (coll_df['未払計'] / max_due)

                disp_cols = ['名前'] + ev_cols + ['未払計', '回収率']
                disp_coll = coll_df[disp_cols].copy()

                col_cfg = {
                    "名前": st.column_config.TextColumn("👤 名前", disabled=True, width="medium"),
                    "未払計": st.column_config.NumberColumn("📊 未払計", format="¥%d", disabled=True, width="small"),
                    "回収率": st.column_config.ProgressColumn("✅ 回収率", min_value=0, max_value=1, width="small"),
                }
                for c in ev_cols:
                    col_cfg[c] = st.column_config.NumberColumn(c, format="¥%d", step=100, width="small")

                if IS_ADMIN:
                    edited_coll = st.data_editor(disp_coll, use_container_width=True, hide_index=True,
                        height=420, column_config=col_cfg, key="coll_editor_tc")

                    cc1, cc2, _ = st.columns([1, 1, 4])
                    with cc1:
                        if st.button("💾 徴収状況を保存", type="primary", use_container_width=True, key="save_coll_tc"):
                            save_data = st.session_state.tc_collection.copy()
                            for c in ev_cols:
                                if c in edited_coll.columns:
                                    save_data[c] = edited_coll[c]
                            save_collection(save_data)
                            del st.session_state['tc_collection']
                            st.success("✅ 保存しました")
                            st.rerun()
                    with cc2:
                        if st.button("↩️ 元に戻す", use_container_width=True, key="reload_coll_tc"):
                            del st.session_state['tc_collection']
                            st.rerun()
                else:
                    st.dataframe(disp_coll, use_container_width=True, hide_index=True, height=420, column_config=col_cfg)
            else:
                st.info("📭 徴収イベントがまだありません")
        else:
            st.info("📭 徴収データがありません")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # 徴収完了処理
        ev_cols_r = [c for c in st.session_state.tc_collection.columns if c != '名前']
        if len(ev_cols_r) > 0 and IS_ADMIN:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">✅ 徴収完了処理</p>', unsafe_allow_html=True)

            sel_event = st.selectbox("イベント選択", ev_cols_r, key="complete_event_tc")
            st.caption("全員から徴収が完了したら、ここで収入として計上します")

            if st.button("💰 全員徴収完了として記録", type="primary", use_container_width=True, key="complete_tc"):
                c_data = st.session_state.tc_collection.copy()
                collected = int(pd.to_numeric(c_data[sel_event], errors='coerce').fillna(0).sum())
                c_data[sel_event] = 0
                save_collection(c_data)
                add_transport_balance_entry(datetime.now().strftime('%Y-%m-%d'), f"{sel_event} 徴収完了", collected, 0)
                # キャッシュクリア
                for k in ['tc_balance', 'tc_collection']:
                    if k in st.session_state:
                        del st.session_state[k]
                st.success(f"✅ ¥{collected:,} を収入として計上しました")
                st.balloons()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 部員別の未払い詳細
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">⚠️ 未払い者リスト</p>', unsafe_allow_html=True)
        coll_check = st.session_state.tc_collection.copy()
        if len(coll_check) > 0:
            ev_c = [c for c in coll_check.columns if c != '名前']
            if len(ev_c) > 0:
                for c in ev_c:
                    coll_check[c] = pd.to_numeric(coll_check[c], errors='coerce').fillna(0)
                coll_check['未払計'] = coll_check[ev_c].sum(axis=1)
                unpaid_members = coll_check[coll_check['未払計'] > 0][['名前', '未払計']].sort_values('未払計', ascending=False)
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
                st.info("徴収イベントがありません")
        else:
            st.info("データがありません")
        st.markdown('</div>', unsafe_allow_html=True)

# フッター
st.markdown(f"""
<div style="text-align:center;padding:24px 0 12px 0;color:#999;font-size:0.8rem;">
    交通費会計 v1.0 | 部活動 会計管理システム
</div>
""", unsafe_allow_html=True)
