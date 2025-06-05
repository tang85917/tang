import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRC", page_icon="⛅")

st.title('🌈CRC_Data整理')

st.markdown('#### :green[災害CSVの進捗管理用DataをCopyしてください]')

if 'df' not in st.session_state:
    st.session_state.df = None
if 'df_split' not in st.session_state:
    st.session_state.df_split = None

def crc_copy():
    return pd.read_clipboard(sep='\t').dropna()

def time_to_minutes(time_str):
    if len(time_str) == 4:
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
    else:
        time_str = time_str.zfill(4)
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
    return hours * 60 + minutes

def remove_past_times(time_ranges_str):
    current_time = datetime.now()
    current_minutes = current_time.hour * 60 + current_time.minute
    
    time_ranges = time_ranges_str.split(',')
    valid_ranges = []
    
    for time_range in time_ranges:
        start, end = time_range.split('~')
        end_time = time_to_minutes(end)
        
        if end_time > current_minutes:
            valid_ranges.append(time_range)
    
    return ','.join(valid_ranges) if valid_ranges else None

def process_dataframe(df):
    new_rows = []
    
    for _, row in df.iterrows():
        updated_time_range = remove_past_times(row['Start Time ~ End Time'])
        
        if updated_time_range:
            new_row = row.copy()
            new_row['Start Time ~ End Time'] = updated_time_range
            new_rows.append(new_row)
    
    return pd.DataFrame(new_rows) if new_rows else pd.DataFrame()

def split_time_ranges(time_ranges_str):
    time_ranges = time_ranges_str.split(',')
    groups = []
    current_group = []
    
    for i, time_range in enumerate(time_ranges):
        start, end = time_range.split('~')
        start_time = time_to_minutes(start)
        
        if not current_group:
            current_group.append(time_range)
        else:
            first_end = time_to_minutes(current_group[0].split('~')[1])
            
            if start_time >= first_end:
                groups.append(','.join(current_group))
                current_group = [time_range]
            else:
                current_group.append(time_range)
    
    if current_group:
        groups.append(','.join(current_group))
    
    return groups

def split_dataframe(df):
    new_rows = []
    
    for _, row in df.iterrows():
        time_groups = split_time_ranges(row['Start Time ~ End Time'])
        
        for time_group in time_groups:
            new_row = row.copy()
            new_row['Start Time ~ End Time'] = time_group
            new_rows.append(new_row)
    
    return pd.DataFrame(new_rows)

def copy_to_clipboard(df):
    if df is not None:
        df.to_clipboard(sep='\t', index=False, header=False)
        return True
    return False

col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 3, 1])
with col1:
    copy_btn = st.button('Copy', key='crc_copy')

with col2:
    split_btn = st.button('Split', key='crc_split')

with col3:
    sharepoint_btn = st.button('SharePoint', key='crc_sharePoint')

with col5:
    reset_btn = st.button('Reset', key='crc_reset')

if copy_btn:
    df = crc_copy()
    st.session_state.df = process_dataframe(df)

if split_btn and st.session_state.df is not None:
    st.session_state.df = split_dataframe(st.session_state.df)

if sharepoint_btn and st.session_state.df is not None:
    success = copy_to_clipboard(st.session_state.df)
    if success:
        st.success('データをクリップボードにコピーしました')
    else:
        st.error('コピーに失敗しました')

if reset_btn:
    st.session_state.df = None
    st.success('DataFrameをリセットしました')

if st.session_state.df is not None:
    st.write("🌪️災害CSV_Data整理")
    st.dataframe(st.session_state.df, height=800)
