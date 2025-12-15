"""
Social Media Analytics Dashboard
A Streamlit application for analyzing social media data with interactive visualizations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from data_loader import load_and_preprocess_data
from analytics import SocialMediaAnalytics
from visualizations import SocialMediaVisualizations, create_top_keywords_chart
from gemini_chatbot import GeminiChatbot, render_chatbot_interface, is_gemini_available
import networkx as nx


# Page configuration
st.set_page_config(
    page_title="Social Media Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache the social media data."""
    try:
        return load_and_preprocess_data("data/data.jsonl")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()


def apply_filters(data, keyword_filter, date_range, platform_filter, subreddit_filter):
    """Apply user-selected filters to the data."""
    filtered_data = data.copy()
    
    # Keyword filter
    if keyword_filter:
        filtered_data = filtered_data[
            filtered_data['combined_text'].str.contains(keyword_filter.lower(), na=False)
        ]
    
    # Date range filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['created_at'].dt.date >= start_date) &
            (filtered_data['created_at'].dt.date <= end_date)
        ]
    
    # Platform filter
    if platform_filter and platform_filter != "All":
        filtered_data = filtered_data[filtered_data['platform'] == platform_filter]
    
    # Subreddit filter
    if subreddit_filter and subreddit_filter != "All":
        filtered_data = filtered_data[filtered_data['subreddit'] == subreddit_filter]
    
    return filtered_data


def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Social Media Analytics Dashboard</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Investigative Social Media Analytics** - Explore patterns, trends, and networks in social media data.
    This dashboard provides insights into content spread, key contributors, and community interactions.
    """)
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_data()
    
    if data.empty:
        st.error("No data available. Please check your data file.")
        return
    
    # Initialize analytics and visualization classes
    analytics = SocialMediaAnalytics(data)
    viz = SocialMediaVisualizations()
    
    # Initialize chatbot
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = GeminiChatbot()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Keyword search
    keyword_filter = st.sidebar.text_input(
        "Search by keyword/phrase:",
        placeholder="Enter keywords to search in posts..."
    )
    
    # Date range filter
    if not data['created_at'].isna().all():
        min_date = data['created_at'].min().date()
        max_date = data['created_at'].max().date()
        
        date_range = st.sidebar.date_input(
            "Select date range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = None
        st.sidebar.warning("No valid dates found in data")
    
    # Platform filter
    platforms = ["All"] + sorted(data['platform'].unique().tolist())
    platform_filter = st.sidebar.selectbox("Platform:", platforms)
    
    # Subreddit filter (top 20 most active)
    top_subreddits = data['subreddit'].value_counts().head(20).index.tolist()
    subreddit_options = ["All"] + top_subreddits
    subreddit_filter = st.sidebar.selectbox("Subreddit:", subreddit_options)
    
    # Apply filters
    filtered_data = apply_filters(data, keyword_filter, date_range, platform_filter, subreddit_filter)
    
    # Display filter results
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Filtered Results:** {len(filtered_data):,} posts")
    
    # Main dashboard content
    if filtered_data.empty:
        st.warning("No data matches the selected filters. Please adjust your criteria.")
        return
    
    # Summary Statistics
    st.markdown('<h2 class="section-header">📈 Summary Statistics</h2>', unsafe_allow_html=True)
    
    summary_stats = analytics.get_summary_stats(filtered_data)
    viz.create_summary_metrics_cards(summary_stats)
    
    # Time Series Analysis
    st.markdown('<h2 class="section-header">📅 Time Series Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Post volume over time
        time_series_data = analytics.get_time_series_data(filtered_data, freq='D')
        time_series_fig = viz.create_time_series_plot(time_series_data)
        st.plotly_chart(time_series_fig, use_container_width=True)
    
    with col2:
        # Weekly posting rhythm bar chart
        rhythm_data = analytics.get_weekly_posting_rhythm(filtered_data)
        rhythm_fig = viz.create_weekly_rhythm_bar_chart(rhythm_data)
        st.plotly_chart(rhythm_fig, use_container_width=True)
    
    # Topic/Theme Analysis
    st.markdown('<h2 class="section-header">🏷️ Topic Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top keywords
        top_keywords = analytics.get_top_keywords(filtered_data, top_n=15)
        keywords_fig = create_top_keywords_chart(top_keywords, "Top Keywords")
        st.plotly_chart(keywords_fig, use_container_width=True)
        
    
    with col2:
        # Keyword trends over time
        if top_keywords:
            # Use top 5 keywords for trend analysis
            top_5_keywords = [kw[0] for kw in top_keywords[:5]]
            keyword_trends = analytics.get_keyword_time_series(filtered_data, top_5_keywords, freq='D')
            
            if not keyword_trends.empty:
                trends_fig = viz.create_keyword_trends_plot(keyword_trends)
                st.plotly_chart(trends_fig, use_container_width=True)
            else:
                st.info("No keyword trend data available for the selected period.")
    
    # Community Analysis
    st.markdown('<h2 class="section-header">👥 Community & Contributors</h2>', unsafe_allow_html=True)
    
    # Top contributors (full width)
    top_contributors = analytics.get_top_contributors(filtered_data, top_n=10)
    contributors_fig = viz.create_contributors_chart(top_contributors, chart_type="bar")
    st.plotly_chart(contributors_fig, use_container_width=True)
    
    # Network Analysis
    st.markdown('<h2 class="section-header">🕸️ Top Authors & Subreddits Network</h2>', unsafe_allow_html=True)
    
    st.markdown("**Network showing connections between the most active authors and popular subreddits:**")
    st.info("📊 **Automatically displays:** Top 15 authors and top 10 subreddits based on post volume")
    
    # Build and display network
    with st.spinner("Building top authors-subreddits network..."):
        network_graph = analytics.build_top_author_subreddit_network(filtered_data)
    
    if network_graph.number_of_nodes() > 0:
        # Network statistics
        network_stats = analytics.get_network_stats(network_graph)
        
        # Network visualization
        st.markdown("**Interactive Author-Subreddit Network:**")
        network_html = viz.create_network_visualization(network_graph, "Author-Subreddit Network")
        
        # Display network in Streamlit
        st.components.v1.html(network_html, height=500)
        
        st.info("""
        💡 **Network Insights:**
        - **👤 Blue nodes** represent the top 15 most active authors
        - **📋 Orange nodes** represent the top 10 most popular subreddits  
        - **Edge thickness** shows posting frequency (thicker = more posts)
        - **Node size** reflects the number of connections
        - **Focused View**: Only shows the most significant contributors and communities
        - Hover over nodes and edges for detailed information
        """)
    
    else:
        st.warning("No network connections found with the current filters. The top authors and subreddits may not have overlapping activity.")
    
    # Data Export Section
    st.markdown('<h2 class="section-header">💾 Data Export</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download Filtered Data (CSV)"):
            csv_data = filtered_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"social_media_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📈 Download Summary Report"):
            # Create a simple summary report
            report = f"""
Social Media Analytics Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS:
- Total Posts: {summary_stats['total_posts']:,}
- Unique Authors: {summary_stats['unique_authors']:,}
- Date Range: {summary_stats['date_range']}
- Average Score: {summary_stats['avg_score']:.2f}
- Total Comments: {summary_stats['total_comments']:,}

TOP CONTRIBUTORS:
{top_contributors[['author', 'post_count', 'percentage']].to_string(index=False)}

TOP KEYWORDS:
{chr(10).join([f"{kw}: {count}" for kw, count in top_keywords[:10]])}

NETWORK STATISTICS:
- Nodes: {network_stats.get('nodes', 0)}
- Edges: {network_stats.get('edges', 0)}
- Density: {network_stats.get('density', 0):.3f}
- Connected Components: {network_stats.get('connected_components', 0)}
            """
            
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    
    # Floating AI Assistant
    if is_gemini_available():
        render_chatbot_interface(
            st.session_state.chatbot,
            summary_stats,
            top_keywords,
            top_contributors,
            network_stats if 'network_stats' in locals() else {}
        )


if __name__ == "__main__":
    main()