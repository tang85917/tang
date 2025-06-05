import pandas as pd
import streamlit as st
import datetime
import altair as alt
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title('就業実績😫')
st.write('')
poc=st.expander('就業実績POC',icon='👽')
poc.write('Nishiyama')
poc.write('Arai')
poc.write('Tao')

st.logo(r'Image\stco_log.jpg',size='large')
with st.sidebar:
    #radio=st.radio('表示期間を選択してください',['Dayly','Weekly','Monthly'],key='radio_2024',horizontal=True)
    st.image(r'Image\goa.png')
    st.image(r'Image\alshu.png')
    st.image(r'Image\aja.png')

#先週のデータタイトルとチェックボックス
col1,col2=st.columns([2,6])
with col1:
    st.markdown("###  Last Week's Data")
with col2:
    Last_Week_chcek=st.checkbox('👈',key='Last_Week_chcek')

#先週のデータ表示
if Last_Week_chcek:   
    df=pd.read_csv('data/2025.csv',index_col=0).fillna(0)
    df.index=pd.to_datetime(df.index).date
    last_sat=next((day for day in reversed(df.index) if day.weekday()==5),None)
    last_sun=last_sat-datetime.timedelta(days=6)
    df_lastweek=df.loc[last_sun:last_sat]
    df_lastweek=df_lastweek.loc[:,(df_lastweek!=0).any()]
    df=st.dataframe(df_lastweek)    

    #棒グラフ
    df_bar=df_lastweek.T
    df_bar['total_time']=df_bar.sum(axis=1)
    df_bar=df_bar.reset_index()
    bar=alt.Chart(df_bar).mark_bar().encode(
        x=alt.X('index',title='Project'),y='total_time',color='index'
    ).properties(width=1000,height=500,title="先週Projectトータル時間")
    bar=bar.configure_title(fontSize=30,anchor='middle')
    st.altair_chart(bar)

    #円グラフ
    df_bar_sorted=df_bar.sort_values(by='total_time',ascending=False)
    df10=df_bar_sorted.iloc[:10]
    df_other_sum = df_bar_sorted.iloc[10:].sum(numeric_only=True)
    df_other_sum['index'] = 'Other'
    labels = df10['index'].tolist() + ['Other']
    values = df10['total_time'].tolist() + [df_other_sum['total_time']]

    pie_week=go.Figure(
        data=[go.Pie(labels=labels,
                    values=values,
                    hole=0.4,
                    pull=[0.08]
                    )]
)
    pie_week.update_traces(
        textinfo='percent+label',
        textfont_size=20,
        marker=dict(line=dict(color='#000000', width=2))
        
    )
    pie_week.update_layout(
        title_text='先週Project別作業時間割合（上位10とその他)',
        showlegend=True,
        title_font=dict(size=30),
        width=800,
        height=800
    )
    st.plotly_chart(pie_week)

#先月のデータタイトルとチェックボックス
col1,col2=st.columns([2,6])
with col1:
    st.markdown("### Last Month's Data")
with col2:
    Last_Month_check=st.checkbox('👈',key='Last_Month_check')

#先月のデータ表示
if Last_Month_check:
    df=pd.read_csv('data/2025.csv',index_col=0).fillna(0)
    df.index=pd.to_datetime(df.index).date
    last_me=next((me for me in reversed(df.index) if me.day==1),None)
    last_me=last_me-datetime.timedelta(days=1)
    last_ms=next((ms for ms in reversed(df.index[df.index<last_me]) if ms.day==1),None)
    df_lastmonth=df.loc[last_ms:last_me]
    df_lastmonth=df_lastmonth.loc[:,(df_lastmonth!=0).any()]
    df=st.dataframe(df_lastmonth)

    #棒グラフ
    df_bar=df_lastmonth.T
    df_bar['total_time']=df_bar.sum(axis=1)
    df_bar=df_bar.reset_index()
    bar=alt.Chart(df_bar).mark_bar().encode(
        x=alt.X('index',title='Project'),y='total_time',color='index'
    ).properties(width=1000,height=500,title="先月Projectトータル時間")
    bar=bar.configure_title(fontSize=30,anchor='middle')
    st.altair_chart(bar)
    
        #円グラフ
    df_bar_sorted=df_bar.sort_values(by='total_time',ascending=False)
    df10=df_bar_sorted.iloc[:10]
    df_other_sum = df_bar_sorted.iloc[10:].sum(numeric_only=True)
    df_other_sum['index'] = 'Other'
    labels = df10['index'].tolist() + ['Other']
    values = df10['total_time'].tolist() + [df_other_sum['total_time']]

    pie_month=go.Figure(
        data=[go.Pie(labels=labels,
                    values=values,
                    hole=0.4,
                    pull=[0.08]
                    )]
    )
    pie_month.update_traces(
        textinfo='percent+label',
        textfont_size=20,
        marker=dict(line=dict(color='#000000', width=2))
        
    )
    pie_month.update_layout(
        title_text='先月Project別作業時間割合（上位10とその他)',
        showlegend=True,
        title_font=dict(size=30),
        width=800,
        height=800
    )
    st.plotly_chart(pie_month)