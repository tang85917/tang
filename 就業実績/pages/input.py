import streamlit as st
import datetime
import pandas as pd

col1,col2,col3=st.columns([2,1,1])
with col1:
    st.title('就業実績入力')
with col2:
    st.date_input('📅',datetime.date.today(),key='input_date')
with col3:
    open_all=st.checkbox('全てを開く')

# サイドバーに画像を表示
with st.sidebar:
    st.image(r'Image\goa.png', use_container_width=False)
    st.image(r'Image\alshu.png', use_container_width=False)
    st.image(r'Image\aja.png', use_container_width=False)

#8時シフト
shift_time8=[f"{h:02d}:{m:02d}~{h2:02d}:{m2:02d}"
             for h in range(8,17)
             for m,h2,m2 in[(0,h,30),(30,h+1,0)]]

#13時シフト
shift_time13=[f"{h:02d}:{m:02d}~{h2:02d}:{m2:02d}"
              for h in range(13,22)
              for m,h2,m2 in[(0,h,30),(30,h+1,0)]]

#分類の定義
df=pd.read_csv(r'data\category.csv',encoding='shift-jis')

category1=df['大分類']
category2=df['中分類']
category3=df['小分類']

#シフトの選択
choice_shift=st.radio('シフトを選んでください',['shift-8','shift-13'],horizontal=True,key='choice_shift')
check_shift=[]
if choice_shift=='shift-8':
    check_shift=shift_time8
elif choice_shift=='shift-13':
    check_shift=shift_time13

#分類の選択
for time in check_shift:
    with st.expander(f'{time}',expanded=open_all):
        col1,col2,col3=st.columns(3)
        with col1:
            st.selectbox('大分類',category1,key=f'category1{time}')
        with col2:
            st.selectbox('中分類',category2,key=f'category2{time}')
        with col3:
            st.selectbox('小分類',category3,key=f'category3{time}')


