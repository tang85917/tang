import pandas as pd
import streamlit as st
import altair as alt
import numpy as np

st.logo(r'Image\stco_log.jpg',size='large')
st.title('2025年就業実績データ')
st.write('')

with st.sidebar:
    radio=st.radio('表示期間を選択してください',['Dayly','Weekly','Monthly'],key='radio_2024',horizontal=True)
    st.image(r'Image\goa.png')
    st.image(r'Image\alshu.png')
    st.image(r'Image\aja.png')
#コラム設定
col1,col2=st.columns(2)
with col1:
    st.markdown(":blue[**2025年就業実績データ一覧**]👀")
with col2:
    check=st.checkbox('👈',key='check_2025')

if check:
    df=pd.read_csv('./data/2025.csv',index_col=0).fillna(0)
    df.index=pd.to_datetime(df.index)
    if radio=='Monthly':
        df=df.resample('M').sum()
    elif radio=='Weekly':
        df=df.resample('W').sum()
    else:
        df=df
    df.index=df.index.date
    st.dataframe(df,use_container_width=True)

col1,col2=st.columns(2)
with col1:
    st.markdown(":blue[**Project別トータル時間集計グラフ**]📊")
with col2:
    check_bar=st.checkbox('👈',key='check_bar=2025')

if check_bar:
    #データ処理
    df=pd.read_csv('./data/2025.csv',index_col=0).fillna(0)
    df_t=df.T
    df_t['total_time']=df_t.sum(axis=1)
    df_t=df_t.reset_index()
    #グラフ作成
    st.altair_chart(alt.Chart(df_t).mark_bar().encode(
        x=alt.X('index',title='Project'),y='total_time',color='index'
    ).properties(width=1200,height=600,title=alt.TitleParams(
        '2025年Projectトータル時間',fontSize=30,anchor='middle')))
    df_t=(df_t[['index','total_time']].set_index('index').rename_axis('Project'))
    st.dataframe(df_t,use_container_width=False)

col1,col2=st.columns(2)
with col1:
    st.markdown(":blue[**Project別セレクト折れ線グラフ**]📈")
with col2:
    check_line=st.checkbox('👈',key='check_line_2025')

if check_line:
    df=pd.read_csv('./data/2025.csv',index_col=0).fillna(0)
    df.index=pd.to_datetime(df.index)
    if radio=='Monthly':
        df=df.resample('M').sum()
    elif radio=='Weekly':
        df=df.resample('W').sum()
    else:
        df=df
    #マルチセレクトボックス
    all_select=st.checkbox('全選択',key='all_select_2025')
    default_selection=df.columns.tolist() if all_select else []
    select=st.multiselect('',df.columns,default_selection,
    placeholder='こちらからProjectを選んでください')
    #データの編集
    df_long = df.reset_index().melt(id_vars=['日付'], var_name='Project', value_name='Hours')
    if select:
        df_long = df_long[df_long['Project'].isin(select)]
        # 折れ線グラフを表示
        chart = alt.Chart(df_long).mark_line().encode(
            x='日付:T',y='Hours:Q',color='Project:N').properties(
            width=1200, height=600,title=alt.TitleParams('2025年Project時間推移',
                fontSize=30,anchor='middle'
            ))
        st.altair_chart(chart)
    