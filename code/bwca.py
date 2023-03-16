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
    selected = option_menu("BWCA Lake Search", ["About", 'Lake Search','BFI','Gallery'], 
        icons=['info-circle','search','calculator','camera'],menu_icon="tree-fill", default_index=0)
  
#read data
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
    st.subheader('Lake Search')
    st.write('**(1)**     Enter a Lake Name')
    st.write('**(2)**     Interactive map auto centered to lake selection, topographic and satellite layers, markers/colors for campsites and portages, hover data shows campsite number and portage distance)')
    st.write('**(3)**     Fishery Lake Survey data shown which includes: Lake Characteristics, Fish Size Distribution, and Status of the Fishery')
    st.write('**(4)**     Top three search results from YouTube for the prompt "<selected lake> BWCA"')
    st.subheader('BFI')
    st.write('**(1)**     Optional filter on County within BWCA')
    st.write('**(2)**     List of lakes within county selection, sorted by BFI (high to low), with tab options for different species, and a download to CSV button')
    st.write('**(3)**     3-D scatter plot that shows lakes with non missing BFI values for Walleye, Northern Pike, and Smallmouth Bass, hover data contains lake name and BFI values')
if selected=="Lake Search":
    lm = pd.read_csv('CountyLakeMapping.csv',dtype=str)
    lm.rename(columns={'Name': 'lake'}, inplace=True)
    lakeagg=pd.read_csv('lakeagg.csv')
    camps=pd.read_csv('campsites.csv')
    camps.rename(columns={'Y': 'lat', 'X': 'lon', 'name': 'info'}, inplace=True)
    camps['Legend']='Campsite'
    camps[['test1','lake','test3','test4','test5','test6','test7','test8']] = camps['desc'].str.split('-', expand = True)
    camps['lake']=camps['lake'].str.replace('Lake','')
    camps['lake']=camps['lake'].str.strip()
    camps_lo=camps[['lake']].drop_duplicates()
    lm_reduce = pd.merge(lm,camps_lo, on='lake')  
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
    camps_ports=pd.concat([camps, ports3], ignore_index=True, sort=False)

    st.header('Search for a Lake')
    lake_select = st.selectbox('Select Lake',list(lm_reduce['lake'].unique()),index=127)

    if lake_select:
        st.header(lake_select)
        fss=pd.read_csv('FishSurveySum.csv')
        #get ID for Lake Name
        lakeid=lm_reduce[lm_reduce['lake']==lake_select].reset_index()
        numlakes=0
        if len(lakeid.index)>1:
            numlakes=len(lakeid)
            st.write('There are multiple with that name! Pick the nearest town')
            town_select=st.selectbox('Select Town',list(lakeid['Nearest Town'].unique()),index=0)
            lakeid=lakeid[lakeid['Nearest Town']==town_select].reset_index()
        lakeidval=lakeid.loc[0]['ID']

        #subset lakeagg  on selected lake
        lakeagg['LakeID']=lakeagg['LakeID'].astype(str)
        lakeaggshort=lakeagg[lakeagg['LakeID']==lakeidval].reset_index()

        #subset campsites on selected lake - this is to help center and zoom the map for display
        camps_small=camps[camps['lake']==lake_select]
        #if lakeid['County']=='St. Louis':
        #     camps_small2=(camps['lon']>=-93.00)&(camps['lon']<=-91.75)
        #if lakeid['County']=='Lake':
        #    camps_small2=(camps['lon']>=-91.80)&(camps['lon']<=-91.02)
        #if lakeid['County']=='Cook':
        #    camps_small2=(camps['lon']>=-91.07)&(camps['lon']<=-89.46)
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
        lakeaggshort['BFI_NOP_Pct'] = lakeaggshort['BFI_NOP_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_LAT_Pct'] = lakeaggshort['BFI_LAT_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_SMB_Pct'] = lakeaggshort['BFI_SMB_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)
        lakeaggshort['BFI_WAE_Pct'] = lakeaggshort['BFI_WAE_Pct'].apply(lambda x: x*100).map('{:,.2f}%'.format)

        if not lakeaggshort.empty:
            BFI_NOP=lakeaggshort.loc[0]['BFI_NOP']
            BFI_NOP_PCT=lakeaggshort.loc[0]['BFI_NOP_Pct']
            BFI_LAT=lakeaggshort.loc[0]['BFI_LAT']
            BFI_LAT_PCT=lakeaggshort.loc[0]['BFI_LAT_Pct']
            BFI_SMB=lakeaggshort.loc[0]['BFI_SMB']
            BFI_SMB_PCT=lakeaggshort.loc[0]['BFI_SMB_Pct']
            BFI_WAE=lakeaggshort.loc[0]['BFI_WAE']
            BFI_WAE_PCT=lakeaggshort.loc[0]['BFI_WAE_Pct']
    

            tab1,tab2,tab3,tab4=st.tabs(['Walleye','Northern Pike','Lake Trout','Smallmouth Bass'])
            with tab1:
                fig = px.line(x=fss['Length'], y=fss['WAEpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['WAEpct'], marker_color='red',name=lake_select)
                fig.update_xaxes(range=[0, 32])
                tab1.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab1.columns(5)
                col2.metric('**Walleye BFI**',BFI_WAE)
                col4.metric('**Walleye BFI Percentile**',BFI_WAE_PCT)
            with tab2:
                fig = px.line(x=fss['Length'], y=fss['NOPpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['NOPpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 46])
                tab2.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab2.columns(5)
                col2.metric('**Northern Pike BFI**',BFI_NOP)
                col4.metric('**Northern Pike BFI Percentile**',BFI_NOP_PCT)
            with tab3:
                fig = px.line(x=fss['Length'], y=fss['LATpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['LATpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 42])
                tab3.plotly_chart(fig, use_container_width=True)
                col1,col2,col3,col4,col5=tab3.columns(5)
                col2.metric('**Lake Trout BFI**',BFI_LAT)
                col4.metric('**Lake Trout BFI Percentile**',BFI_LAT_PCT)
            with tab4:
                fig = px.line(x=fss['Length'], y=fss['SMBpct'], color=px.Constant('All BWCA'),labels=dict(x='Length', y='Pct', color='Legend'))
                fig.add_bar(x=fss['Length'], y=fg['SMBpct'],marker_color='red', name=lake_select)
                fig.update_xaxes(range=[0, 22])
                tab4.plotly_chart(fig, use_container_width=True)
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

if selected=="BFI":
    @st.cache_data
    def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    #read in data
    lm = pd.read_csv('CountyLakeMapping.csv',dtype=str)
    lm.rename(columns={'Name': 'lake'}, inplace=True)
    camps=pd.read_csv('campsites.csv')
    camps.rename(columns={'Y': 'lat', 'X': 'lon', 'name': 'info'}, inplace=True)
    camps['Legend']='Campsite'
    camps[['test1','lake','test3','test4','test5','test6','test7','test8']] = camps['desc'].str.split('-', expand = True)
    camps['lake']=camps['lake'].str.replace('Lake','')
    camps['lake']=camps['lake'].str.strip()
    camps_lo=camps[['lake']].drop_duplicates()
    lakeagg=pd.read_csv('lakeagg.csv')
    lakeagg['LakeID']=lakeagg['LakeID'].astype(str)
    #only keep lakes with campsites to align with other page
    lm_reduce = pd.merge(lm,camps_lo, on='lake')  
    #county filter
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
        tab4.table(t4)
        csv = convert_df(t4[t4cols].head(50))
        st.download_button(label="Download data as CSV",data=csv,file_name='SMB_BFI.csv',mime='text/csv',)
        
    #3d plot
    st.header('3-D Plot')
    fig = px.scatter_3d(merged_reduced, x='BFI_NOP', y='BFI_WAE', z='BFI_SMB',color='County',hover_name="lake",width=1200,height=1000)
    st.plotly_chart(fig)

if selected=="Gallery":
    col1,col2=st.columns(2)
    col1.image('vidimage/1.JPG')
    col1.image('vidimage/3.JPG')
    col1.image('vidimage/5.JPG')
    col1.image('vidimage/7.JPG')
    col1.image('vidimage/9.JPG')
    col1.image('vidimage/11.JPG')
    col1.image('vidimage/13.JPG')
    col1.image('vidimage/15.JPG')
    col1.image('vidimage/17.JPG')
    col1.image('vidimage/19.JPG')
    col1.image('vidimage/21.JPG')
    col1.image('vidimage/23.JPG')
    col1.image('vidimage/25.JPG')
    col1.image('vidimage/27.JPG')
    col1.image('vidimage/29.JPG')
    col1.image('vidimage/31.JPG')
    col1.image('vidimage/33.JPG')
    col1.image('vidimage/35.JPG')
    col1.image('vidimage/37.JPG')
    col1.image('vidimage/39.JPG')
    col1.image('vidimage/41.JPG')
    col1.image('vidimage/43.JPG')
    col1.image('vidimage/45.JPG')
    col1.image('vidimage/47.JPG')
    col1.image('vidimage/49.JPG')
    col1.image('vidimage/52.JPG')
    col1.image('vidimage/56.JPG')
    col1.image('vidimage/57.JPG')
    col2.image('vidimage/2.JPG')
    col2.image('vidimage/4.JPG')
    col2.image('vidimage/6.JPG')
    col2.image('vidimage/8.JPG')
    col2.image('vidimage/10.JPG')
    col2.image('vidimage/12.JPG')
    col2.image('vidimage/14.JPG')
    col2.image('vidimage/16.JPG')
    col2.image('vidimage/18.JPG')
    col2.image('vidimage/20.JPG')
    col2.image('vidimage/22.JPG')
    col2.image('vidimage/24.JPG')
    col2.image('vidimage/26.JPG')
    col2.image('vidimage/28.JPG')
    col2.image('vidimage/30.JPG')
    col2.image('vidimage/32.JPG')
    col2.image('vidimage/34.JPG')
    col2.image('vidimage/36.JPG')
    col2.image('vidimage/38.JPG')
    col2.image('vidimage/40.JPG')
    col2.image('vidimage/42.JPG')
    col2.image('vidimage/44.JPG')
    col2.image('vidimage/46.JPG')
    col2.image('vidimage/48.JPG')
    col2.image('vidimage/50.JPG')
    col2.image('vidimage/53.JPG')
    col2.image('vidimage/54.JPG')
    col2.image('vidimage/55.JPG')
    col2.image('vidimage/51.JPG')

 


