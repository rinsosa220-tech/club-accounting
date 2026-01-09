import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
import math

# ======================
# 🔒 管理者専用アクセス制限
# ======================
# ログインしていない場合
if "role" not in st.session_state:
    st.warning("⚠️ このページを表示するにはログインが必要です。メインページからログインしてください。")
    st.stop()

# 管理者以外の場合
if st.session_state.get("role") != "admin":
    st.error("🚫 このページは管理者専用です。")
    st.stop()

# 親ディレクトリのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ページ設定
st.set_page_config(
    page_title="交通費精算 | 部活動 会計管理",
    page_icon="🚗",
    layout="wide"
)

# ======================
# 🔐 権限管理付き認証機能
# ======================
def check_password():
    """Admin/Guest権限を確認する"""
    
    # secrets.tomlにパスワードが設定されているか確認
    if "admin_password" not in st.secrets or "guest_password" not in st.secrets:
        st.session_state.role = "admin"
        st.session_state.authenticated = True
        return True
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "role" not in st.session_state:
        st.session_state.role = None
    
    if st.session_state.authenticated and st.session_state.role:
        return True
    
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <h1 style="color: #670317;">🔐 交通費精算システム</h1>
        <p style="color: #666;">部員専用ページです。パスワードを入力してください。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔑 パスワード", type="password", key="tc_password_input")
        
        if st.button("ログイン", use_container_width=True, type="primary"):
            if password == st.secrets["admin_password"]:
                st.session_state.authenticated = True
                st.session_state.role = "admin"
                st.rerun()
            elif password == st.secrets["guest_password"]:
                st.session_state.authenticated = True
                st.session_state.role = "guest"
                st.rerun()
            else:
                st.error("⚠️ パスワードが違います")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #888; font-size: 0.85rem;">
            <p>👤 管理者: 設定変更・計算実行が可能</p>
            <p>👁️ 一般部員: 閲覧のみ</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()
    return False

check_password()

# 現在の権限を取得
CURRENT_ROLE = st.session_state.get("role", "guest")
IS_ADMIN = CURRENT_ROLE == "admin"

# テーマカラー
PRIMARY_COLOR = "#670317"
PRIMARY_LIGHT = "#8b1a33"
SECONDARY_COLOR = "#495057"
BG_COLOR = "#f0f2f6"
CARD_BG = "#ffffff"

# ======================
# カスタムCSS
# ======================
st.markdown(f"""
<style>
    .stApp {{
        background-color: {BG_COLOR};
    }}
    
    .card {{
        background: {CARD_BG};
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    
    .section-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: #333;
        padding-left: 14px;
        border-left: 4px solid {PRIMARY_COLOR};
        margin-bottom: 18px;
    }}
    
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
    
    .kpi-card {{
        background: {CARD_BG};
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
        border: 1px solid #eee;
    }}
    
    .kpi-label {{
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 6px;
    }}
    
    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {PRIMARY_COLOR};
    }}
    
    .kpi-primary {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        border-radius: 14px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(103,3,23,0.25);
    }}
    
    .kpi-primary .kpi-label {{
        color: rgba(255,255,255,0.9);
    }}
    
    .kpi-primary .kpi-value {{
        color: #fff;
        font-size: 2.4rem;
    }}
    
    .kpi-secondary {{
        background: linear-gradient(135deg, {SECONDARY_COLOR} 0%, #6c757d 100%);
        border-radius: 14px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(73,80,87,0.25);
    }}
    
    .kpi-secondary .kpi-label {{
        color: rgba(255,255,255,0.9);
    }}
    
    .kpi-secondary .kpi-value {{
        color: #fff;
        font-size: 2.4rem;
    }}
    
    .member-item {{
        background: {CARD_BG};
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        border-left: 4px solid {PRIMARY_COLOR};
    }}
    
    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 600;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ======================
# Google Sheets連携（utils.sheetsモジュール使用）
# ======================
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sheets import (
    load_members, save_members,
    load_drivers, save_drivers,
    load_collection, save_collection,
    load_transport_balance, save_transport_balance,
    add_transport_balance_entry
)

FUEL_TYPES = ["レギュラー", "ハイオク", "軽油"]
MEMBER_TYPES = ["Player", "Manager"]

# ======================
# データクリーニング（幽霊部員削除）
# ======================
def cleanup_ghost_members():
    members = load_members()
    collection = load_collection()
    
    if len(collection) > 0 and len(members) > 0:
        valid_names = set(members['名前'].tolist())
        original_count = len(collection)
        collection = collection[collection['名前'].isin(valid_names)]
        
        if len(collection) < original_count:
            save_collection(collection)
            return original_count - len(collection)
    return 0

cleaned = cleanup_ghost_members()

# ======================
# Session State 初期化（初回のみSheets読み込み）
# ======================
if 'members_data' not in st.session_state:
    st.session_state.members_data = load_members()

if 'drivers_data' not in st.session_state:
    st.session_state.drivers_data = load_drivers()

if 'collection_data' not in st.session_state:
    st.session_state.collection_data = load_collection()

if 'dispatch_data' not in st.session_state:
    st.session_state.dispatch_data = None

if 'prev_drivers' not in st.session_state:
    st.session_state.prev_drivers = []

if 'gas_prices' not in st.session_state:
    st.session_state.gas_prices = {'regular': 170, 'premium': 180, 'diesel': 150}

# ======================
# ヘッダー
# ======================
st.markdown("""
<div class="app-header">
    <p class="app-title">🚗 交通費精算システム</p>
    <p class="app-subtitle">メンバー管理 • 遠征費計算 • 徴収管理</p>
</div>
""", unsafe_allow_html=True)

# 権限モード表示
col_mode1, col_mode2, col_mode3 = st.columns([1, 2, 1])
with col_mode2:
    if IS_ADMIN:
        st.success("👤 管理者モード - 設定変更・計算実行が可能")
    else:
        st.info("👁️ 閲覧モード - データの変更はできません")

if cleaned > 0:
    st.success(f"🧹 データクリーニング: {cleaned}件の不整合データを削除")

# ======================
# 3タブ構成
# ======================
tab1, tab2, tab3 = st.tabs(["👥 メンバー管理", "🚗 遠征費計算", "💰 徴収管理"])

# ======================
# タブ1: メンバー管理
# ======================
with tab1:
    col_left, col_right = st.columns([1.2, 1], gap="large")
    
    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">➕ 新規メンバー登録</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            new_name = st.text_input("名前", placeholder="メンバー名を入力", key="new_member_input", label_visibility="collapsed")
        with col2:
            new_type = st.radio("属性", MEMBER_TYPES, horizontal=True, key="new_member_type", label_visibility="collapsed")
        
        if st.button("➕ メンバーを登録", use_container_width=True, type="primary", disabled=not IS_ADMIN):
            if new_name and new_name.strip():
                if new_name.strip() not in st.session_state.members_data['名前'].values:
                    new_row = pd.DataFrame({'名前': [new_name.strip()], '属性': [new_type]})
                    st.session_state.members_data = pd.concat([st.session_state.members_data, new_row], ignore_index=True)
                    save_members(st.session_state.members_data)
                    
                    coll_row = pd.DataFrame({'名前': [new_name.strip()]})
                    for col in st.session_state.collection_data.columns:
                        if col != '名前':
                            coll_row[col] = 0
                    st.session_state.collection_data = pd.concat([st.session_state.collection_data, coll_row], ignore_index=True)
                    save_collection(st.session_state.collection_data)
                    st.success(f"✨ {new_name} を登録しました！")
                else:
                    st.warning("⚠️ その名前は既に登録されています")
            else:
                st.warning("⚠️ 名前を入力してください")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 登録済みメンバー一覧
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">📋 登録済みメンバー</p>', unsafe_allow_html=True)
        
        members = st.session_state.members_data
        valid_members = members[members['名前'].str.strip() != '']
        
        if len(valid_members) > 0:
            players = valid_members[valid_members['属性'] == 'Player']
            managers = valid_members[valid_members['属性'] == 'Manager']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🏃 Player", f"{len(players)} 名")
            with col2:
                st.metric("📋 Manager", f"{len(managers)} 名")
            
            st.divider()
            
            for idx, row in valid_members.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    icon = "🏃" if row['属性'] == 'Player' else "📋"
                    st.markdown(f"""
                    <div class="member-item">
                        <span style="font-weight:600;">{icon} {row['名前']}</span>
                        <span style="font-size:0.85rem; color:#666; background:#f0f0f0; padding:2px 10px; border-radius:12px;">{row['属性']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.members_data = members.drop(idx).reset_index(drop=True)
                        save_members(st.session_state.members_data)
                        st.success("削除しました")
        else:
            st.info("📭 メンバーが登録されていません")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🚗 ドライバー管理</p>', unsafe_allow_html=True)
        
        drivers = st.session_state.drivers_data.copy()
        if len(drivers) == 0:
            drivers = pd.DataFrame({'名前': [''], '車種': [''], '燃料タイプ': ['レギュラー'], '燃費': [15.0]})
        
        edited_drivers = st.data_editor(
            drivers,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "名前": st.column_config.TextColumn("👤 名前", width="medium"),
                "車種": st.column_config.TextColumn("🚗 車種", width="medium"),
                "燃料タイプ": st.column_config.SelectboxColumn("⛽ 燃料", options=FUEL_TYPES, width="small"),
                "燃費": st.column_config.NumberColumn("📊 燃費", min_value=1.0, max_value=50.0, format="%.1f km/L", step=0.5, width="small")
            },
            key="drivers_editor_main"
        )
        
        # 保存ボタンで明示的に保存（無限ループ防止）
        if st.button("💾 ドライバー情報を保存", use_container_width=True, type="primary", key="save_drivers", disabled=not IS_ADMIN):
            clean_df = edited_drivers[edited_drivers['名前'].str.strip() != ''].copy()
            st.session_state.drivers_data = clean_df
            save_drivers(clean_df)
            st.success("✨ 保存しました！")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ======================
# タブ2: 遠征費計算
# ======================
with tab2:
    with st.sidebar:
        st.markdown("### ⛽ ガソリン単価設定")
        st.session_state.gas_prices['regular'] = st.number_input("レギュラー (円/L)", 100, 300, st.session_state.gas_prices['regular'], 1)
        st.session_state.gas_prices['premium'] = st.number_input("ハイオク (円/L)", 100, 300, st.session_state.gas_prices['premium'], 1)
        st.session_state.gas_prices['diesel'] = st.number_input("軽油 (円/L)", 100, 300, st.session_state.gas_prices['diesel'], 1)
    
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">📋 遠征設定</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("日付", datetime.now(), key="event_date")
        with col2:
            event_name = st.text_input("遠征名", placeholder="例: 10月練習試合", key="event_name")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">👥 参加者選択</p>', unsafe_allow_html=True)
        
        members = st.session_state.members_data
        valid_members = members[members['名前'].str.strip() != '']
        
        if len(valid_members) > 0:
            member_names = valid_members['名前'].tolist()
            selected = st.multiselect("参加メンバー", member_names, member_names, key="participants")
            
            if len(selected) > 0:
                sel_df = valid_members[valid_members['名前'].isin(selected)]
                num_players = len(sel_df[sel_df['属性'] == 'Player'])
                num_managers = len(sel_df[sel_df['属性'] == 'Manager'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👥 合計", f"{len(selected)} 名")
                with col2:
                    st.metric("🏃 Player", f"{num_players} 名")
                with col3:
                    st.metric("📋 Manager", f"{num_managers} 名")
            else:
                num_players = 0
                num_managers = 0
        else:
            st.info("⚠️ メンバーを先に登録してください")
            num_players = 0
            num_managers = 0
            selected = []
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🚘 配車・走行データ</p>', unsafe_allow_html=True)
        
        drivers = st.session_state.drivers_data
        valid_drivers = drivers[drivers['名前'].str.strip() != '']
        
        if len(valid_drivers) > 0:
            driver_names = valid_drivers['名前'].tolist()
            sel_drivers = st.multiselect("配車ドライバー", driver_names, key="sel_drivers")
            
            if len(sel_drivers) > 0:
                if st.session_state.prev_drivers != sel_drivers:
                    rows = []
                    for name in sel_drivers:
                        info = valid_drivers[valid_drivers['名前'] == name]
                        if len(info) > 0:
                            rows.append({
                                'ドライバー': name,
                                '燃料': info['燃料タイプ'].values[0],
                                '燃費': float(info['燃費'].values[0]),
                                '距離': 0.0,
                                'ETC': 0,
                                '他': 0
                            })
                    st.session_state.dispatch_data = pd.DataFrame(rows)
                    st.session_state.prev_drivers = sel_drivers
                
                if st.session_state.dispatch_data is not None:
                    # 編集用データを取得
                    edited_dispatch = st.data_editor(
                        st.session_state.dispatch_data,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "ドライバー": st.column_config.TextColumn("👤 名前", disabled=True, width="small"),
                            "燃料": st.column_config.TextColumn("⛽ 燃料", disabled=True, width="small"),
                            "燃費": st.column_config.NumberColumn("km/L", disabled=True, format="%.1f", width="small"),
                            "距離": st.column_config.NumberColumn("🛣️ 距離", min_value=0.0, format="%.1f km", step=10.0, width="small"),
                            "ETC": st.column_config.NumberColumn("🛤️ ETC", min_value=0, format="¥%d", step=100, width="small"),
                            "他": st.column_config.NumberColumn("💰 他", min_value=0, format="¥%d", step=100, width="small")
                        },
                        key="dispatch_editor_main"
                    )
                    # 編集結果をsession_stateに反映（保存ボタン不要、表示用）
                    st.session_state.dispatch_data = edited_dispatch
        else:
            st.info("⚠️ ドライバーを先に登録してください")
            sel_drivers = []
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 計算結果
    if len(sel_drivers) > 0 and st.session_state.dispatch_data is not None:
        calc_df = st.session_state.dispatch_data.copy()
        calc_df['距離'] = pd.to_numeric(calc_df['距離'], errors='coerce').fillna(0)
        calc_df['ETC'] = pd.to_numeric(calc_df['ETC'], errors='coerce').fillna(0)
        calc_df['他'] = pd.to_numeric(calc_df['他'], errors='coerce').fillna(0)
        calc_df['燃費'] = pd.to_numeric(calc_df['燃費'], errors='coerce').fillna(15)
        
        prices = st.session_state.gas_prices
        def get_price(ft):
            if ft == "レギュラー": return prices['regular']
            elif ft == "ハイオク": return prices['premium']
            elif ft == "軽油": return prices['diesel']
            return prices['regular']
        
        calc_df['単価'] = calc_df['燃料'].apply(get_price)
        calc_df['使用L'] = calc_df['距離'] / calc_df['燃費']
        calc_df['使用L'] = calc_df['使用L'].replace([float('inf'), float('-inf')], 0)
        calc_df['ガソリン代'] = calc_df['使用L'] * calc_df['単価']
        calc_df['支給額'] = calc_df['ガソリン代'] + calc_df['ETC'] + calc_df['他']
        
        total_payment = calc_df['支給額'].sum()
        
        if total_payment > 0 and len(selected) > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">💰 計算結果</p>', unsafe_allow_html=True)
            
            total_units = num_managers + (num_players * 2)
            if total_units > 0:
                unit = math.ceil(total_payment / total_units)
                player_amt = unit * 2
                manager_amt = unit
                coll_total = (num_players * player_amt) + (num_managers * manager_amt)
                surplus = coll_total - total_payment
                
                # メインKPI表示（help引数でツールチップ追加）
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "🏃 Player 1人", 
                        f"¥{player_amt:,}", 
                        f"{num_players}名 = ¥{num_players * player_amt:,}",
                        help="計算式: (総額 ÷ 按分人数) × 2"
                    )
                with col2:
                    st.metric(
                        "📋 Manager 1人", 
                        f"¥{manager_amt:,}", 
                        f"{num_managers}名 = ¥{num_managers * manager_amt:,}",
                        help="計算式: 総額 ÷ 按分人数"
                    )
                with col3:
                    st.metric(
                        "🚗 ドライバー支払", 
                        f"¥{total_payment:,.0f}", 
                        f"端数 +¥{surplus:,.0f}",
                        help="ガソリン代 + ETC + その他経費"
                    )
                
                # 計算式の詳細アコーディオン
                with st.expander("🧮 計算式の詳細を見る (クリックして展開)", expanded=False):
                    st.markdown("### 📐 傾斜配分方式")
                    st.markdown("""
                    > **Player : Manager = 2 : 1** の比率で負担を配分します。
                    > これにより、マネージャーの負担を軽減しています。
                    """)
                    
                    st.divider()
                    
                    # 基本数式（LaTeX）
                    st.markdown("#### 1️⃣ 基本数式")
                    st.latex(r"""
                    負担単位 = \left\lceil \frac{交通費総額}{マネージャー数 + (プレーヤー数 \times 2)} \right\rceil
                    """)
                    
                    st.divider()
                    
                    # 計算過程（実際の数値）
                    st.markdown("#### 2️⃣ 計算過程")
                    
                    # ガソリン代の内訳
                    gas_total = calc_df['ガソリン代'].sum()
                    etc_total = calc_df['ETC'].sum()
                    other_total = calc_df['他'].sum()
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"""
                        **交通費総額の内訳:**
                        - ⛽ ガソリン代: **¥{gas_total:,.0f}**
                        - 🛤️ ETC代: **¥{etc_total:,.0f}**
                        - 💰 その他: **¥{other_total:,.0f}**
                        - **合計: ¥{total_payment:,.0f}**
                        """)
                    with col_b:
                        st.markdown(f"""
                        **按分人数（分母）の計算:**
                        - 👥 MG: {num_managers}人 × 1単位 = {num_managers}
                        - 🏃 PL: {num_players}人 × 2単位 = {num_players * 2}
                        - **合計: {total_units} 単位**
                        """)
                    
                    st.markdown(f"""
                    **1単位あたりの金額:**
                    ```
                    ⌈ {total_payment:,.0f} ÷ {total_units} ⌉ = ⌈ {total_payment / total_units:,.1f} ⌉ = ¥{unit:,}
                    ```
                    """)
                    
                    st.divider()
                    
                    # 最終結果
                    st.markdown("#### 3️⃣ 最終結果")
                    
                    result_col1, result_col2 = st.columns(2)
                    with result_col1:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #670317 0%, #8b1a33 100%); color: white; padding: 16px; border-radius: 12px; text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">🏃 プレーヤー (2単位)</div>
                            <div style="font-size: 1.8rem; font-weight: 800;">¥{player_amt:,}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{num_players}名 × ¥{player_amt:,} = ¥{num_players * player_amt:,}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with result_col2:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #495057 0%, #6c757d 100%); color: white; padding: 16px; border-radius: 12px; text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">📋 マネージャー (1単位)</div>
                            <div style="font-size: 1.8rem; font-weight: 800;">¥{manager_amt:,}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{num_managers}名 × ¥{manager_amt:,} = ¥{num_managers * manager_amt:,}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 端数処理の説明
                    if surplus > 0:
                        st.info(f"💡 **端数処理**: 切り上げにより **¥{surplus:,.0f}** の余剰が発生します。この余剰は交通費特別会計に繰り入れられます。")
                
                st.divider()
                
                if st.button("📝 確定して徴収リストに追加", use_container_width=True, type="primary", disabled=not IS_ADMIN):
                    if event_name:
                        coll_df = st.session_state.collection_data.copy()
                        col_name = event_name
                        
                        if col_name not in coll_df.columns:
                            coll_df[col_name] = 0
                        
                        for name in selected:
                            if name in coll_df['名前'].values:
                                m_type = valid_members[valid_members['名前'] == name]['属性'].values
                                if len(m_type) > 0:
                                    amt = manager_amt if m_type[0] == 'Manager' else player_amt
                                    coll_df.loc[coll_df['名前'] == name, col_name] = amt
                        
                        st.session_state.collection_data = coll_df
                        save_collection(coll_df)
                        
                        driver_list = ', '.join(calc_df[calc_df['支給額'] > 0]['ドライバー'].tolist())
                        add_transport_balance_entry(event_date.strftime('%Y-%m-%d'), f"{col_name} ({driver_list})", 0, int(total_payment))
                        
                        st.success("✨ 徴収リストに追加しました！")
                        st.balloons()
                    else:
                        st.warning("⚠️ 遠征名を入力してください")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ======================
# タブ3: 徴収管理
# ======================
with tab3:
    col_left, col_right = st.columns([1.5, 1], gap="large")
    
    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">📊 現在の回収状況</p>', unsafe_allow_html=True)
        
        coll_df = st.session_state.collection_data.copy()
        
        if len(coll_df) > 0 and len(coll_df.columns) > 1:
            coll_df['名前'] = coll_df['名前'].fillna('').astype(str)
            event_cols = [c for c in coll_df.columns if c != '名前']
            
            if len(event_cols) > 0:
                for c in event_cols:
                    coll_df[c] = pd.to_numeric(coll_df[c], errors='coerce').fillna(0).astype(int)
                
                coll_df['未払計'] = coll_df[event_cols].sum(axis=1)
                
                # 回収状況サマリ
                total_unpaid = coll_df['未払計'].sum()
                unpaid_count = len(coll_df[coll_df['未払計'] > 0])
                total_count = len(coll_df)
                paid_rate = (total_count - unpaid_count) / total_count if total_count > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💴 未回収総額", f"¥{total_unpaid:,}")
                with col2:
                    st.metric("👥 未払者数", f"{unpaid_count} 名")
                with col3:
                    st.metric("📈 回収完了率", f"{paid_rate*100:.0f}%")
                
                st.divider()
                
                max_due = coll_df['未払計'].max() if coll_df['未払計'].max() > 0 else 1
                coll_df['回収率'] = 1.0 - (coll_df['未払計'] / max_due)
                
                display_cols = ['名前'] + event_cols + ['未払計', '回収率']
                display_df = coll_df[display_cols].copy()
                
                col_config = {
                    "名前": st.column_config.TextColumn("👤 名前", disabled=True, width="medium"),
                    "未払計": st.column_config.NumberColumn("📊 未払計", format="¥%d", disabled=True, width="small"),
                    "回収率": st.column_config.ProgressColumn("✅ 回収率", min_value=0, max_value=1, width="small")
                }
                for c in event_cols:
                    col_config[c] = st.column_config.NumberColumn(c, format="¥%d", step=100, width="small")
                
                edited_coll = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=col_config,
                    key="collection_editor_main"
                )
                
                # 保存ボタンで明示的に保存
                if st.button("💾 徴収状況を保存", use_container_width=True, type="primary", key="save_coll", disabled=not IS_ADMIN):
                    for col in event_cols:
                        if col in edited_coll.columns:
                            st.session_state.collection_data[col] = edited_coll[col]
                    save_collection(st.session_state.collection_data)
                    st.success("✨ 保存しました！")
            else:
                st.info("📭 徴収イベントがありません")
        else:
            st.info("📭 徴収データがありません")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">💰 交通費会計</p>', unsafe_allow_html=True)
        
        balance_df = load_transport_balance()
        if len(balance_df) > 0:
            current = balance_df['残高'].iloc[-1]
            income = balance_df['収入'].sum()
            expense = balance_df['支出'].sum()
            
            st.metric("💰 現在残高", f"¥{current:,}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📈 収入累計", f"¥{income:,}")
            with col2:
                st.metric("📉 支出累計", f"¥{expense:,}")
        else:
            st.info("📭 取引履歴がありません")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        event_cols = [c for c in st.session_state.collection_data.columns if c != '名前']
        if len(event_cols) > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">✅ 徴収完了処理</p>', unsafe_allow_html=True)
            
            sel_event = st.selectbox("イベント選択", event_cols, key="complete_event")
            
            if st.button("💰 全員徴収完了として記録", use_container_width=True, type="primary", disabled=not IS_ADMIN):
                collected = st.session_state.collection_data[sel_event].sum()
                st.session_state.collection_data[sel_event] = 0
                save_collection(st.session_state.collection_data)
                
                add_transport_balance_entry(datetime.now().strftime('%Y-%m-%d'), f"{sel_event} 徴収完了", int(collected), 0)
                
                st.success(f"✨ ¥{collected:,} を収入として計上しました！")
            
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 24px 0 12px 0; color: #999; font-size: 0.8rem;">
    交通費精算システム v5.0 - Stable Edition
</div>
""", unsafe_allow_html=True)
