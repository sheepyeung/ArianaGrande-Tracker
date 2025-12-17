import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random
import urllib.parse
import base64
import json
import glob
from datetime import datetime

# --- 1. 🎨 主题配置 ---
THEMES = {
    "Elphaba Green": ("#2E8B57", "#98FB98"),
    "Glinda Pink": ("#FF1493", "#FFB6C1"),
    "Wicked Mix": ("#FF69B4", "#50C878"),
    "Eternal Sunshine": ("#722F37", "#A52A2A"),
    "Brighter Days": ("#1E90FF", "#87CEEB"),
    "Dangerous Woman": ("#333333", "#9370DB"),
    "Sweetener": ("#A0A0A0", "#F5F5DC"),
    "Positions": ("#696969", "#D3D3D3"),
    "Thank u, next": ("#000000", "#FFC0CB"),
    "My Everything": ("#9400D3", "#EE82EE"),
    "Yours Truly": ("#4682B4", "#ADD8E6")
}

THEME_IMAGE_MAP = {
    "Elphaba Green": "WICKED.jpg", "Glinda Pink": "WICKED.jpg", "Wicked Mix": "WICKED.jpg",
    "Eternal Sunshine": "ETERNALSUNSHINE.jpg", "Brighter Days": "BRIGHTERDAYSAHEAD.jpg",
    "Dangerous Woman": "DANGEROUSWOMAN.jpg", "Sweetener": "SWEETENER.jpg",
    "Positions": "POSITIONS.jpg", "Thank u, next": "THANKUNEXT.jpg",
    "My Everything": "MYEVERYTHING.jpg", "Yours Truly": "YOURSTRULY.jpg"
}

# 随机选择主题
theme_name, (primary_color, secondary_color) = random.choice(list(THEMES.items()))

st.set_page_config(page_title=f"Ari-Stats: {theme_name}", page_icon="🦋", layout="wide")

# --- CSS 配置 ---
st.markdown(f"""
<style>
    /* 全局字体 */
    .stApp, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .stDataFrame, .stMetric, button, input, a {{
        font-family: 'Times New Roman', Times, serif !important;
    }}
    div[data-testid="stMetricValue"], div[data-testid="stMetricDelta"] {{
        font-family: 'Times New Roman', Times, serif !important;
    }}
    i, .material-icons, [data-testid="stExpanderToggleIcon"] {{
        font-family: "Source Sans Pro", sans-serif !important;
    }}
    /* 背景渐变 */
    .stApp {{ background: linear-gradient(to bottom, {secondary_color}25, #ffffff); background-attachment: fixed; }}
    /* 标题颜色 */
    h1, h2, h3, h4 {{ color: {primary_color} !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); }}
    
    /* Metric 卡片样式 */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid {primary_color}40;
        border-left: 5px solid {primary_color};
        border-radius: 12px; 
        padding: 15px 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }}
    
    /* Big Stat Banner */
    .big-stat {{
        background: linear-gradient(to right, rgba(255,255,255,0.95), {secondary_color}30, rgba(255,255,255,0.95));
        border: 2px solid {primary_color}; color: {primary_color};
        font-size: 42px; font-weight: bold; text-align: center;
        padding: 25px; border-radius: 25px; margin-bottom: 25px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        font-family: 'Times New Roman', Times, serif !important;
    }}
    .sub-stat {{ font-size: 18px; color: #555; display: block; margin-top: 5px; font-family: 'Times New Roman', serif !important; }}
    .date-stat {{ font-size: 14px; color: #888; display: block; margin-top: 15px; font-weight: normal; font-family: 'Times New Roman', serif !important; }}
    
    .spotify-card {{
        background: white; border: 1px solid {primary_color}; border-radius: 8px;
        padding: 10px; text-align: center; text-decoration: none; color: #333;
        display: block; transition: 0.3s; margin-bottom: 10px;
        font-family: 'Times New Roman', serif !important;
    }}
    .spotify-card:hover {{ background: {secondary_color}40; transform: translateY(-2px); }}
    
    .media-btn {{
        display: inline-block; padding: 10px 20px; margin: 5px;
        border-radius: 20px; text-decoration: none; color: white; font-weight: bold;
        transition: 0.3s; border: none;
        font-family: 'Times New Roman', serif !important;
    }}
    .media-btn:hover {{ opacity: 0.9; transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
    .footer {{
        margin-top: 20px; padding: 20px; background-color: rgba(255,255,255,0.6);
        border-top: 1px solid {primary_color}; text-align: center; color: #555; border-radius: 10px;
        font-family: 'Times New Roman', serif !important;
    }}
    img {{ border-radius: 15px; border: 3px solid {primary_color}; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# --- 辅助函数 ---
def normalize_text(text):
    if not isinstance(text, str): return str(text)
    text = text.replace("â€™", "'").replace("’", "'").replace("â„¢", "")
    text = text.replace("*", "").strip()
    return text

def get_image_base64(path):
    if not os.path.exists(path): return ""
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def clean_number(x):
    try: return int(str(x).replace(',', '').replace('+', '').split('.')[0])
    except: return 0

def standardize_columns(df, is_album=False):
    """
    统一列名，解决 Daily Raw, Daily_Raw, Daily 等不一致问题。
    强制生成 'Daily_Num' 和 'Total_Num' (如果是专辑) 列。
    """
    if df is None: return None
    
    # 统一 Daily 列
    if 'Daily_Num' not in df.columns:
        if 'Daily_Raw' in df.columns:
            df['Daily_Num'] = df['Daily_Raw'].apply(clean_number)
        elif 'Daily Raw' in df.columns:
            df['Daily_Num'] = df['Daily Raw'].apply(clean_number)
        elif 'Daily' in df.columns:
            df['Daily_Num'] = df['Daily'].apply(clean_number)
        else:
            df['Daily_Num'] = 0
            
    # 如果是专辑，统一 Total 列
    if is_album:
        if 'Total_Num' not in df.columns:
            if 'Total' in df.columns:
                df['Total_Num'] = df['Total'].apply(clean_number)
            elif 'Streams' in df.columns: # 有时专辑总流媒列名为 Streams
                df['Total_Num'] = df['Streams'].apply(clean_number)
            else:
                df['Total_Num'] = 0
                
    # 如果是单曲，确保 Streams_Num
    if not is_album:
         if 'Streams_Num' not in df.columns:
            if 'Streams' in df.columns:
                df['Streams_Num'] = df['Streams'].apply(clean_number)
            else:
                df['Streams_Num'] = 0
                
    return df

# --- 数据加载引擎 ---
DATA_DIR = "daily_data"

@st.cache_data(ttl=600)
def load_latest_data():
    """查找并加载最新的 songs, albums 和 meta 文件"""
    if not os.path.exists(DATA_DIR):
        return None, None, None, None

    # 获取所有 songs 文件并排序
    song_files = sorted(glob.glob(os.path.join(DATA_DIR, "*_songs.csv")))
    
    if not song_files:
        return None, None, None, None

    latest_song_file = song_files[-1]
    date_str = os.path.basename(latest_song_file).split('_')[0]
    
    # 构造对应的其他文件名
    latest_meta_file = os.path.join(DATA_DIR, f"{date_str}_meta.json")
    latest_album_file = os.path.join(DATA_DIR, f"{date_str}_albums.csv")
    
    # 尝试加载
    try:
        # 1. 加载 Songs
        df_songs = pd.read_csv(latest_song_file)
        df_songs['Song'] = df_songs['Song'].apply(normalize_text)
        df_songs = standardize_columns(df_songs, is_album=False)
        
        # 2. 加载 Meta
        with open(latest_meta_file, 'r') as f:
            meta_data = json.load(f)
            
        # 3. 加载 Albums
        if os.path.exists(latest_album_file):
            df_albums = pd.read_csv(latest_album_file)
            df_albums = standardize_columns(df_albums, is_album=True)
        else:
            df_albums = None
            
        return df_songs, df_albums, meta_data, date_str
    except Exception as e:
        st.error(f"Error loading files for {date_str}: {e}")
        return None, None, None, None

@st.cache_data(ttl=3600)
def get_career_history():
    """读取所有 meta.json 构建生涯日增趋势"""
    if not os.path.exists(DATA_DIR): return pd.DataFrame()
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*_meta.json")))
    history = []
    if len(files) < 2: return pd.DataFrame()
    for i in range(1, len(files)):
        curr_file, prev_file = files[i], files[i-1]
        date_str = os.path.basename(curr_file).split('_')[0]
        try:
            with open(curr_file, 'r') as f: curr_meta = json.load(f)
            with open(prev_file, 'r') as f: prev_meta = json.load(f)
            daily_inc = curr_meta['career_total'] - prev_meta['career_total']
            if daily_inc > 0 and daily_inc < 100_000_000:
                history.append({'Date': date_str, 'Daily': daily_inc})
        except: continue
    return pd.DataFrame(history)

@st.cache_data(ttl=3600)
def get_item_history(item_name, is_album=False):
    if not os.path.exists(DATA_DIR): return pd.DataFrame()
    suffix = "_albums.csv" if is_album else "_songs.csv"
    files = sorted(glob.glob(os.path.join(DATA_DIR, f"*{suffix}")))
    history = []
    col_name = "Base_Name" if is_album else "Song"
    for f in files:
        date_str = os.path.basename(f).split('_')[0]
        try:
            df = pd.read_csv(f)
            if not is_album: df[col_name] = df[col_name].apply(normalize_text)
            
            # 临时标准化以获取数据
            df = standardize_columns(df, is_album=is_album)
            
            row = df[df[col_name] == item_name]
            if not row.empty:
                val = row.iloc[0]['Daily_Num']
                history.append({'Date': date_str, 'Daily': val})
        except: continue
    return pd.DataFrame(history)

@st.cache_data(ttl=3600)
def get_listeners_history():
    if not os.path.exists(DATA_DIR): return pd.DataFrame()
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*_meta.json")))
    history = []
    for f in files:
        date_str = os.path.basename(f).split('_')[0]
        try:
            with open(f, 'r') as meta_file:
                meta = json.load(meta_file)
                l_val = meta.get('listeners', 0)
                if isinstance(l_val, dict): l_val = l_val.get('count', 0)
                if l_val > 0: history.append({'Date': date_str, 'Listeners': l_val})
        except: continue
    return pd.DataFrame(history)

@st.cache_data(ttl=3600)
def get_7day_average():
    if not os.path.exists(DATA_DIR): return {}
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*_songs.csv")))
    recent_files = files[-7:]
    if len(recent_files) < 2: return {}
    all_dailies = []
    for f in recent_files:
        try:
            df = pd.read_csv(f)
            df['Song'] = df['Song'].apply(normalize_text)
            df = standardize_columns(df, is_album=False)
            all_dailies.append(df[['Song', 'Daily_Num']].rename(columns={'Daily_Num': 'Daily'}))
        except: pass
    if not all_dailies: return {}
    big_df = pd.concat(all_dailies)
    return big_df.groupby('Song')['Daily'].mean().to_dict()

def get_spotify_card_html(label, song_name, value_text):
    query = f"Ariana Grande {song_name}"
    link = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
    return f"""
    <a href="{link}" target="_blank" class="spotify-card">
        <span class="card-label">{label} <span class="spotify-icon">▶ Listen</span></span>
        <span class="card-song">{song_name}</span>
        <span class="card-val">{value_text}</span>
    </a>
    """

def generate_random_predictions(df_songs, df_albums):
    pool = []
    if df_albums is not None and not df_albums.empty:
        alb_sorted = df_albums.sort_values('Total_Num', ascending=False).reset_index(drop=True)
        for i in range(len(alb_sorted)-1):
            leader = alb_sorted.iloc[i]
            chaser = alb_sorted.iloc[i+1]
            gap = leader['Total_Num'] - chaser['Total_Num']
            speed = chaser.get('Daily_Num', 0) - leader.get('Daily_Num', 0)
            if speed > 0 and gap > 0:
                days = gap / speed
                if days < 2000:
                    pool.append((f"💿 {chaser['Base_Name']} 🚀 {leader['Base_Name']}", f"差距 {gap//1000000}M | 约 {int(days)} 天"))
    for _, row in df_songs.head(50).iterrows():
        curr, inc = row['Streams_Num'], row.get('Daily_Num', 0)
        if inc > 0:
            next_goal = ((curr // 100000000) + 1) * 100000000
            days = (next_goal - curr) / inc
            if days < 365:
                pool.append((f"🎵 {row['Song']} ✨ {next_goal/100000000:.1f}亿", f"还差 {(next_goal-curr)//1000}k | 约 {int(days)} 天"))
    if len(pool) > 12: return random.sample(pool, 12)
    else: return pool

# --- 6. UI 主程序 ---
with st.sidebar:
    st.markdown("### 🦋 Ari-Stats 30.1 (Fix)")
    st.caption(f"Theme: **{theme_name}**")
    theme_img = THEME_IMAGE_MAP.get(theme_name)
    if theme_img and os.path.exists(theme_img): st.image(theme_img, caption=f"{theme_name} Era", use_container_width=True)
    if os.path.exists("ARIANA.jpg"): st.image("ARIANA.jpg", caption="Ariana Grande", use_container_width=True)
    st.info("💡 数据源: GitHub Repository\n(读取 daily_data 文件夹最新上传)")

st.title(f"✨ Ariana Grande Data Universe ✨")

# 加载数据
final_songs_df, final_albums_df, today_meta, data_date = load_latest_data()

if final_songs_df is not None and today_meta is not None:
    
    # 核心数据计算
    career_total = today_meta.get('career_total', 0)
    
    # 计算今日总增量 (使用标准化后的 Daily_Num)
    real_career_daily = final_songs_df['Daily_Num'].sum()

    # 计算 Listeners 变化
    l_hist = get_listeners_history()
    real_listeners_change = 0
    if len(l_hist) >= 2:
        try:
            curr_l = l_hist.iloc[-1]['Listeners']
            prev_l = l_hist.iloc[-2]['Listeners']
            real_listeners_change = curr_l - prev_l
        except: pass

    # 专辑份额计算
    if final_albums_df is not None:
        if real_career_daily > 0: 
            final_albums_df['Daily_Share'] = (final_albums_df['Daily_Num'] / real_career_daily * 100).round(2).astype(str) + '%'
        else: final_albums_df['Daily_Share'] = "0%"
        if career_total > 0:
            final_albums_df['Total_Share'] = (final_albums_df['Total_Num'] / career_total * 100).round(2).astype(str) + '%'
        else: final_albums_df['Total_Share'] = "0%"

    count_1b = len(final_songs_df[final_songs_df['Streams_Num'] >= 1_000_000_000])
    count_100m = len(final_songs_df[final_songs_df['Streams_Num'] >= 100_000_000])
    
    l_count = today_meta.get('listeners', 0)
    l_rank = today_meta.get('listeners_rank', 0)
    l_peak = today_meta.get('listeners_peak', 0)
    l_pk_c = today_meta.get('listeners_pk_count', 0)
    if isinstance(l_count, dict): l_count = l_count.get('count', 0) 
    
    listeners_html = (
        f"<div style='margin-top: 15px; padding-top: 15px; border-top: 1px dashed {primary_color}80;'>"
        f"👥 月收听人数: {l_count:,} <span style='font-size:16px; color:#555;'>(Rank #{l_rank})</span><br>"
        f"<span class='sub-stat' style='font-size:16px;'>较昨日: {real_listeners_change:+d} | 峰值: #{l_peak} ({l_pk_c:,})</span>"
        "</div>"
    )

    st.markdown(f"""
    <div class="big-stat">
        🌍 生涯总流媒: {career_total:,}<br>
        <span class="sub-stat">🔥 今日总增量: +{real_career_daily:,}</span>
        {listeners_html}
        <span class="date-stat">📅 数据日期: {data_date} (Latest Upload)</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("👥 点击查看：月收听人数历史趋势"):
        l_hist_df = get_listeners_history()
        if not l_hist_df.empty:
            fig_l = px.line(l_hist_df, x='Date', y='Listeners', markers=True, title="Monthly Listeners History", height=450)
            fig_l.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"), xaxis_title=None, yaxis_title=None, hovermode="x unified")
            fig_l.update_traces(line_color=primary_color, line_width=3)
            st.plotly_chart(fig_l, use_container_width=True)
        else: st.caption("暂无历史数据")
    
    top_song_d = final_songs_df.sort_values('Daily_Num', ascending=False).iloc[0]
    top_song_t = final_songs_df.sort_values('Streams_Num', ascending=False).iloc[0]
    
    # --- 核心UI ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1: 
        st.metric("📊 日增总量", f"{real_career_daily:,}", "Updated")

    with c2: 
        st.metric("🔥 最佳日增", top_song_d['Song'], f"+{top_song_d['Daily_Num']:,}")
        lnk = f"https://open.spotify.com/search/{urllib.parse.quote('Ariana Grande ' + top_song_d['Song'])}"
        st.markdown(f"<div style='text-align:center'><a href='{lnk}' target='_blank' style='text-decoration:none; color:{primary_color};font-weight:bold;font-size:14px;'>▶ Listen on Spotify</a></div>", unsafe_allow_html=True)

    with c3: 
        st.metric("👑 总量冠军", top_song_t['Song'], f"{top_song_t['Streams_Num']:,}")
        lnk = f"https://open.spotify.com/search/{urllib.parse.quote('Ariana Grande ' + top_song_t['Song'])}"
        st.markdown(f"<div style='text-align:center'><a href='{lnk}' target='_blank' style='text-decoration:none; color:{primary_color};font-weight:bold;font-size:14px;'>▶ Listen on Spotify</a></div>", unsafe_allow_html=True)

    if final_albums_df is not None:
        with c4: 
            st.metric("💿 专辑收录", "eternal sunshine (deluxe)", f"{len(final_albums_df)} 曲")
            lnk = "https://open.spotify.com/album/5EYKrEDnKhhcNxGedaRQeK"
            st.markdown(f"<div style='text-align:center'><a href='{lnk}' target='_blank' style='text-decoration:none; color:{primary_color};font-weight:bold;font-size:14px;'>▶ Listen on Spotify</a></div>", unsafe_allow_html=True)

    with c5: st.metric("🏆 破10亿(1B)", f"{count_1b} 首")
    with c6: st.metric("💎 破1亿(100M)", f"{count_100m} 首")

    st.write("") 
    with st.expander("📈 点击查看：生涯日增历史趋势 (Total Daily Streams History)", expanded=False):
        hist_df = get_career_history()
        if not hist_df.empty:
            fig_hist = px.line(hist_df, x='Date', y='Daily', markers=True, height=450)
            fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), font=dict(family="Times New Roman"), xaxis_title=None, yaxis_title=None, hovermode="x unified")
            fig_hist.update_traces(line_color=primary_color, line_width=3)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
             st.caption("暂无足够的历史数据生成趋势图")

    st.divider()

    st.subheader("🔮 未来水晶球")
    preds = generate_random_predictions(final_songs_df, final_albums_df)
    if preds:
        chunk = 4
        for i in range(0, len(preds), chunk):
            cols = st.columns(chunk)
            for j, (t, s) in enumerate(preds[i:i+chunk]):
                with cols[j]: st.info(f"**{t}**\n\n_{s}_")
    
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🔥 单曲日增", "💎 单曲总榜", "💿 专辑日增", "🏛️ 专辑总榜"])
    color_map = "RdPu" if "Pink" in theme_name else ("Viridis" if "Green" in theme_name else "Turbo")

    with tab1:
        st.markdown("#### 🔥 单曲日增 (Top 150)")
        with st.expander("🔎 查询单曲历史走势"):
            all_songs_list = final_songs_df['Song'].unique().tolist()
            selected_song_hist = st.selectbox("选择歌曲查看历史:", all_songs_list, index=0)
            if selected_song_hist:
                song_hist_df = get_item_history(selected_song_hist, is_album=False)
                if not song_hist_df.empty:
                    fig_s = px.line(song_hist_df, x='Date', y='Daily', markers=True, title=f"Trend: {selected_song_hist}", height=450)
                    fig_s.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"), hovermode="x unified")
                    fig_s.update_traces(line_color=secondary_color, line_width=3)
                    st.plotly_chart(fig_s, use_container_width=True)
                else: st.info("数据不足")

        if real_career_daily > 0:
            final_songs_df['Share'] = (final_songs_df['Daily_Num'] / real_career_daily * 100).round(2).astype(str) + '%'
        else: final_songs_df['Share'] = "0%"
        sub_df = final_songs_df.head(150)
        fig = px.bar(sub_df.head(10), x='Daily_Num', y='Song', orientation='h', text='Daily_Num', color='Daily_Num', color_continuous_scale=color_map)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"))
        st.plotly_chart(fig, use_container_width=True, key="chart_songs_daily")
        
        disp_cols = ['Song','Daily_Num','Share']
        if 'Change' in sub_df.columns: disp_cols.insert(2, 'Change')
        
        st.dataframe(sub_df[disp_cols], use_container_width=True)

    with tab2:
        st.markdown("#### 💎 单曲总榜")
        avg_7day_map = get_7day_average()
        final_songs_df['Avg_7Days'] = final_songs_df['Song'].map(avg_7day_map).fillna(final_songs_df['Daily_Num'])
        
        def format_milestone_prediction(row):
            curr = row['Streams_Num']
            next_goal = ((curr // 100_000_000) + 1) * 100_000_000
            gap = next_goal - curr
            speed = row['Avg_7Days']
            goal_str = f"{gap:,}"
            if speed > 0:
                days = gap / speed
                if days < 3650: return f"{goal_str} (Need {int(days)} Days)"
            return goal_str

        final_songs_df['Next_Milestone'] = final_songs_df.apply(format_milestone_prediction, axis=1)
        sub_df = final_songs_df.sort_values('Streams_Num', ascending=False).head(150)
        fig = px.bar(sub_df.head(10), x='Streams_Num', y='Song', orientation='h', text='Streams_Num', color='Streams_Num', color_continuous_scale='Turbo')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"))
        st.plotly_chart(fig, use_container_width=True, key="chart_songs_total")
        st.dataframe(sub_df[['Song','Streams_Num','Avg_7Days', 'Next_Milestone']], use_container_width=True, column_config={"Avg_7Days": st.column_config.NumberColumn("7日平均日增", format="%d")})

    if final_albums_df is not None:
        with tab3:
            st.markdown("#### 💿 专辑日增")
            with st.expander("🔎 查询专辑历史走势"):
                all_albs_list = final_albums_df['Base_Name'].unique().tolist()
                selected_alb_hist = st.selectbox("选择专辑:", all_albs_list, index=0)
                if selected_alb_hist:
                    alb_hist_df = get_item_history(selected_alb_hist, is_album=True)
                    if not alb_hist_df.empty:
                        fig_a = px.line(alb_hist_df, x='Date', y='Daily', markers=True, title=f"Trend: {selected_alb_hist}", height=450)
                        fig_a.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"), hovermode="x unified")
                        fig_a.update_traces(line_color=primary_color, line_width=3)
                        st.plotly_chart(fig_a, use_container_width=True)
            
            sub_df = final_albums_df.sort_values('Daily_Num', ascending=False).head(20)
            fig = px.bar(sub_df.head(10), x='Base_Name', y='Daily_Num', text='Daily_Num', color='Base_Name')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"))
            fig.update_traces(texttemplate='%{text:.2s}', textposition='outside') 
            st.plotly_chart(fig, use_container_width=True, key="chart_albums_daily")
            
            disp_cols_alb = ['Base_Name','Daily_Num','Daily_Share']
            if 'Change' in sub_df.columns: disp_cols_alb.insert(2, 'Change')
            st.dataframe(sub_df[disp_cols_alb], use_container_width=True)

        with tab4:
            st.markdown("#### 🏛️ 专辑总榜")
            sub_df = final_albums_df.sort_values('Total_Num', ascending=False).head(20)
            fig = px.bar(sub_df.head(10), x='Base_Name', y='Total_Num', text='Total_Num', color='Base_Name')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman"))
            st.plotly_chart(fig, use_container_width=True, key="chart_albums_total")
            st.dataframe(sub_df[['Base_Name','Total_Num','Total_Share']], use_container_width=True)

    st.divider()
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("##### 📺 Official Pick")
        youtube_videos = ["SXiSVQZLje8", "QYh6mYIJG2Y", "iS1g8G_njx8", "ffxKSjUwKdU", "nlR0MkrRklg", "pE49WK-oNjU", "KNtJGQkC-WI", "B6_iQvaIjXw", "EEhZAHZQyf4", "kHLHSlExFis", "BPgEgaPk62M", "tcYodQoapMg", "gl1aHhXnN1k", "1ekZEVeXwek", "yj1Kvhog6PU", "KwRxeZ9Ro24", "eB6txyhHFG4"]
        random_vid = random.choice(youtube_videos)
        st.video(f"https://youtu.be/{random_vid}")
        st.markdown(f"<div style='text-align:center; margin-top:15px;'><a href='https://www.arianagrande.com/' target='_blank' class='media-btn' style='background:{primary_color}; border:2px solid {secondary_color};'>🌐 Official Website</a> <a href='https://www.instagram.com/arianagrande/' target='_blank' class='media-btn' style='background:linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); margin-left:10px;'>📸 Instagram</a></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("##### 🎧 Spotify Hits (Randomized)")
        hits_pool = {
            "eternal sunshine": ["we can't be friends", "yes, and?", "the boy is mine", "intro (end of the world)"],
            "Positions": ["positions", "34+35", "pov", "motive"],
            "thank u, next": ["7 rings", "thank u, next", "break up with your girlfriend", "needy"],
            "Sweetener": ["no tears left to cry", "god is a woman", "breathin", "R.E.M"],
            "Dangerous Woman": ["Side To Side", "Into You", "Dangerous Woman", "Be Alright"],
            "My Everything": ["One Last Time", "Bang Bang", "Problem", "Break Free"],
            "Yours Truly": ["The Way", "Honeymoon Avenue", "Baby I", "Tattooed Heart"],
            "Yours Truly (Tenth Anniversary Edition)": ["The Way - Live from London", "Tattooed Heart - Live from London"]
        }
        selected_hits = []
        for alb, songs in hits_pool.items():
            song = random.choice(songs)
            selected_hits.append((song, alb))
        st.markdown(f'<div style="text-align:center; margin-bottom:10px;"><a href="https://open.spotify.com/artist/66CXWjxzNUsdJxJ2JdwvnR" target="_blank" class="media-btn" style="background:#1DB954;">🟢 Spotify Profile</a></div>', unsafe_allow_html=True)
        for song, alb in selected_hits[:6]:
             st.markdown(get_spotify_card_html(f"💿 {alb}", song, "Stream Now"), unsafe_allow_html=True)

    st.divider()
    if os.path.exists("ARIANAlogo.png"):
        logo_b64 = get_image_base64("ARIANAlogo.png")
        if logo_b64:
            st.markdown(f"<div style='display: flex; justify-content: center; margin: 30px 0;'><div style='background: {primary_color}; padding: 20px 40px; border-radius: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 3px solid {secondary_color};'><img src='data:image/png;base64,{logo_b64}' style='max-width: 250px; width: 100%; display: block; border: none; border-radius: 0; margin: 0;'></div></div>", unsafe_allow_html=True)

    st.markdown(f'<div class="footer"><b>✨ 制作: 小羊生煎 With Gemini ✨</b><br><div class="footer-links">A.K.A 唐可可的小炸弹（贴吧，B站同名）/ TangKeke可可日记<br>邮箱: sheepYeoh@outlook.com | ig: @sampoohh</div></div>', unsafe_allow_html=True)

else:
    st.info("👋 欢迎！请在 GitHub 仓库的 'daily_data' 文件夹中上传 *_songs.csv 和 *_meta.json 文件以开始显示数据。")
