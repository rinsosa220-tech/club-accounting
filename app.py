import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Google Sheets連携ユーティリティ
from utils.sheets import load_database, save_database

# ページ設定
st.set_page_config(
    page_title="部活動 会計管理",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# 🔐 権限管理付き認証機能
# ======================
def check_password():
    """Admin/Guest権限を確認する"""
    
    # secrets.tomlにパスワードが設定されているか確認
    if "admin_password" not in st.secrets or "guest_password" not in st.secrets:
        # パスワード未設定の場合はAdmin権限で通す（ローカル開発用）
        st.session_state.role = "admin"
        st.session_state.authenticated = True
        return True
    
    # セッション状態でログイン状態を管理
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "role" not in st.session_state:
        st.session_state.role = None
    
    if st.session_state.authenticated and st.session_state.role:
        return True
    
    # ログイン画面を表示
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1 style="color: #670317;">🔐 部活動 会計管理システム</h1>
        <p style="color: #666;">部員専用ページです。パスワードを入力してください。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔑 パスワード", type="password", key="password_input")
        
        if st.button("ログイン", use_container_width=True, type="primary"):
            if password == st.secrets["admin_password"]:
                st.session_state.authenticated = True
                st.session_state.role = "admin"
                st.success("✅ 管理者としてログインしました")
                st.rerun()
            elif password == st.secrets["guest_password"]:
                st.session_state.authenticated = True
                st.session_state.role = "guest"
                st.success("✅ 閲覧者としてログインしました")
                st.rerun()
            else:
                st.error("⚠️ パスワードが違います")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #888; font-size: 0.85rem;">
            <p>👤 管理者: データの編集・追加が可能</p>
            <p>👁️ 一般部員: 閲覧のみ</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()
    return False

# パスワードチェック
check_password()

# 現在の権限を取得（デフォルトはguest）
CURRENT_ROLE = st.session_state.get("role", "guest")
IS_ADMIN = CURRENT_ROLE == "admin"

# 科目リスト定義（種別ごと）
EXPENSE_CATEGORIES = [
    "大会費", "OB通信費", "備品", "雑費", 
    "グラウンド代（練習試合）", "グラウンド代（試合）",
    "審判登録費", "JFA登録費", "次年度繰越金", "その他"
]

INCOME_CATEGORIES = [
    "前年度繰越金", "OB会費", "寄付金", "部費",
    "利息", "その他", "クラウドファンディング"
]

ALL_CATEGORIES = list(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES))

# 決済方法
PAYMENT_METHODS = ["現金 (財布)", "銀行口座"]

# 種別（資金移動を追加）
TRANSACTION_TYPES = ["収入", "支出", "資金移動"]

# えんじ色ベースのカラーパレット
PRIMARY_COLOR = "#670317"
SECONDARY_COLOR = "#8B1538"
ACCENT_COLOR = "#A52A4A"
INCOME_COLOR = "#2E7D32"
EXPENSE_COLOR = "#670317"
WALLET_COLOR = "#E65100"
BANK_COLOR = "#1565C0"

# カスタムCSS
st.markdown(f"""
<style>
    .section-title {{
        font-size: 1.4rem;
        font-weight: 600;
        color: {PRIMARY_COLOR};
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid {PRIMARY_COLOR};
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    .app-header {{
        text-align: center;
        padding: 20px 0 30px 0;
    }}
    
    .app-title {{
        font-size: 2.8rem;
        font-weight: 800;
        color: {PRIMARY_COLOR};
        margin-bottom: 5px;
    }}
    
    .app-subtitle {{
        color: #666;
        font-size: 1.1rem;
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricDelta"] {{
        font-size: 0.95rem !important;
    }}
    
    [data-testid="stDataFrame"] {{
        border-radius: 10px;
        overflow: hidden;
    }}
</style>
""", unsafe_allow_html=True)

# session_stateにデータを保持（Google Sheetsから読み込み）
if 'data' not in st.session_state:
    st.session_state.data = load_database()

# ======================
# サイドバー: 権限に応じて表示切替
# ======================
with st.sidebar:
    st.markdown("## 💰 会計管理")
    
    # 現在のログイン状態を表示
    if IS_ADMIN:
        st.success("👤 管理者モード")
    else:
        st.info("👁️ 閲覧モード")
    
    st.markdown("---")
    
    # 管理者のみ入力フォームを表示
    if IS_ADMIN:
        # 入力フォーム
        st.markdown("### 📝 新規取引登録")
        
        # 種別選択
        transaction_type = st.selectbox("📊 種別", TRANSACTION_TYPES, key="tx_type")
        
        # 決済方法選択（資金移動の場合は移動元/移動先）
        if transaction_type == "資金移動":
            st.markdown("##### 🔄 資金移動設定")
            transfer_from = st.selectbox("📤 移動元", PAYMENT_METHODS, key="transfer_from")
            transfer_to_options = [m for m in PAYMENT_METHODS if m != transfer_from]
            transfer_to = st.selectbox("📥 移動先", transfer_to_options, key="transfer_to")
            category = "資金移動"
        else:
            payment_method = st.selectbox("💳 決済方法", PAYMENT_METHODS, key="payment_method")
            
            if transaction_type == "支出":
                category = st.selectbox("📁 科目", EXPENSE_CATEGORIES, key="category")
            else:
                category = st.selectbox("📁 科目", INCOME_CATEGORIES, key="category")
        
        with st.form("entry_form", clear_on_submit=True):
            date = st.date_input("📅 日付", value=datetime.now())
            amount = st.number_input("💴 金額", min_value=0, value=0, step=100)
            note = st.text_input("📝 備考", placeholder="メモを入力...")
            
            submitted = st.form_submit_button("✅ 登録する", use_container_width=True)
            
            if submitted:
                if amount > 0:
                    if transaction_type == "資金移動":
                        entry_out = pd.DataFrame({
                            '日付': [pd.Timestamp(date)],
                            '種別': ['支出'],
                            '科目': [f'資金移動 → {transfer_to}'],
                            '金額': [amount],
                            '備考': [note if note else f'{transfer_from}から{transfer_to}へ移動'],
                            '決済方法': [transfer_from]
                        })
                        entry_in = pd.DataFrame({
                            '日付': [pd.Timestamp(date)],
                            '種別': ['収入'],
                            '科目': [f'資金移動 ← {transfer_from}'],
                            '金額': [amount],
                            '備考': [note if note else f'{transfer_from}から{transfer_to}へ移動'],
                            '決済方法': [transfer_to]
                        })
                        st.session_state.data = pd.concat([st.session_state.data, entry_out, entry_in], ignore_index=True)
                    else:
                        new_entry = pd.DataFrame({
                            '日付': [pd.Timestamp(date)],
                            '種別': [transaction_type],
                            '科目': [category],
                            '金額': [amount],
                            '備考': [note],
                            '決済方法': [payment_method]
                        })
                        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
                    
                    # Google Sheetsに保存
                    save_database(st.session_state.data)
                    st.success("✨ 登録完了！")
                    st.rerun()
                else:
                    st.error("⚠️ 金額を入力してください")
    else:
        # Guestの場合は閲覧専用メッセージ
        st.markdown("""
        <div style="background: #fff3cd; border-radius: 10px; padding: 15px; margin: 10px 0;">
            <p style="margin: 0; color: #856404; font-weight: 600;">🔒 閲覧モード</p>
            <p style="margin: 5px 0 0 0; color: #856404; font-size: 0.9rem;">
                データの追加・編集には管理者権限が必要です。
            </p>
        </div>
        """, unsafe_allow_html=True)

# ======================
# メインエリア
# ======================

# ヘッダー
st.markdown("""
<div class="app-header">
    <p class="app-title">💰 部活動 会計管理</p>
    <p class="app-subtitle">財布と銀行口座を分けて、部活動の財務を効率的に管理</p>
</div>
""", unsafe_allow_html=True)

# 全期間のデータを使用
df = st.session_state.data.copy()
if len(df) > 0:
    df['日付'] = pd.to_datetime(df['日付'])
    if '決済方法' not in df.columns:
        df['決済方法'] = '現金 (財布)'

# ======================
# KPIセクション（財布・口座・総資産の3分割表示）
# ======================
st.markdown('<p class="section-title">📊 資産状況（全期間累計）</p>', unsafe_allow_html=True)

if len(df) > 0:
    # 財布（現金）の計算
    wallet_df = df[df['決済方法'] == '現金 (財布)']
    wallet_income = wallet_df[wallet_df['種別'] == '収入']['金額'].sum()
    wallet_expense = wallet_df[wallet_df['種別'] == '支出']['金額'].sum()
    wallet_balance = wallet_income - wallet_expense
    
    # 銀行口座の計算
    bank_df = df[df['決済方法'] == '銀行口座']
    bank_income = bank_df[bank_df['種別'] == '収入']['金額'].sum()
    bank_expense = bank_df[bank_df['種別'] == '支出']['金額'].sum()
    bank_balance = bank_income - bank_expense
    
    # 総資産
    total_balance = wallet_balance + bank_balance
    
    # 全期間の収入・支出
    total_income = df[df['種別'] == '収入']['金額'].sum()
    total_expense = df[df['種別'] == '支出']['金額'].sum()
else:
    wallet_balance = 0
    bank_balance = 0
    total_balance = 0
    total_income = 0
    total_expense = 0

# KPIカード表示（3列）
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(
        label="💰 財布 (現金)",
        value=f"¥{wallet_balance:,.0f}"
    )

with kpi2:
    st.metric(
        label="🏦 銀行口座",
        value=f"¥{bank_balance:,.0f}"
    )

with kpi3:
    st.metric(
        label="📊 総資産合計",
        value=f"¥{total_balance:,.0f}"
    )

st.markdown("<br>", unsafe_allow_html=True)

# 全期間の収入・支出サマリ
st.markdown('<p class="section-title">📈 収支サマリ（全期間）</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📈 総収入", f"¥{total_income:,.0f}")
with col2:
    st.metric("📉 総支出", f"¥{total_expense:,.0f}")
with col3:
    net = total_income - total_expense
    st.metric("💹 収支差額", f"¥{net:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ======================
# グラフセクション（全期間データ）
# ======================
st.markdown('<p class="section-title">📈 分析（全期間）</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🥧 支出の内訳", "📊 月別収支推移", "💳 決済方法別"])

with tab1:
    expense_data = df[df['種別'] == '支出'] if len(df) > 0 else pd.DataFrame()
    
    if len(expense_data) > 0:
        expense_by_category = expense_data.groupby('科目')['金額'].sum().reset_index()
        
        enji_palette = [
            '#670317', '#8B1538', '#A52A4A', '#C04060', 
            '#D85A7A', '#E87A9A', '#F5A0B8', '#FFD0DD',
            '#4A0210', '#7D1A3D'
        ]
        
        fig = px.pie(
            expense_by_category,
            values='金額',
            names='科目',
            color_discrete_sequence=enji_palette,
            hole=0.45
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#262730', size=14),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(t=30, b=30, l=30, r=30),
            height=400
        )
        fig.update_traces(
            textinfo='percent+value',
            texttemplate='%{percent}<br>¥%{value:,.0f}',
            textfont_size=13,
            hovertemplate='<b>%{label}</b><br>金額: ¥%{value:,.0f}<br>割合: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 支出データがありません")

with tab2:
    if len(df) > 0:
        df['年月'] = df['日付'].dt.to_period('M').astype(str)
        monthly_data = df.groupby(['年月', '種別'])['金額'].sum().unstack(fill_value=0).reset_index()
        
        if '収入' not in monthly_data.columns:
            monthly_data['収入'] = 0
        if '支出' not in monthly_data.columns:
            monthly_data['支出'] = 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='収入',
            x=monthly_data['年月'],
            y=monthly_data['収入'],
            marker_color='#2E7D32',
            hovertemplate='<b>%{x}</b><br>収入: ¥%{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='支出',
            x=monthly_data['年月'],
            y=monthly_data['支出'],
            marker_color='#670317',
            hovertemplate='<b>%{x}</b><br>支出: ¥%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#262730', size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=50, b=50, l=50, r=30),
            height=400,
            xaxis=dict(showgrid=False, title="月"),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', title="金額 (円)")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 データがありません")

with tab3:
    if len(df) > 0:
        method_data = df.groupby(['決済方法', '種別'])['金額'].sum().unstack(fill_value=0).reset_index()
        
        if '収入' not in method_data.columns:
            method_data['収入'] = 0
        if '支出' not in method_data.columns:
            method_data['支出'] = 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='収入',
            x=method_data['決済方法'],
            y=method_data['収入'],
            marker_color='#2E7D32',
            hovertemplate='<b>%{x}</b><br>収入: ¥%{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='支出',
            x=method_data['決済方法'],
            y=method_data['支出'],
            marker_color='#670317',
            hovertemplate='<b>%{x}</b><br>支出: ¥%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#262730', size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=50, b=50, l=50, r=30),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 データがありません")

st.markdown("<br>", unsafe_allow_html=True)

# ======================
# 取引履歴セクション（権限に応じて表示切替）
# ======================
if IS_ADMIN:
    st.markdown('<p class="section-title">📋 取引履歴（全期間・編集可能）</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="section-title">📋 取引履歴（全期間・閲覧専用）</p>', unsafe_allow_html=True)

if len(df) > 0:
    display_df = df.copy()
    display_df['日付'] = pd.to_datetime(display_df['日付']).dt.strftime('%Y-%m-%d')
    display_df['備考'] = display_df['備考'].fillna("").astype(str)
    if '決済方法' not in display_df.columns:
        display_df['決済方法'] = '現金 (財布)'
    display_df = display_df.sort_values('日付', ascending=False).reset_index(drop=True)
    
    if IS_ADMIN:
        # 管理者: 編集・削除可能
        # 削除用カラムを一番左に追加
        display_df.insert(0, "削除", False)
        
        # カラム順序を調整
        column_order = ['削除', '日付', '種別', '科目', '金額', '決済方法', '備考']
        display_df = display_df[[c for c in column_order if c in display_df.columns]]
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "削除": st.column_config.CheckboxColumn(
                    "🗑️",
                    help="チェックすると削除されます",
                    default=False,
                    width="small"
                ),
                "日付": st.column_config.TextColumn("📅 日付", width="small"),
                "種別": st.column_config.SelectboxColumn(
                    "📊 種別",
                    options=["収入", "支出"],
                    width="small"
                ),
                "科目": st.column_config.SelectboxColumn(
                    "📁 科目",
                    options=ALL_CATEGORIES + ["資金移動 → 銀行口座", "資金移動 → 現金 (財布)", "資金移動 ← 銀行口座", "資金移動 ← 現金 (財布)"],
                    width="medium"
                ),
                "金額": st.column_config.NumberColumn(
                    "💴 金額",
                    min_value=0,
                    format="¥%d",
                    width="small"
                ),
                "決済方法": st.column_config.SelectboxColumn(
                    "💳 決済方法",
                    options=PAYMENT_METHODS,
                    width="small"
                ),
                "備考": st.column_config.TextColumn("📝 備考", width="medium")
            },
            key="data_editor"
        )
        
        # 削除チェックがついている行を除外して保存用データを作成
        to_save_df = edited_df[edited_df["削除"] == False].drop(columns=["削除"]).copy()
        
        # 元データ（削除カラムなし）と比較
        original_df = display_df.drop(columns=["削除"]).copy()
        
        # 変更検知して保存
        if not original_df.equals(to_save_df):
            try:
                save_df = to_save_df.copy()
                save_df['日付'] = pd.to_datetime(save_df['日付'])
                save_df = save_df.sort_values('日付', ascending=False).reset_index(drop=True)
                st.session_state.data = save_df
                save_database(save_df)
                st.success("✅ 変更を保存しました")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ 保存中にエラーが発生しました: {e}")
    else:
        # Guest: 閲覧専用（dataframeで表示）
        column_order = ['日付', '種別', '科目', '金額', '決済方法', '備考']
        display_df = display_df[[c for c in column_order if c in display_df.columns]]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "日付": st.column_config.TextColumn("📅 日付", width="small"),
                "種別": st.column_config.TextColumn("📊 種別", width="small"),
                "科目": st.column_config.TextColumn("📁 科目", width="medium"),
                "金額": st.column_config.NumberColumn("💴 金額", format="¥%d", width="small"),
                "決済方法": st.column_config.TextColumn("💳 決済方法", width="small"),
                "備考": st.column_config.TextColumn("📝 備考", width="medium")
            }
        )
        st.caption("💡 データの編集には管理者権限が必要です")
else:
    st.info("📭 取引データがありません")

# フッター
st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0; color: #666; font-size: 0.9rem;">
    <p>部活動 会計管理システム v5.0 | ☁️ Google Sheets連携版</p>
</div>
""", unsafe_allow_html=True)
