import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

from rss_aggregator import DonorRSSAggregator

# Page config
st.set_page_config(
    page_title="Donor Opportunity Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2563eb;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .opportunity-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2563eb;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .urgent-card {
        border-left-color: #dc2626;
        background: #fef2f2;
    }
    .high-priority-card {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }
    .stButton>button {
        background: #2563eb;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

def load_applications():
    """Load application tracking data"""
    try:
        if os.path.exists('applications.json'):
            with open('applications.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_applications():
    """Save application tracking data"""
    try:
        with open('applications.json', 'w') as f:
            json.dump(st.session_state.applications, f, indent=2)
    except Exception as e:
        st.error(f"Error saving applications: {e}")

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = None
if 'applications' not in st.session_state:
    st.session_state.applications = load_applications()

def load_latest_opportunities():
    """Load the most recent CSV file"""
    csv_files = list(Path('.').glob('rss_opportunities_*.csv'))
    
    if not csv_files:
        return None
    
    # Get the most recent file
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    
    try:
        df = pd.read_csv(latest_file)
        
        # Convert sectors from string to list if needed
        if 'sectors' in df.columns:
            df['sectors'] = df['sectors'].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else [x])
        
        return df
    except Exception as e:
        st.error(f"Error loading opportunities: {e}")
        return None

def run_scan():
    """Run a new RSS scan"""
    with st.spinner("🔍 Scanning RSS feeds... This may take 1-2 minutes..."):
        try:
            from rss_aggregator import DonorRSSAggregator
            
            aggregator = DonorRSSAggregator(
                country="Tanzania",
                sectors=["education", "health"]
            )
            
            results = aggregator.scan_all_feeds()
            
            if len(results) > 0:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"rss_opportunities_{timestamp}.csv"
                results.to_csv(filename, index=False)
                st.session_state.opportunities = results
                st.success(f"✅ Found {len(results)} opportunities! Saved to {filename}")
            else:
                st.info("No new opportunities found this time. Try again later!")
            
            return results
            
        except ImportError:
            st.error("⚠️ rss_donor_aggregator.py not found. Make sure it's in the same directory.")
            return None
        except Exception as e:
            st.error(f"Error running scan: {e}")
            return None

# SIDEBAR
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/goal.png", width=80)
    st.title("Donor Tracker")
    
    st.markdown("---")
    
    # Scan button
    if st.button("🔄 Run New Scan", use_container_width=True):
        run_scan()
        st.rerun()
    
    # Load data button
    if st.button("📂 Load Latest Data", use_container_width=True):
        st.session_state.opportunities = load_latest_opportunities()
        st.rerun()
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Filters")
    
    if st.session_state.opportunities is not None:
        df = st.session_state.opportunities
        
        # Relevance filter
        min_relevance = st.slider(
            "Min Relevance Score",
            min_value=0,
            max_value=10,
            value=5,
            help="Filter by relevance score (0-10)"
        )
        
        # Source type filter
        source_types = ['All'] + sorted(df['source_type'].unique().tolist())
        selected_source = st.selectbox("Source Type", source_types)
        
        # Sector filter
        all_sectors = set()
        for sectors in df['sectors']:
            if isinstance(sectors, list):
                all_sectors.update(sectors)
        
        sector_options = ['All'] + sorted(list(all_sectors))
        selected_sector = st.selectbox("Sector", sector_options)
        
        # Deadline filter
        deadline_filter = st.radio(
            "Deadlines",
            ["All", "With Deadline", "No Deadline"]
        )
    
    st.markdown("---")
    
    # Stats
    st.subheader("📊 Quick Stats")
    if st.session_state.opportunities is not None:
        df = st.session_state.opportunities
        st.metric("Total Opportunities", len(df))
        st.metric("With Deadlines", df['deadline'].notna().sum())
        st.metric("Applications Tracked", len(st.session_state.applications))
    else:
        st.info("Load data to see stats")

# MAIN CONTENT
st.markdown('<p class="main-header">🎯 Donor Opportunity Dashboard</p>', unsafe_allow_html=True)
st.markdown(f"**Tanzania • Education & Health** | Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

# Check if we have data
if st.session_state.opportunities is None:
    st.info("👆 Click 'Load Latest Data' in the sidebar to get started, or 'Run New Scan' to fetch fresh opportunities.")
    
    # Show instructions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Getting Started
        
        1. **Run New Scan** - Fetch latest opportunities from RSS feeds
        2. **Load Latest Data** - Load previously scanned data
        3. **Filter & Explore** - Use sidebar filters to find relevant opportunities
        4. **Track Applications** - Mark opportunities you've applied to
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Features
        
        - 📊 Visual analytics and charts
        - 🔍 Smart filtering by sector, source, relevance
        - ⏰ Deadline tracking and alerts
        - 📝 Application status tracking
        - 📥 Export filtered results
        """)
    
    st.stop()

# We have data - let's display it!
df = st.session_state.opportunities.copy()

# Apply filters
if 'min_relevance' in locals():
    df = df[df['relevance_score'] >= min_relevance]

if 'selected_source' in locals() and selected_source != 'All':
    df = df[df['source_type'] == selected_source]

if 'selected_sector' in locals() and selected_sector != 'All':
    df = df[df['sectors'].apply(lambda x: selected_sector in x if isinstance(x, list) else False)]

if 'deadline_filter' in locals():
    if deadline_filter == "With Deadline":
        df = df[df['deadline'].notna()]
    elif deadline_filter == "No Deadline":
        df = df[df['deadline'].isna()]

# METRICS ROW
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📊 Total Opportunities",
        len(df),
        delta=f"{len(df[df['is_new']])} new" if 'is_new' in df.columns else None
    )

with col2:
    high_priority = len(df[df['relevance_score'] >= 8])
    st.metric("🔥 High Priority", high_priority)

with col3:
    with_deadline = df['deadline'].notna().sum()
    st.metric("⏰ With Deadlines", with_deadline)

with col4:
    applied = len([k for k in st.session_state.applications.keys() if k in df['url'].values])
    st.metric("✅ Applied", applied)

st.markdown("---")

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Opportunities", "📊 Analytics", "📝 Applications", "⚙️ Settings"])

# TAB 1: OPPORTUNITIES LIST
with tab1:
    st.subheader(f"Showing {len(df)} Opportunities")
    
    # Sort options
    sort_col1, sort_col2 = st.columns([3, 1])
    with sort_col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Relevance Score", "Date Added", "Deadline", "Title"],
            key="sort_opportunities"
        )
    
    with sort_col2:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
    
    # Sort dataframe
    sort_mapping = {
        "Relevance Score": "relevance_score",
        "Date Added": "discovered",
        "Deadline": "deadline",
        "Title": "title"
    }
    
    df_sorted = df.sort_values(
        sort_mapping[sort_by],
        ascending=(sort_order == "Ascending")
    )
    
    # Display opportunities
    for idx, row in df_sorted.iterrows():
        # Determine card style
        card_class = "opportunity-card"
        if row['deadline'] and pd.notna(row['deadline']):
            card_class = "urgent-card"
        elif row['relevance_score'] >= 8:
            card_class = "high-priority-card"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            # Header row
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### {row['title']}")
                
                # Badges
                badges = f"**Source:** {row['source']} | **Type:** {row['source_type']} | **Relevance:** {row['relevance_score']}/10"
                if row['deadline'] and pd.notna(row['deadline']):
                    badges += f" | ⏰ **Deadline:** {row['deadline']}"
                if row['amount'] and pd.notna(row['amount']):
                    badges += f" | 💰 **Amount:** {row['amount']}"
                
                st.markdown(badges)
                
                # Sectors
                if isinstance(row['sectors'], list):
                    sectors_str = " • ".join([f"🏷️ {s}" for s in row['sectors']])
                    st.markdown(sectors_str)
            
            with col2:
                # Application status
                is_applied = row['url'] in st.session_state.applications
                
                if is_applied:
                    status = st.session_state.applications[row['url']]['status']
                    st.success(f"✅ {status}")
                else:
                    if st.button("Track", key=f"track_{idx}"):
                        st.session_state.applications[row['url']] = {
                            'title': row['title'],
                            'status': 'Interested',
                            'date_added': datetime.now().strftime('%Y-%m-%d'),
                            'notes': ''
                        }
                        save_applications()
                        st.rerun()
            
            # Description
            st.markdown(f"**Description:** {row['description'][:300]}...")
            
            # Link
            st.markdown(f"🔗 [View Full Opportunity]({row['url']})")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("")

# TAB 2: ANALYTICS
with tab2:
    st.subheader("📊 Opportunity Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Opportunities by source type
        fig1 = px.pie(
            df,
            names='source_type',
            title='Opportunities by Source Type',
            hole=0.4
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Relevance score distribution
        fig3 = px.histogram(
            df,
            x='relevance_score',
            nbins=10,
            title='Relevance Score Distribution',
            labels={'relevance_score': 'Relevance Score', 'count': 'Number of Opportunities'}
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Opportunities by sector
        all_sectors = []
        for sectors in df['sectors']:
            if isinstance(sectors, list):
                all_sectors.extend(sectors)
        
        sector_counts = (
            pd.Series(all_sectors)
            .value_counts()
            .reset_index()
        )

        sector_counts.columns = ['Sector', 'Count']

        fig2 = px.bar(
            sector_counts,
            x='Sector',
            y='Count',
            title='Opportunities by Sector'
        )

        st.plotly_chart(fig2, use_container_width=True)
        
        # Top sources
        source_counts = (
            df['source']
            .value_counts()
            .head(10)
            .reset_index()
        )

        source_counts.columns = ['Source', 'Count']

        fig4 = px.bar(
            source_counts,
            x='Count',
            y='Source',
            orientation='h',
            title='Top 10 Sources'
        )

        st.plotly_chart(fig4, use_container_width=True)
    
    # Timeline if we have dates
    st.subheader("📅 Discovery Timeline")
    
    if 'discovered' in df.columns:
        df['discovered_date'] = pd.to_datetime(df['discovered'], errors='coerce')
        timeline_df = df.groupby(df['discovered_date'].dt.date).size().reset_index()
        timeline_df.columns = ['Date', 'Count']
        
        fig5 = px.line(
            timeline_df,
            x='Date',
            y='Count',
            title='Opportunities Discovered Over Time',
            markers=True
        )
        st.plotly_chart(fig5, use_container_width=True)

# TAB 3: APPLICATIONS
with tab3:
    st.subheader("📝 Application Tracker")
    
    if len(st.session_state.applications) == 0:
        st.info("No applications tracked yet. Click 'Track' on any opportunity to start tracking.")
    else:
        # Application status filter
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Interested", "Applied", "Under Review", "Awarded", "Rejected"]
        )
        
        for url, app in st.session_state.applications.items():
            if status_filter != "All" and app['status'] != status_filter:
                continue
            
            with st.expander(f"📄 {app['title']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Update status
                    new_status = st.selectbox(
                        "Status",
                        ["Interested", "Applied", "Under Review", "Awarded", "Rejected"],
                        index=["Interested", "Applied", "Under Review", "Awarded", "Rejected"].index(app['status']),
                        key=f"status_{url}"
                    )
                    
                    if new_status != app['status']:
                        st.session_state.applications[url]['status'] = new_status
                        save_applications()
                        st.rerun()
                    
                    # Notes
                    notes = st.text_area(
                        "Notes",
                        value=app.get('notes', ''),
                        key=f"notes_{url}",
                        height=100
                    )
                    
                    if notes != app.get('notes', ''):
                        st.session_state.applications[url]['notes'] = notes
                        save_applications()
                
                with col2:
                    st.markdown(f"**Added:** {app['date_added']}")
                    st.markdown(f"[View Opportunity]({url})")
                    
                    if st.button("🗑️ Remove", key=f"remove_{url}"):
                        del st.session_state.applications[url]
                        save_applications()
                        st.rerun()

# TAB 4: SETTINGS
with tab4:
    st.subheader("⚙️ Settings & Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Export Data")
        
        if st.button("Export Opportunities to CSV"):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"filtered_opportunities_{timestamp}.csv"
            df.to_csv(filename, index=False)
            st.success(f"✅ Exported to {filename}")
        
        if st.button("Export Applications to CSV"):
            if len(st.session_state.applications) > 0:
                apps_df = pd.DataFrame.from_dict(st.session_state.applications, orient='index')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"applications_{timestamp}.csv"
                apps_df.to_csv(filename)
                st.success(f"✅ Exported to {filename}")
            else:
                st.warning("No applications to export")
    
    with col2:
        st.markdown("### 🔄 Data Management")
        
        # Show available data files
        csv_files = list(Path('.').glob('rss_opportunities_*.csv'))
        
        if csv_files:
            st.write(f"Found {len(csv_files)} data files:")
            for f in sorted(csv_files, reverse=True)[:5]:
                st.text(f"📄 {f.name}")
        
        if st.button("🗑️ Clear Application History"):
            if st.checkbox("Are you sure?"):
                st.session_state.applications = {}
                save_applications()
                st.success("Application history cleared")
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
    ### 💡 Tips
    
    - Run scans daily to catch new opportunities
    - Use filters to focus on high-priority items
    - Track applications to stay organized
    - Export data for reporting or sharing
    - Set up automation to run scans automatically
    """)

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🎯 Donor Opportunity Tracker | Built for Tanzania Education & Health NGOs</p>
    <p>Data refreshed from RSS feeds | Not affiliated with any donor organization</p>
</div>
""", unsafe_allow_html=True)