import pandas as pd
import streamlit as st
import time
import plotly.express as px
import plotly.graph_objects as go


        # FETCHING DATA FROM GOOGLE SHEETS: ===================================
@st.cache_data(ttl=3)
def fetch_data(sheet):
    sheet_id = "1S67a7BLqIFwyLZMR734Xh7iMHiWURUzvXfS4KlkQEVk"
    sheets = sheet
    timestamp = int(time.time())  # Force Google Sheets refresh
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheets}&t={timestamp}"    
    return pd.read_csv(sheet_url)

        # AUTO REFRESHING DATA: ===============================================
def auto_refresh(interval=3):
    time.sleep(interval)
    st.rerun()
    
        # VISUALIZATION: ======================================================
# 1. Col 1, sub- Col 1 and sub- Col 2 Total SKU + Total Missing SKU by SSO/ SFO:
def piebytab(piebytabdf, title):
    teamse = piebytabdf['dept'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=teamse.index,  # dept names
        values=teamse.values,  # counts
        hole=0.5,  # Donut-style
        textinfo='value',
        textfont_size=30,
        domain={'x': [0, 1], 'y': [0, 1]})])
    
    fig.update_layout(
        title_text=title,
        height=600,
        width=600,
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=60, r=60, t=60, b=60),
        annotations=[dict(text=f"{len(piebytabdf.index)}", 
                          x=0.5, y=0.5, 
                          font=dict(size=70, color="grey"), showarrow=False)])
    
    # fig.update_traces(textinfo='value')
    
    st.plotly_chart(fig)
    
# 2. Col 1, Total Missing SKU by Field by SSO/ SFO:
def barbytab(barbytabdf):
    
    barbytabdf = barbytabdf.reset_index()
    barbytabdf['Total'] = barbytabdf['SSO'] + barbytabdf['SFO']
    barbytabdf = barbytabdf[barbytabdf['Total'] > 0] # Filter missbyteam rows where both 'SSO' and 'SFO' are zero
    barbytabdf = barbytabdf.sort_values(by='Total', ascending=True) # Sort by 'Total' in descending order
    
    if not barbytabdf.empty:                
        fig = px.bar(barbytabdf, y='index', x=['SSO', 'SFO'],
        text_auto=True, barmode='stack', height=1030, labels={"index": "", "value": ""})
        
        fig.update_layout(
        title_text='Missing Field Break- down by Team',
        height=800,
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=0, r=0, t=60, b=0),  # Reduce margins
        xaxis=dict(
            automargin=True, 
            fixedrange=True, 
            zeroline=False,
            showgrid=False),
        yaxis=dict(
            automargin=True, 
            showgrid=False,
            categoryorder="total ascending"),
        uniformtext_minsize=8, uniformtext_mode="hide")                    
        
        st.plotly_chart(fig)

# Function to draw pie chart of each department (Number of Sufficient vs Missing SKU):
def piebydept(dept, piebydeptdf):
    
    custom_colors = ['#e62023', '#1abd3b']
    
    fig = go.Figure(data=[go.Pie(
        labels=piebydeptdf[dept].drop('Total by Dept').index,  # dept names
        values=piebydeptdf[dept].drop('Total by Dept').values,  # counts
        hole=0.5,  # Donut-style
        textinfo='value',
        textfont_size=30,
        domain={'x': [0, 1], 'y': [0, 1]},
        marker=dict(colors=custom_colors))])
    
    fig.update_layout(
        title = 'Sufficient/ Missing SKU Break- down',
        height=600,
        width=600,
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=60, r=60, t=60, b=60),
        annotations=[dict(text=f"{piebydeptdf[dept]['Total by Dept']}", 
                          x=0.5, y=0.5, 
                          font=dict(size=70, color="grey"), showarrow=False)])
    st.plotly_chart(fig)

# Function to draw bar chart of each department (Number of Missing of Each field):
def barbydept(dept, barbydeptdf):
    missbyfield = barbydeptdf[barbydeptdf['dept'] == dept].isna().sum()
    missbyfield = missbyfield.to_frame(name=dept)
    missbyfield = missbyfield[missbyfield[dept] > 0].reset_index()
    missbyfield = missbyfield.sort_values(by=dept, ascending=True)
    
    fig = px.bar(missbyfield, y='index', x=dept,
    text_auto=True, height=650, width=500, labels={"index": "", "value": ""})    
    
    fig.update_traces(
    textfont_size=12,
    textposition="outside",  # Show text labels above bars
    marker=dict(
        color='#fff900',
        line=dict(width=1, color="#e62003"),  # Add border
        opacity=0.9,  # Slight transparency
        cornerradius=60),)
    fig.update_layout(xaxis=dict(range=[0, max(missbyfield[dept]) * 1.5]))  # Adjust margins as needed

    # width=0.1 if len(missbyfield) == 1 else None)
    st.plotly_chart(fig, use_container_width=True)

# Function to display dataframe of each department (group SKU by the same group of Missing Field)
def detailbysku(dept, detailbyskudf):
    # Data- prep:
    detailbyskudf.set_index('SKU', inplace=True)
    missing_patterns = detailbyskudf[detailbyskudf['dept'] == dept].isna().apply(lambda row: tuple(row[row].index), axis=1)
    grouped_skus = missing_patterns.groupby(missing_patterns).apply(lambda x: list(x.index)).to_dict()
    output_df = pd.DataFrame(
        [(', '.join(missing_cols), ', '.join(skus)) for missing_cols, skus in grouped_skus.items()],
        columns=["Missing Columns", "SKUs"])
    output_df["Missing Count"] = output_df["Missing Columns"].apply(lambda x: len(x.split(", ")) if x else 0)    
    output_df = output_df.sort_values(by="Missing Count", ascending=False).drop(columns=["Missing Count"])
    output_df.reset_index(drop=True, inplace=True)    
    # missing_col_options = sorted(output_df["Missing Columns"].unique(), key=lambda x: len(x.split(", ")) if x else 0, reverse=True)
    
    with st.expander("Group of Missing"):
        st.dataframe(output_df, use_container_width = True)

# Function to display dataframe of each department (group SKU by Missing Field and PIC)
def filterfield(dept, filferfielddf, filferfieldmask, key):
    outfildf = filferfielddf[filferfieldmask]
    selected_list = outfildf[outfildf['dept'] == dept].columns[outfildf.isna().any()].tolist()
    selected_column = st.selectbox("Select a column", selected_list, key=f"select_{dept}")
    filtered_df = outfildf[outfildf['dept'] == dept][['PIC', key, selected_column]]                     
    filtered_df[selected_column] = filtered_df[selected_column].isna()
    filtered_df = filtered_df[filtered_df[selected_column]]

    # Group by PIC and count blank SKUs and total SKUs
    summary_df = filtered_df.groupby("PIC").agg(
        blank_SKU=(key, "count"),
        SKU=(key, lambda x: ", ".join(x))
    ).reset_index()
    summary_df = summary_df.sort_values(by='blank_SKU', ascending=False)
    st.write("Summary of Blank Values in", selected_column)
    st.dataframe(summary_df, use_container_width = True)
    
# MIGHT NEED LATER ============================================================
#     # Pull 4 dataframe from GGS (pre: static, post:dynamic):
# for sheet_name in ['propre', 'provenpre', 'propost', 'provenpost']:
#     globals()[sheet_name] = pd.read_csv("https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".
#                                         format("1S67a7BLqIFwyLZMR734Xh7iMHiWURUzvXfS4KlkQEVk", sheet_name))

#     # Fix struture (post Has 'PIC' and 10 Categories):
# inpostnotinpre = set(propost.columns) - set(propre.columns)
# propost = propost[[col for col in propost.columns if col not in list(inpostnotinpre)]]
# del inpostnotinpre, sheet_name

#     # These 2 were in pre file but data insufficient
# propre = propre[~propre['SKU'].isin(['LMHR', 'LRTZ'])]

#     # Concatenate 2 Dataframe and Set 'SKU' as index:
# promaster = pd.concat([propre, propost])
# promaster.set_index('SKU', inplace=True, drop=False)
    
#     # File from PIMS: 
# pim = pd.read_excel(r"C:\Users\quannhm\Desktop\pim.xlsx",sheet_name='Basic Information')
# mkp = pd.read_excel(r"C:\Users\quannhm\Desktop\pim.xlsx", sheet_name='Marketplace')
#     # Sheet 'Basic Information':
#     # - Row index 0: Export Date
#     # - Row index 1: Columns Headline (WHAT WE NEED !)
#     # - Row index 2: All nan
#     # Data start from Row index 3 => Set col Name by index 1, then drop index [0:2]

# pim.columns = pim.iloc[1,:]
# pim.drop(index=range(3), inplace=True)
# pim.reset_index(inplace=True, drop=True)

#     # 1. MEMBERSHIP CHECKING:
        
# infilenotinpim = set(promaster['SKU']) - set(pim['SKU'])
# inpimnotinfile = set(pim['SKU']) - set(promaster['SKU'])
# selltypecheck = pim[pim['SKU'].isin(list(inpimnotinfile))][['SKU', 'Selling Type']]

#     # Verification:
#     # - Step 1: Remove all 'Replacement', 'Not sales' Selling Type
#     # - Step 2: Check 'Status' and 'Listing status' of remainders
# check_SKU = pim[pim['SKU'].isin(list(inpimnotinfile)) & 
#                 ~pim['Selling Type'].isin(['Replacement', 'Not sales'])][['SKU', 'Selling Type']]
# inpimnotinfile_df = mkp[mkp['SKU'].isin(list(check_SKU['SKU']))]