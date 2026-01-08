"""
Google Sheets連携ユーティリティ
gspreadを使用してGoogle Spreadsheetsに接続し、データを読み書きする
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Google Sheets APIのスコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# シート名の定義
SHEET_DATABASE = 'database'
SHEET_MEMBERS = 'members'
SHEET_DRIVERS = 'drivers'
SHEET_COLLECTION = 'collection_status'
SHEET_TRANSPORT_BALANCE = 'transportation_balance'


@st.cache_resource
def get_gspread_client():
    """Google Sheets APIクライアントを取得（キャッシュ）"""
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"⚠️ Google Sheets接続エラー: {e}")
        st.info("secrets.tomlの設定を確認してください")
        return None


@st.cache_resource
def get_spreadsheet():
    """スプレッドシートを取得（キャッシュ）"""
    client = get_gspread_client()
    if client is None:
        return None
    
    try:
        spreadsheet_id = st.secrets["spreadsheet"]["id"]
        spreadsheet = client.open_by_key(spreadsheet_id)
        return spreadsheet
    except Exception as e:
        st.error(f"⚠️ スプレッドシート取得エラー: {e}")
        return None


def get_or_create_worksheet(sheet_name: str, headers: list = None):
    """ワークシートを取得、なければ作成"""
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return None
    
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # シートが存在しない場合は作成
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        if headers:
            worksheet.update('A1', [headers])
    
    return worksheet


def load_sheet_as_dataframe(sheet_name: str, default_columns: list = None) -> pd.DataFrame:
    """シートをDataFrameとして読み込む"""
    worksheet = get_or_create_worksheet(sheet_name, default_columns)
    
    if worksheet is None:
        if default_columns:
            return pd.DataFrame(columns=default_columns)
        return pd.DataFrame()
    
    try:
        data = worksheet.get_all_records()
        if len(data) == 0:
            if default_columns:
                return pd.DataFrame(columns=default_columns)
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"シート '{sheet_name}' の読み込みエラー: {e}")
        if default_columns:
            return pd.DataFrame(columns=default_columns)
        return pd.DataFrame()


def save_dataframe_to_sheet(df: pd.DataFrame, sheet_name: str):
    """DataFrameをシートに保存（全データ上書き）"""
    worksheet = get_or_create_worksheet(sheet_name, df.columns.tolist())
    
    if worksheet is None:
        st.error("シートへの保存に失敗しました")
        return False
    
    try:
        # シートをクリアして書き込み
        worksheet.clear()
        
        # DataFrameが空でない場合のみ書き込み
        if len(df) > 0:
            # ヘッダーとデータを準備
            headers = df.columns.tolist()
            
            # すべてのデータを文字列に変換（NaNを空文字に）
            data = df.fillna('').astype(str).values.tolist()
            
            # ヘッダー + データを書き込み
            all_data = [headers] + data
            worksheet.update('A1', all_data)
        else:
            # 空の場合はヘッダーのみ
            worksheet.update('A1', [df.columns.tolist()])
        
        return True
    except Exception as e:
        st.error(f"シート '{sheet_name}' への保存エラー: {e}")
        return False


def append_row_to_sheet(row_data: dict, sheet_name: str):
    """シートに1行追加"""
    worksheet = get_or_create_worksheet(sheet_name)
    
    if worksheet is None:
        return False
    
    try:
        # ヘッダーを取得
        headers = worksheet.row_values(1)
        if not headers:
            headers = list(row_data.keys())
            worksheet.update('A1', [headers])
        
        # データを整形
        row = [str(row_data.get(h, '')) for h in headers]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"行の追加エラー: {e}")
        return False


# ======================
# 各シート用の読み込み・保存関数
# ======================

def load_database() -> pd.DataFrame:
    """取引履歴を読み込み"""
    df = load_sheet_as_dataframe(
        SHEET_DATABASE,
        ['日付', '種別', '科目', '金額', '備考', '決済方法']
    )
    if len(df) > 0:
        df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
        df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0)
        if '決済方法' not in df.columns:
            df['決済方法'] = '現金 (財布)'
    return df


def save_database(df: pd.DataFrame):
    """取引履歴を保存"""
    save_df = df.copy()
    if '日付' in save_df.columns:
        save_df['日付'] = pd.to_datetime(save_df['日付']).dt.strftime('%Y-%m-%d')
    return save_dataframe_to_sheet(save_df, SHEET_DATABASE)


def load_members() -> pd.DataFrame:
    """メンバーを読み込み"""
    df = load_sheet_as_dataframe(SHEET_MEMBERS, ['名前', '属性'])
    if len(df) > 0:
        df['名前'] = df['名前'].fillna('').astype(str)
        df['属性'] = df['属性'].fillna('Player').astype(str)
        df = df[df['名前'].str.strip() != ''].reset_index(drop=True)
    return df


def save_members(df: pd.DataFrame):
    """メンバーを保存"""
    return save_dataframe_to_sheet(df, SHEET_MEMBERS)


def load_drivers() -> pd.DataFrame:
    """ドライバーを読み込み"""
    df = load_sheet_as_dataframe(
        SHEET_DRIVERS,
        ['名前', '車種', '燃料タイプ', '燃費']
    )
    if len(df) > 0:
        df['名前'] = df['名前'].fillna('').astype(str)
        df['車種'] = df['車種'].fillna('').astype(str)
        df['燃料タイプ'] = df['燃料タイプ'].fillna('レギュラー').astype(str)
        df['燃費'] = pd.to_numeric(df['燃費'], errors='coerce').fillna(15.0)
        df = df[df['名前'].str.strip() != ''].reset_index(drop=True)
    return df


def save_drivers(df: pd.DataFrame):
    """ドライバーを保存"""
    return save_dataframe_to_sheet(df, SHEET_DRIVERS)


def load_collection() -> pd.DataFrame:
    """徴収状況を読み込み"""
    df = load_sheet_as_dataframe(SHEET_COLLECTION, ['名前'])
    if len(df) > 0:
        df['名前'] = df['名前'].fillna('').astype(str)
    return df


def save_collection(df: pd.DataFrame):
    """徴収状況を保存"""
    return save_dataframe_to_sheet(df, SHEET_COLLECTION)


def load_transport_balance() -> pd.DataFrame:
    """交通費会計を読み込み"""
    df = load_sheet_as_dataframe(
        SHEET_TRANSPORT_BALANCE,
        ['日付', '項目', '収入', '支出', '残高']
    )
    if len(df) > 0:
        df['収入'] = pd.to_numeric(df['収入'], errors='coerce').fillna(0)
        df['支出'] = pd.to_numeric(df['支出'], errors='coerce').fillna(0)
        df['残高'] = pd.to_numeric(df['残高'], errors='coerce').fillna(0)
    return df


def save_transport_balance(df: pd.DataFrame):
    """交通費会計を保存"""
    return save_dataframe_to_sheet(df, SHEET_TRANSPORT_BALANCE)


def add_transport_balance_entry(date: str, item: str, income: int, expense: int) -> int:
    """交通費会計に1行追加"""
    df = load_transport_balance()
    current = int(df['残高'].iloc[-1]) if len(df) > 0 else 0
    new_balance = current + income - expense
    
    new_entry = pd.DataFrame({
        '日付': [date],
        '項目': [item],
        '収入': [income],
        '支出': [expense],
        '残高': [new_balance]
    })
    
    df = pd.concat([df, new_entry], ignore_index=True)
    save_transport_balance(df)
    
    return new_balance
