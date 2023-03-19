import streamlit as st
import pandas as pd
from urllib.request import urlopen
import json
from flatten_json import flatten
from apiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import markdownify

#Layout
st.set_page_config(
    page_title="BWCA Lake Search",
    page_icon='water',
    layout="wide",
    initial_sidebar_state="expanded",
)

#Create Menu
with st.sidebar:
    selected = option_menu("BWCA Lake Search", ["About", 'Lake Search','Big Fish Index','Gallery'], 
        icons=['info-circle','search','calculator','camera'],menu_icon="tree-fill", default_index=0)
  
#read data
@st.cache_data
def pull_fss():
    fss=pd.read_csv('FishSurveySum.csv')
    return fss
fss=pull_fss()

@st.cache_data
def pull_clean_lm():
    lm = pd.read_csv('CountyLakeMapping.csv',dtype=str)
    lm.rename(columns={'Name': 'lake'}, inplace=True)
    return lm
lm=pull_clean_lm()
 
@st.cache_data
def pull_clean_lakeagg():
    lakeagg=pd.read_csv('lakeagg.csv')
    lakeagg['LakeID']=lakeagg['LakeID'].astype(str)
    return lakeagg
lakeagg=pull_clean_lakeagg()

@st.cache_data
def pull_clean_camps():
    camps=pd.read_csv('campsites.csv')
    camps.rename(columns={'Y': 'lat', 'X': 'lon', 'name': 'info'}, inplace=True)
    camps['Legend']='Campsite'
    camps[['test1','lake','test3','test4','test5','test6','test7','test8']] = camps['desc'].str.split('-', expand = True)
    camps['lake']=camps['lake'].str.replace('Lake','')
    camps['lake']=camps['lake'].str.strip()
    camps_lo=camps[['lake']].drop_duplicates()
    return camps, camps_lo
camps,camps_lo=pull_clean_camps()

    
@st.cache_data
def pull_clean_ports():
    ports1=pd.read_csv('portage_points.csv')
    ports2=pd.read_csv('portage_tracks.csv')
    ports1.rename(columns={'Y': 'lat', 'X': 'lon'}, inplace=True)
    ports2.rename(columns={'Y': 'lat', 'X': 'lon'}, inplace=True)
    ports2[['b1','b2','b3','Rods','RodsVal','b6','b7']]=ports2['desc'].str.split(expand = True)
    ports2['info']=ports2['Rods']+ports2['RodsVal']
    ports2=ports2[['lat','lon','info']]
    ports1=pd.merge(ports1,ports2[['lat','lon','info']], on=['lat','lon'], how='left')
    ports3=pd.concat([ports1, ports2], ignore_index=True, sort=False)
    ports3['Legend']='Portage'
    return ports3
ports3=pull_clean_ports()

@st.cache_data
def merge():
    lm_reduce = pd.merge(lm,camps_lo, on='lake') 
    camps_ports=pd.concat([camps, ports3], ignore_index=True, sort=False)
    return lm_reduce, camps_ports
lm_reduce,camps_ports=merge()

if selected=="About":
    st.header('About the BWCA')
    st.write('Established in 1964 as Federally Designated Wilderness, the Boundary Waters Canoe Area Wilderness is over one million acres of rugged and remote boreal forest in the northern third of the Superior National Forest in northeastern Minnesota.')
    st.write("The BWCAW extends nearly 150 miles along the International Boundary, adjacent to Canada's Quetico and La Verendrye Provincial Parks, is bordered on the west by Voyageurs National Park, and by Grand Portage National Monument to the east. The BWCAW contains over 1,200 miles of canoe routes, 12 hiking trails and over 2,000 designated campsites. The BWCAW is composed of lakes, islands, rocky outcrops and forest.")
    st.write("_U.S. Forest Service_ [Learn More](https://www.fs.usda.gov/recarea/superior/recarea/?recid=84168)")
    st.image('vidimage/bwcamap.png',caption='Credit: Canoeing.com LTD')

    st.header('About this Tool')
    st.subheader('Purpose')
    st.write('This application is designed for BWCA trip planning as a personal use tool.  The app brings together various BWCA data sources into one location, and creates new metrics and data visualizations from these data sources.')
    st.subheader('Data')
    with st.container():
        col1,col2=st.columns(2)
        col1.image('vidimage/bwca-logo.png')
        col2.write('Campsite and portage waypoints are from publicly available GPX files by BWCA.com and are for personal use only (not to be used commercially or redistributed).')
    with st.container():
        col1,col2=st.columns(2)
        col1.image('vidimage/mndnr.jpeg')
        col2.write('Lake data including Fisheries Surveys are from publicly available JSON strings from URL of the LakeFinder tool from the Minnesota Department of Natural Resources.')
    
    st.header('Functionality')
    with st.expander('Lake Search'):
        st.write('**(1)**     Enter a Lake Name')
        st.write('**(2)**     Interactive map auto centered to lake selection, topographic and satellite layers, markers/colors for campsites and portages, hover data shows campsite number and portage distance)')
        st.write('**(3)**     Fishery Lake Survey data shown which includes: Lake Characteristics, Fish Size Distribution, and Status of the Fishery')
        st.write('**(4)**     Top three search results from YouTube for the prompt "<selected lake> BWCA"')
    with st.expander('Lake Stats'):
        st.write('**(1)**     Not sure yet')
    with st.expander('Big Fish Index'):
        st.write('**(1)**     Optional filter on County within BWCA')
        st.write('**(2)**     List of lakes within county selection, sorted by BFI (high to low), with tab options for different species, and a download to CSV button')
        st.write('**(3)**     3-D scatter plot that shows lakes with non missing BFI values for Walleye, Northern Pike, and Smallmouth Bass, hover data contains lake name and BFI values')

if selected=="Lake Search":
 
    st.header('Search for a Lake')
    lake_select = st.selectbox('Select Lake',list(lm_reduce['lake'].unique()),index=127)
    if lake_select:
        st.header(lake_select)
        lakeid=lm_reduce[lm_reduce['lake']==lake_select].reset_index()
        numlakes=0
        if len(lakeid.index)>1:
            numlakes=len(lakeid)
            st.write('There are multiple with that name! Pick the nearest town')
            town_select=st.selectbox('Select Town',list(lakeid['Nearest Town'].unique()),index=0)
            lakeid=lakeid[lakeid['Nearest Town']==town_select].reset_index()
        lakeidval=lakeid.loc[0]['ID']
        lakeaggshort=lakeagg[lakeagg['LakeID']==lakeidval].reset_index()
        camps_small=camps[camps['lake']==lake_select]
        numsites=str(camps_small.shape[0])
        latcenter=camps_small['lat'].mean()
        loncenter=camps_small['lon'].mean()

        #map token for additional map layers
        token = "pk.eyJ1Ijoia3NvZGVyaG9sbTIyIiwiYSI6ImNsZjI2djJkOTBmazU0NHBqdzBvdjR2dzYifQ.9GkSN9FUYa86xldpQvCvxA" # you will need your own token
        #first map shows terrain
        fig1 = px.scatter_mapbox(camps_ports, lat='lat',lon='lon',center=go.layout.mapbox.Center(lat=latcenter,lon=loncenter),
                                zoom=12,color='Legend',color_discrete_sequence=['red','yellow'],hover_name='Legend',
                                hover_data={'lat':False,'lon':False,'Legend':False,'info':True})
        fig1.update_layout(mapbox_style="mapbox://styles/mapbox/outdoors-v11",mapbox_accesstoken=token)
        fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        #second map shows satellite view
        fig2 = px.scatter_mapbox(camps_ports, lat='lat',lon='lon',center=go.layout.mapbox.Center(lat=latcenter,lon=loncenter),
                                zoom=12,color='Legend',color_discrete_sequence=['red','yellow'],hover_name='Legend',
                                hover_data={'lat':False,'lon':False,'Legend':False,'info':True})
        fig2.update_layout(mapbox_style="mapbox://styles/mapbox/satellite-streets-v12",mapbox_accesstoken=token)
        fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        tab1,tab2=st.tabs(['Terrain','Satellite'])
        #show maps in tabs
        with tab1:
            tab1.plotly_chart(fig1,use_container_width=True)
        with tab2:
            tab2.plotly_chart(fig2,use_container_width=True)
        if numlakes>0:
            st.write(lake_select+' has unknwown number of campsites')
        else:
            st.write(lake_select+' has '+numsites+' campsites')

        #Function for parsing JSON Fish data
        def fishdata(acr):
            path='result_surveys_'+maxsurvey+'_lengths_'+acr+'_fishCount_'
            cols=[col for col in djc.columns if col.startswith(path)]
            data=djc[cols]
            lencols=[col for col in cols if col.endswith('0')]
            dj1=[]
            dj2=[]
            cols2=[]
            for i in range(0,len(lencols)):
                dj1.append(data[path+'{}'.format(i)+'_0'][0])
                cols2.append(acr+'Len_'+'{}'.format(dj1[i]))
                dj2.append(data[path+'{}'.format(i)+'_1'][0])
            df=pd.DataFrame([dj2],columns=cols2)
            return df
        #Retrieve data from URL in JSON format
        url="https://maps2.dnr.state.mn.us/cgi-bin/lakefinder/detail.cgi?type=lake_survey&id="+lakeidval
        response=urlopen(url)
        dja=json.loads(response.read())

        #flatten JSON and put in DataFrame
        djb=flatten(dja)
        djc=pd.json_normalize(djb).reset_index()
        djc=djc.astype(str)
        #if djc['status'][0]=='ERROR':
        
        #Identify the different surveys
        datecols=[col for col in djc.columns if 'surveyDate' in col]
        idcols=['result_DOWNumber','result_lakeName']
        numsurveys = len(datecols)

        #Extract survey years
        for y in range(0,numsurveys):
            djc['year'+'{}'.format(y)]=djc['result_surveys_'+'{}'.format(y)+'_surveyDate'].str.slice(0,4)
        yearcols=[col for col in djc.columns if 'year' in col]
        djyear=djc[yearcols]
        djyear[yearcols].astype(int)

        #Identify max (most recent survey year)
        for z in range(0,numsurveys):
            djyear['year'+'{}'.format(z)]=pd.to_numeric(djyear['year'+'{}'.format(z)])
        maxsurvey=djyear[yearcols].idxmax(axis=1)
        maxsurvey=maxsurvey[0]
        maxsurvey=maxsurvey[4:]

        SMB=fishdata('SMB')
        SMB = SMB.loc[:,~SMB.columns.duplicated()] 
        NOP=fishdata('NOP')
        NOP = NOP.loc[:,~NOP.columns.duplicated()] 
        WAE=fishdata('WAE')
        WAE = WAE.loc[:,~WAE.columns.duplicated()] 
        LAT=fishdata('LAT')
        LAT = LAT.loc[:,~LAT.columns.duplicated()] 

        
        fg=pd.DataFrame({'Length': [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46]})
        fg['SMBcnt']=''
        fg['NOPcnt']=''
        fg['WAEcnt']=''
        fg['LATcnt']=''
        fg['SMBpct']=''
        fg['NOPpct']=''
        fg['WAEpct']=''
        fg['LATpct']=''
        fgcols = fg.columns
        fg[fgcols] = fg[fgcols].apply(pd.to_numeric, errors='coerce')
        for a in range(0,46):
            if 'SMBLen_'+'{}'.format(a) in SMB.columns:
                fg['SMBcnt'][a]=pd.to_numeric(SMB['SMBLen_'+'{}'.format(a)][0])
        for b in range(0,46):
            if 'NOPLen_'+'{}'.format(b) in NOP.columns:
                fg['NOPcnt'][b]=pd.to_numeric(NOP['NOPLen_'+'{}'.format(b)][0])
        for c in range(0,46):
            if 'LATLen_'+'{}'.format(c) in LAT.columns:
                fg['LATcnt'][c]=pd.to_numeric(LAT['LATLen_'+'{}'.format(c)][0])
        for d in range(0,46):
            if 'WAELen_'+'{}'.format(d) in WAE.columns:
                fg['WAEcnt'][d]=pd.to_numeric(WAE['WAELen_'+'{}'.format(d)][0])
        for e in range(0,46): 
            fg['SMBpct'][e]=fg['SMBcnt'][e]/fg['SMBcnt'].sum()
            fg['NOPpct'][e]=fg['NOPcnt'][e]/fg['NOPcnt'].sum()
            fg['LATpct'][e]=fg['LATcnt'][e]/fg['LATcnt'].sum()
            fg['WAEpct'][e]=fg['WAEcnt'][e]/fg['WAEcnt'].sum()

        #Survey info to display fro most recent survey
        FishStat=djc.loc[0]['result_surveys_'+maxsurvey+'_narrative']
        SurveyDate=djc.loc[0]['result_surveys_'+maxsurvey+'_surveyDate']
        #Lake characteristics
        Area=djc.loc[0]['result_areaAcres']
        LitArea=djc.loc[0]['result_littoralAcres']
        ShoreLength=djc.loc[0]['result_shoreLengthMiles']
        MeanDepth=djc.loc[0]['result_meanDepthFeet']
        MaxDepth=djc.loc[0]['result_maxDepthFeet']
        AvgClar=djc.loc[0]['result_averageWaterClarity']
        #Format Lake Characteristics for Display
        Area2='Area:    '+Area+' acres'
        LitArea2='Littoral Area:    '+LitArea+' acres'
        ShoreLength2='Shore Length:    '+ShoreLength+' miles'
        MeanDepth2='Mean Depth:    '+MeanDepth+' ft'
        MaxDepth2='Maximum Depth:    '+MaxDepth+' ft'
        AvgClar2='Average Water Clarity:    '+AvgClar+' ft'
        SurveyDate2='Date of Most Recent Survey:    '+SurveyDate

        #Display data from fishery survey
        st.header('Lake Characteristics')
        col1,col2=st.columns(2)
        col1.write(Area2)
        col1.write(LitArea2)
        col1.write(ShoreLength2)
        col2.write(MeanDepth2)
        col2.write(MaxDepth2)
        col2.write(AvgClar2)
        st.header('Fish Size Distribution')

        #Format aggregated data
        lakeaggshort['BFI_NOP'] = lakeaggshort['BFI_NOP'].map('{:,.2f}'.format)
        lakeaggshort['BFI_LAT'] = lakeaggshort['BFI_LAT'].map('{:,.2f}'.format)
        lakeaggshort['BFI_SMB'] = lakeaggshort['BFI_SMB'].map('{:,.2f}'.format)
        lakeaggshort['BFI_WAE'] = lakeaggshort['BFI_WAE'].map('{:,.2f}'.format)
        lakeaggshort['BFI_NOP_Pct_Raw'] = lakeaggshort['BFI_NOP_Pct']
        lakeaggshort['BFI_LAT_Pct_Raw'] = lakeaggshort['BFI_LAT_Pct']
        lakeaggshort['BFI_SMB_Pct_Raw'] = lakeaggshort['BFI_SMB_Pct']
        lakeaggshort['BFI_WAE_Pct_Raw'] = lakeaggshort['BFI_WAE_Pct']
        lakeaggshort['BFI_NOP_Pct'] = lakeaggshort['BFI_NOP_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_LAT_Pct'] = lakeaggshort['BFI_LAT_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_SMB_Pct'] = lakeaggshort['BFI_SMB_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_WAE_Pct'] = lakeaggshort['BFI_WAE_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)

        if not lakeaggshort.empty:
            BFI_NOP=lakeaggshort.loc[0]['BFI_NOP']
            BFI_NOP_PCT=lakeaggshort.loc[0]['BFI_NOP_Pct']
            BFI_NOP_PCT_RAW=lakeaggshort.loc[0]['BFI_NOP_Pct_Raw']
            BFI_LAT=lakeaggshort.loc[0]['BFI_LAT']
            BFI_LAT_PCT=lakeaggshort.loc[0]['BFI_LAT_Pct']
            BFI_LAT_PCT_RAW=lakeaggshort.loc[0]['BFI_LAT_Pct_Raw']
            BFI_SMB=lakeaggshort.loc[0]['BFI_SMB']
            BFI_SMB_PCT=lakeaggshort.loc[0]['BFI_SMB_Pct']
            BFI_SMB_PCT_RAW=lakeaggshort.loc[0]['BFI_SMB_Pct_Raw']
            BFI_WAE=lakeaggshort.loc[0]['BFI_WAE']
            BFI_WAE_PCT=lakeaggshort.loc[0]['BFI_WAE_Pct']
            BFI_WAE_PCT_RAW=lakeaggshort.loc[0]['BFI_WAE_Pct_Raw']
    

            tab1,tab2,tab3,tab4,tab5=st.tabs(['Radar','Walleye','Northern Pike','Lake Trout','Smallmouth Bass'])
            with tab1:
                def cat(col,BFI_PCT):
                    if BFI_PCT<=0.2:
                        col.progress(BFI_PCT, text=None)
                        col.write(':red[**REALLY BAD**]')
                    if 0.2<BFI_PCT<=0.4:
                        col.progress(BFI_PCT, text=None)
                        col.write(':red[**BAD**]')
                    if 0.4<BFI_PCT<=0.6:
                        col.progress(BFI_PCT, text=None)
                        col.write(':blue[**OK**]')
                    if 0.6<BFI_PCT<=0.8:
                        col.progress(BFI_PCT, text=None)
                        col.write(':green[**GOOD**]')
                    if 0.8<BFI_PCT<=0.95:
                        col.progress(BFI_PCT, text=None)
                        col.write(':green[**REALLY GOOD**]')
                    if 0.95<BFI_PCT<=1:
                        col.progress(BFI_PCT, text=None)
                        col.write(':green[**PHENOMENAL**]')
                df = pd.DataFrame(dict(r=[BFI_WAE_PCT_RAW,BFI_NOP_PCT_RAW,BFI_LAT_PCT_RAW,BFI_SMB_PCT_RAW],theta=['WALLEYE','NORTHERN PIKE','LAKE TROUT','SMALLMOUTH BASS']))
                fig = px.line_polar(df, r='r', theta='theta', line_close=True)
                fig.update_traces(fill='toself')
                tab1.plotly_chart(fig,use_container_width=True)
                col1,col2,col3,col4=st.columns(4)
                col1.metric('**Walleye Percentile**',BFI_WAE_PCT)
                cat(col1,float(BFI_WAE_PCT_RAW))
                col2.metric('**Northern Pike Percentile**',BFI_NOP_PCT)
                cat(col2,float(BFI_NOP_PCT_RAW))
                col3.metric('**Lake Trout Percentile**',BFI_LAT_PCT)
                cat(col3,float(BFI_LAT_PCT_RAW))
                col4.metric('**Smallmouth Bass Percentile**',BFI_SMB_PCT)
                cat(col4,float(BFI_SMB_PCT_RAW))
            with tab2:
                fig = px.line(x=fss['Length'], y=fss['WAEpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['WAEpct'], marker_color='red',name=lake_select)
                fig.update_xaxes(range=[0, 32])
                tab2.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab1.columns(5)
                col2.metric('**Walleye BFI**',BFI_WAE)
                col4.metric('**Walleye BFI Percentile**',BFI_WAE_PCT)
            with tab3:
                fig = px.line(x=fss['Length'], y=fss['NOPpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['NOPpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 46])
                tab3.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab2.columns(5)
                col2.metric('**Northern Pike BFI**',BFI_NOP)
                col4.metric('**Northern Pike BFI Percentile**',BFI_NOP_PCT)
            with tab4:
                fig = px.line(x=fss['Length'], y=fss['LATpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['LATpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 42])
                tab4.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab3.columns(5)
                col2.metric('**Lake Trout BFI**',BFI_LAT)
                col4.metric('**Lake Trout BFI Percentile**',BFI_LAT_PCT)
            with tab5:
                fig = px.line(x=fss['Length'], y=fss['SMBpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['SMBpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 22])
                tab5.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab4.columns(5)
                col2.metric('**Smallmouth Bass BFI**',BFI_SMB)
                col4.metric('**Smallmouth Bass BFI Percentile**',BFI_SMB_PCT)
            
        else:
            st.write("No Fishery Survey Data for Walleye, Northern Pike, Smallmouth, or Lake Trout")
        st.write('**Survey Date:**    '+SurveyDate)
        #convert html to markdown
        st.header('Status of the Fishery')
        FishStat2 = markdownify.markdownify(FishStat,heading_style="ATX")
        st.write(FishStat2)
    
        #Youtube Section
        st.header('YouTube Videos for this Lake')
        api_key='AIzaSyBk20ZEJpaHb-_qaD6z43JNP2GckViiZgk'
        youtube = build('youtube','v3',developerKey = api_key)
        search=lake_select+' lake BWCA'
        request = youtube.search().list(q=search,part='snippet',type='video')
        res = request.execute()
        list=[]
        for item in res['items']:
            list.append(item['id']['videoId'])
        #search
        yt_url1='https://www.youtube.com/watch?v='+list[0]
        yt_url2='https://www.youtube.com/watch?v='+list[1]
        yt_url3='https://www.youtube.com/watch?v='+list[2]
        st.video(yt_url1)
        st.video(yt_url2)
        st.video(yt_url3)
if selected=="Big Fish Index":
    @st.cache_data
    def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    st.header('Big Fish Index (BFI)')
    with st.expander('What is it?'):
        st.write('BFI is a lake and species level ranking metric that compares the fish size distribution of a selected lake, to the fish size distribution of all BWCA lakes with Fish Survey Data.')
    with st.expander('How is it calculated?'):
        st.write('BFI is calculated as a ratio of the average length of a fish species between a sample (selected lake) and population (all BWCA lakes). This ratio is then scaled into an index from 1-100 based on the minimum and maximum values from all BWCA lakes.  Higher values indicate a larger fish size distribution.')
    
    #county filter.  
    st.header('Filter by County')
    county_select=st.selectbox('Select County',['All']+list(lm_reduce['County'].unique()))
    #join lakeagg
    merged=lm_reduce.merge(lakeagg, how='inner', left_on=['ID'], right_on=['LakeID'])
    if county_select=='All':
        merged_reduced=merged
    else:
        merged_reduced=merged[merged['County']==county_select].reset_index()
    # CSS to inject contained in a string
    hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    #show ranking by species within filtered universe
    st.header('BFI Rankings')
    tab1,tab2,tab3,tab4=st.tabs(['Walleye','Northern Pike','Lake Trout','Smallmouth Bass'])
    with tab1:
        t1cols=['lake','ID','Nearest Town','County','BFI_WAE','BFI_WAE_Pct']
        t1=merged_reduced.sort_values(by=['BFI_WAE'],ascending=False)
        tab1.table(t1[t1cols].head(20))
        csv = convert_df(t1)
        st.download_button(label="Download data as CSV",data=csv,file_name='WAE_BFI.csv',mime='text/csv',)
    with tab2:
        t2cols=['lake','ID','Nearest Town','County','BFI_NOP','BFI_NOP_Pct']
        t2=merged_reduced.sort_values(by=['BFI_NOP'],ascending=False)
        tab2.table(t2[t2cols].head(20))
        csv = convert_df(t2)
        st.download_button(label="Download data as CSV",data=csv,file_name='NOP_BFI.csv',mime='text/csv',)
    with tab3:
        t3cols=['lake','ID','Nearest Town','County','BFI_LAT','BFI_LAT_Pct']
        t3=merged_reduced.sort_values(by=['BFI_LAT'],ascending=False)
        tab3.table(t3[t3cols].head(20))
        csv = convert_df(t3)
        st.download_button(label="Download data as CSV",data=csv,file_name='LAT_BFI.csv',mime='text/csv',)
    with tab4:
        t4cols=['lake','ID','Nearest Town','County','BFI_SMB','BFI_SMB_Pct']
        t4=merged_reduced.sort_values(by=['BFI_SMB'],ascending=False)
        tab4.table(t4[t4cols].head(20))
        csv = convert_df(t4[t4cols].head(50))
        st.download_button(label="Download data as CSV",data=csv,file_name='SMB_BFI.csv',mime='text/csv',)
        
    #3d plot
    st.header('3-D Plot')
    fig = px.scatter_3d(merged_reduced, x='BFI_NOP', y='BFI_WAE', z='BFI_SMB',color='County',hover_name="lake",width=1200,height=1000)
    st.plotly_chart(fig)

if selected=="Gallery":
    tab1,tab2,tab3,tab4=st.tabs(['Smallmouth','Walleye','Northern Pike','Lake Trout'])
    with tab1:
        col1,col2=st.columns(2)
        col1.image('vidimage/B1.JPG')
        col1.image('vidimage/B2.JPG')
        col1.image('vidimage/B3.JPG')
        col1.image('vidimage/B4.JPG')
        col1.image('vidimage/B5.JPG')
        col1.image('vidimage/B6.JPG')
        col1.image('vidimage/B7.JPG')
        col1.image('vidimage/B8.JPG')
        col1.image('vidimage/B9.JPG')
        col1.image('vidimage/B10.JPG')
        col1.image('vidimage/B11.JPG')
        col1.image('vidimage/B12.JPG')
        col2.image('vidimage/B13.JPG')
        col2.image('vidimage/B14.JPG')
        col2.image('vidimage/B15.JPG')
        col2.image('vidimage/B16.JPG')
        col2.image('vidimage/B17.JPG')
        col2.image('vidimage/B18.JPG')
        col2.image('vidimage/B19.JPG')
        col2.image('vidimage/B20.JPG')
        col2.image('vidimage/B21.JPG')
        col2.image('vidimage/B22.JPG')
        col2.image('vidimage/B23.JPG')
    with tab2:
        col1,col2=st.columns(2)
        col1.image('vidimage/W1.JPG')
        col1.image('vidimage/W2.JPG')
        col1.image('vidimage/W3.JPG')
        col1.image('vidimage/W4.JPG')
        col1.image('vidimage/W5.JPG')
        col1.image('vidimage/W6.JPG')
        col1.image('vidimage/W7.JPG')
        col2.image('vidimage/W8.JPG')
        col2.image('vidimage/W9.JPG')
        col2.image('vidimage/W10.JPG')
        col2.image('vidimage/W11.JPG')
        col2.image('vidimage/W12.JPG')
        col2.image('vidimage/W13.JPG')
        col2.image('vidimage/W14.JPG')
    with tab3:
        col1,col2=st.columns(2)
        col1.image('vidimage/N1.JPG')
        col1.image('vidimage/N2.JPG')
        col1.image('vidimage/N3.JPG')
        col2.image('vidimage/N4.JPG')
        col2.image('vidimage/N5.JPG')
        col2.image('vidimage/N6.JPG')
        col2.image('vidimage/N7.JPG')
    with tab4:
        col1,col2=st.columns(2)
        col1.image('vidimage/LT1.JPG')
        col1.image('vidimage/LT2.JPG')
        col2.image('vidimage/LT3.JPG')
        col2.image('vidimage/LT4.JPG')

