# -*- coding: utf-8 -*-
import pandas as pd
import sys
import os
sys.path.append('c:/Users/rinso/OneDrive/デスクトップ/club-app')
from utils.sheets import load_collection, save_collection, load_members, save_members

MEMBER_ORDER = [
    '新井　稜平', '飯尾　郁夢', '伊田　悠太', '譲尾　進之介',
    '赤阪　匠汰', '小泉　諭示', '阪井　裕貴', '田中　宏季',
    '白井　悠也', '新名　崇行', '須田　光', '松村　康生', '吉田　倫太郎',
    '梅田　隼作', '長尾　昌浩', '森　尊慈', '山本　晃輔',
    '植田　壮祐', '植村　亮', '大倉　颯太', '小貫　結斗', '千菊　優一', '次田',
    '伊藤　大知', '大崎　公大', '尾崎　友洋', '小野　弘人', '小谷　健人', '左官　瑞輝', '中島　星哉', '堀田　翔太郎', '山﨑　優樹', '弓削　智生',
    '安藤　宇乃', '小寺　胡春', '畑守　実菜',
    '岩﨑　史真', '児島　由奈', '宅間　菜月', '寺川　結花', '仲野　亜美',
    '井上　沙耶', '閤師　楓', '佐藤　萌音', '東田　絢音',
    '長野　乃絵', '船寄　紗生', '増渕　花里奈', '向井　結菜'
]

# Update Collection
df_coll = load_collection()
new_coll = pd.DataFrame({'名前': MEMBER_ORDER})
if len(df_coll) > 0 and '名前' in df_coll.columns:
    for col in df_coll.columns:
        if col != '名前' and col != 'O':
            mapping = dict(zip(df_coll['名前'], df_coll[col]))
            new_coll[col] = new_coll['名前'].map(mapping).fillna(0).astype(int)
save_collection(new_coll)

# Update Members
mgr_start_idx = MEMBER_ORDER.index('安藤　宇乃')
roles = ['Player'] * mgr_start_idx + ['Manager'] * (len(MEMBER_ORDER) - mgr_start_idx)
new_mem = pd.DataFrame({'名前': MEMBER_ORDER, '役職': roles})
save_members(new_mem)

print('Successfully updated via utf-8 script!')
