import pandas as pd
import streamlit as st
from func import fetch_data, auto_refresh, piebytab, barbytab,\
                 piebydept, barbydept, detailbysku, filterfield

    # Streamlit UI
st.set_page_config(page_title="Missing Values", layout="wide")
st.toast("Auto-refresh enabled. Data updates every setting seconds.", icon="🔄")
placeholder = st.empty() # Create a placeholder for real-time updates

while True:
    picdept = fetch_data('dept')

    datasku = fetch_data('propost')
    datasku = datasku[~datasku['SKU'].isna()]
    
    dataskusup = fetch_data('provenpost')
    dataskusup = dataskusup[dataskusup['SKU'].notna() & (dataskusup['SKU_SupCode'] != "_")]

        # PRODUCT MASTER ==============================================================================================
    mancol = ['SKU', 'PIC', 'Idea Code', 'Product Name', 'Product Net Weight - Drawing (kg)',
              'No# of IB - Drawing', 'IB Length - Drawing (cm)', 'IB Width - Drawing (cm)',
              'IB Height - Drawing (cm)', 'IB Gross Weight - Drawing (kg)', 'Base Unit of Measure', 
              'Company', 'Knock-down', 'Assembly instruction', 'Techpack (Technical Pakage)', 
              'Selling Type', 'Brand', 'REACH Result', 'Prop 65 Result', 'Valuation class']
    
    mandf = datasku.set_index('SKU', drop=False)[mancol].merge(picdept[['PIC', 'dept']], on='PIC', how='left')
    mask = (mandf[['PIC', 'Idea Code', 'Product Name', 'Base Unit of Measure', 'Company', 'Knock-down',
               'Techpack (Technical Pakage)', 'Selling Type', 'Brand', 'REACH Result',
               'Prop 65 Result', 'Valuation class']].isna().any(axis=1) |
        ((mandf['Knock-down'] == 'Yes') & mandf['Assembly instruction'].isna()) |
        ((mandf['Selling Type'] != 'Combo') & mandf[['Product Net Weight - Drawing (kg)',
                                                     'No# of IB - Drawing', 'IB Length - Drawing (cm)',
                                                     'IB Width - Drawing (cm)', 'IB Height - Drawing (cm)',
                                                     'IB Gross Weight - Drawing (kg)']].isna().any(axis=1)))
        # PRODUCT DATA BY VENDOR ======================================================================================
    mancolven = ['PIC', 'SKU','Supplier Code', 'Product Name', 'SKU_SupCode', 'MOQ', 'FOB Price',\
               'Port FOB', 'Production leadtime 1st Order', 'Production leadtime', \
               'Product Net Weight - Production (kg)', 'No# of IB - Production', 'IB Length - Production (cm)', 'IB Width - Production (cm)', 'IB Height - Production (cm)',\
               'IB Net Weight - Production (kg)', 'IB Gross Weight - Production (kg)', 'No# of MB - Production', 'MB Length- Production (cm)', 'MB Width - Production (cm)',\
               'MB Height - Production (cm)', 'MB Net Weight - Production (kg)', 'MB Gross Weight - Production (kg)', 'SOR Result', 'Purchasing status', 'Duty (%)', 'HTS Code']
    
    mandfven = dataskusup.set_index('SKU_SupCode', drop=False)[mancolven].merge(picdept[['PIC','dept']], on='PIC', how='left')
    
    mandfvenfilterfield = mandfven.copy()
    mandfvenfilterfield['dept'] = mandfvenfilterfield['dept'].astype(str) + 'ven'
    
    # COOK DATA =======================================================================================================
    out_df = mandf[mask]
    out_df['NaN_Count'] = out_df.isna().sum(axis=1)
    out_df = out_df.sort_values(by='NaN_Count', ascending=True).drop(columns='NaN_Count')
    out_df.set_index('SKU', inplace=True)
    
    out_dfven = mandfven[mandfven.isna().any(axis=1)]
    out_dfven['NaN_Count'] = out_dfven.isna().sum(axis=1)
    out_dfven = out_dfven.sort_values(by='NaN_Count', ascending=True).drop(columns='NaN_Count')
    out_dfven.set_index('SKU_SupCode', inplace=True)
    
        # PRODUCT MASTER ==============================================================================================
    # Stacked Bar - Missing value by team:
    missbyteam = mandf[mask]
    missbyteam = missbyteam.groupby("dept")[list(missbyteam.columns)].apply(lambda x: x.isna().sum()).T
    
    # Separatedly work on the AI:
    aicheck = mandf[['Knock-down', 'Assembly instruction', 'dept']]
    aicheck = aicheck[(aicheck['Knock-down'] == 'Yes') & aicheck['Assembly instruction'].isna()]
    aicheck = aicheck.groupby("dept").apply(lambda x: x.isna().sum()).T
    missbyteam.loc['Assembly instruction'] = aicheck.loc['Assembly instruction'] # Replace AI count by separated outcome value.
    missbyteam = missbyteam.fillna(0)
    
    # Pie Chart - Complete rate by department:
    dept_df = pd.DataFrame({'Affect by Dept': out_df['dept'].value_counts(),
                            'Total by Dept': mandf['dept'].value_counts()}).T
    dept_df.loc['Complete by Dept'] = dept_df.loc['Total by Dept'] - dept_df.loc['Affect by Dept']
    
        # PRODUCT DATA BY VENDOR ======================================================================================
    # Stacked Bar - Missing value by team:
    missbyteamven = mandfven[mandfven.isna().any(axis=1)]
    missbyteamven = missbyteamven.groupby("dept")[list(missbyteamven.columns)].apply(lambda x: x.isna().sum()).T
    
    # Pie Chart - Complete rate by department:
    dept_dfven = pd.DataFrame({'Affect by Dept': out_dfven['dept'].value_counts(),
                               'Total by Dept': mandfven['dept'].value_counts()}).T
    dept_dfven.loc['Complete by Dept'] = dept_dfven.loc['Total by Dept'] - dept_dfven.loc['Affect by Dept']    
    
    # DASHBOARDING ====================================================================================================
    st.markdown("""<style>div[data-testid="stTabs"] {margin-top: -60px;}</style>""", unsafe_allow_html=True)
    # =================================================================================================================
    pro_tab, proven_tab = st.tabs(["Product Master Data", "Product by Supplier"])
    with pro_tab: # Product Master Data ===================================
        st.markdown("<h1 style='font-size: 20px;'>Overview</h1>", unsafe_allow_html=True)

        col1, col2 = st.columns([1,1])
        with col1:
            subcol1, subcol2 = st.columns([1,1])
            with subcol1:
                piebytab(mandf, 'Total SKU by Team')            
            with subcol2:                
                piebytab(mandf[mask], 'Total Missing SKU by Team')
            barbytab(missbyteam)
        with col2:
            st.markdown("""<style>div.stTabs:nth-of-type(2) div[role="tablist"]
                {margin-top: -14px;}</style>""",unsafe_allow_html=True)

            sub_tab1, sub_tab2 = st.tabs(["SSO", "SFO"])
            with sub_tab1: #SSO
                col1, col2 = st.columns(2)
                with col1:
                    piebydept('SSO', dept_df)
                with col2:
                    barbydept('SSO', out_df)            
                filterfield('SSO', mandf, mask, 'SKU')
                detailbysku('SSO', mandf[mask])
            with sub_tab2: #SFO
                col1, col2 = st.columns(2)
                with col1:
                    piebydept('SFO', dept_df)       
                with col2:
                    barbydept('SFO', out_df)
                filterfield('SFO', mandf, mask, 'SKU')
                detailbysku('SFO', mandf[mask])                
    
    with proven_tab: # Product Data by Vendor =============================
        st.markdown("<h1 style='font-size: 20px;'>Overview</h1>", unsafe_allow_html=True)

        col3, col4 = st.columns([1,1])
        with col3:
            subcol3, subcol4 = st.columns([1,1])
            with subcol3:                
                piebytab(mandfven, 'Total SKU by Team')            
            with subcol4:                
                piebytab(mandfven[mandfven.isna().any(axis=1)], 'Total Missing SKU by Team')    
            barbytab(missbyteamven)                
        with col4:            
            sub_tab1, sub_tab2 = st.tabs(["SSO", "SFO"])    
            with sub_tab1: #SSO
                col1, col2 = st.columns(2)
                with col1:
                    piebydept('SSO', dept_dfven)
                with col2:
                    barbydept('SSO', out_dfven)
                filterfield('SSOven', mandfvenfilterfield, mandfvenfilterfield.isna().any(axis=1), 'SKU_SupCode')
                detailbysku('SSO', mandfven[mandfven.isna().any(axis=1)])        
            with sub_tab2: #SFO
                col1, col2 = st.columns(2)
                with col1:
                    piebydept('SFO', dept_dfven)
                with col2:
                    barbydept('SFO', out_dfven)
                filterfield('SFOven', mandfvenfilterfield, mandfvenfilterfield.isna().any(axis=1), 'SKU_SupCode')
                detailbysku('SFO', mandfven[mandfven.isna().any(axis=1)])
 
    # Auto-refresh every setting seconds =======================================
    auto_refresh(3)