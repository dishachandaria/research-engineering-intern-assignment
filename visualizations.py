"""
Visualization module for social media analytics dashboard.
Creates 
interactive Plotly charts and network visualizations.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit as st
from typing import List, Dict, Any
import tempfile
import os
import uuid
import time


class SocialMediaVisualizations:
    """Handles creation of interactive visualizations for social media data."""
    
    def __init__(self):
        # Set consistent color palette
        self.color_palette = px.colors.qualitative.Set3
    
    def create_time_series_plot(self, time_series_data: pd.DataFrame, 
                               title: str = "Post Volume Over Time") -> go.Figure:
        """
        Create an interactive time series plot showing post volume over time.
        
        Args:
            time_series_data: DataFrame with 'date' and 'post_count' columns
            title: Plot title
            
        Returns:
            Plotly figure object
        """
        if time_series_data.empty:
            # Create empty plot with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for the selected filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Number of Posts",
                height=400
            )
            return fig
        
        fig = px.line(
            time_series_data, 
            x='date', 
            y='post_count',
            title=title,
            labels={'post_count': 'Number of Posts', 'date': 'Date'}
        )
        
        # Customize layout
        fig.update_layout(
            height=400,
            hovermode='x unified',
            xaxis_title="Date",
            yaxis_title="Number of Posts"
        )
        
        # Add hover information
        fig.update_traces(
            hovertemplate='<b>Date:</b> %{x}<br><b>Posts:</b> %{y}<extra></extra>'
        )
        
        return fig
    
    def create_keyword_trends_plot(self, keyword_data: pd.DataFrame,
                                  title: str = "Keyword Trends Over Time") -> go.Figure:
        """
        Create a multi-line plot showing keyword trends over time.
        
        Args:
            keyword_data: DataFrame with 'created_at', 'count', and 'keyword' columns
            title: Plot title
            
        Returns:
            Plotly figure object
        """
        if keyword_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No keyword data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        fig = px.line(
            keyword_data,
            x='created_at',
            y='count',
            color='keyword',
            title=title,
            labels={'count': 'Mentions', 'created_at': 'Date', 'keyword': 'Keyword'}
        )
        
        fig.update_layout(
            height=400,
            hovermode='x unified',
            xaxis_title="Date",
            yaxis_title="Number of Mentions"
        )
        
        return fig
    
    def create_contributors_chart(self, contributors_data: pd.DataFrame,
                                 chart_type: str = "bar") -> go.Figure:
        """
        Create a chart showing top contributors.
        
        Args:
            contributors_data: DataFrame with contributor statistics
            chart_type: Type of chart ('bar' or 'pie')
            
        Returns:
            Plotly figure object
        """
        if contributors_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No contributor data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title="Top Contributors", height=400)
            return fig
        
        if chart_type == "pie":
            fig = px.pie(
                contributors_data,
                values='post_count',
                names='author',
                title="Top Contributors by Post Count",
                hover_data=['percentage']
            )
            
            fig.update_traces(
                hovertemplate='<b>%{label}</b><br>Posts: %{value}<br>Percentage: %{customdata[0]:.1f}%<extra></extra>'
            )
        
        else:  # bar chart
            fig = px.bar(
                contributors_data,
                x='author',
                y='post_count',
                title="Top Contributors by Post Count",
                labels={'post_count': 'Number of Posts', 'author': 'Author'},
                hover_data=['percentage', 'avg_score']
            )
            
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>Posts: %{y}<br>Percentage: %{customdata[0]:.1f}%<br>Avg Score: %{customdata[1]:.1f}<extra></extra>'
            )
            
            # Rotate x-axis labels for better readability
            fig.update_layout(xaxis_tickangle=-45)
        
        fig.update_layout(height=400)
        return fig
    
    def create_weekly_rhythm_bar_chart(self, rhythm_data: pd.DataFrame) -> go.Figure:
        """
        Create a bar chart showing posting patterns by day of week.
        
        Args:
            rhythm_data: DataFrame with day_of_week and post_count columns
            
        Returns:
            Plotly figure object
        """
        if rhythm_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No posting rhythm data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title="Weekly Posting Rhythm", height=400)
            return fig
        
        # Create bar chart
        fig = px.bar(
            rhythm_data,
            x='day_of_week',
            y='post_count',
            title="Weekly Posting Rhythm",
            labels={'day_of_week': 'Day of Week', 'post_count': 'Number of Posts'},
            color='post_count',
            color_continuous_scale='Blues'
        )
        
        # Customize layout
        fig.update_layout(
            height=400,
            xaxis_title="Day of Week",
            yaxis_title="Number of Posts",
            showlegend=False
        )
        
        # Update hover template
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Posts: %{y}<extra></extra>'
        )
        
        # Ensure days are in correct order
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fig.update_xaxes(categoryorder='array', categoryarray=days_order)
        
        return fig
    

    
    def create_network_visualization(self, graph: nx.Graph, 
                                   title: str = "Author Network") -> str:
        """
        Create an interactive network visualization using PyVis.
        
        Args:
            graph: NetworkX graph object
            title: Visualization title
            
        Returns:
            HTML string for embedding in Streamlit
        """
        if graph.number_of_nodes() == 0:
            return "<div style='text-align: center; padding: 50px;'>No network data available for the selected filters</div>"
        
        # Create PyVis network
        net = Network(
            height="500px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black"
        )
        
        # Add nodes with sizing based on degree centrality
        degrees = dict(graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        
        for node in graph.nodes(data=True):
            node_id, node_data = node
            # Size nodes based on their degree (number of connections)
            node_size = 10 + (degrees.get(node_id, 0) / max_degree) * 30
            
            # Determine node type and color
            if node_data.get('node_type') == 'author':
                color = '#3498db'  # Blue for authors
                label = node_data.get('label', node_id)
                title = f"Author: {label}<br>Connections: {degrees.get(node_id, 0)}"
            elif node_data.get('node_type') == 'subreddit':
                color = '#e67e22'  # Orange for subreddits
                label = node_data.get('label', node_id)
                title = f"Subreddit: {label}<br>Authors: {degrees.get(node_id, 0)}"
            else:
                color = '#95a5a6'  # Gray for unknown
                label = str(node_id)
                title = f"Node: {label}<br>Connections: {degrees.get(node_id, 0)}"
            
            net.add_node(
                node_id,
                label=label,
                size=node_size,
                title=title,
                color=color
            )
        
        # Add edges with thickness based on weight
        for edge in graph.edges(data=True):
            source, target, data = edge
            weight = data.get('weight', 1)
            post_count = data.get('post_count', weight)
            
            # Create edge title with connection information
            edge_title = f"Posts: {post_count}"
            
            net.add_edge(
                source,
                target,
                width=min(weight, 10),  # Cap width for readability
                title=edge_title
            )
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          }
        }
        """)
        
        # Generate HTML
        try:
            # Method 1: Try using PyVis's built-in HTML generation
            try:
                # Use a unique filename to avoid conflicts
                temp_filename = f"network_{uuid.uuid4().hex}.html"
                temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                
                # Save the graph
                net.save_graph(temp_path)
                
                # Read the generated HTML
                html_content = ""
                with open(temp_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Clean up temporary file with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        break
                    except (OSError, PermissionError):
                        if attempt < max_retries - 1:
                            time.sleep(0.1)  # Brief delay before retry
                        # If all retries fail, just continue (file will be cleaned up by system)
                
                return html_content
                
            except Exception:
                # Method 2: Fallback - generate simple HTML manually
                return self._generate_fallback_network_html(graph)
                
        except Exception as e:
            return f"<div style='text-align: center; padding: 50px;'>Error generating network visualization: {str(e)}</div>"
    
    def _generate_fallback_network_html(self, graph: nx.Graph) -> str:
        """
        Generate a simple fallback network visualization when PyVis fails.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            HTML string with basic network information
        """
        if graph.number_of_nodes() == 0:
            return "<div style='text-align: center; padding: 50px;'>No network data available</div>"
        
        # Count node types
        authors = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'author']
        subreddits = [n for n, d in graph.nodes(data=True) if d.get('node_type') == 'subreddit']
        
        # Generate simple HTML table
        html = f"""
        <div style='padding: 20px; font-family: Arial, sans-serif;'>
            <h3>Network Overview</h3>
            <p><strong>Authors:</strong> {len(authors)} | <strong>Subreddits:</strong> {len(subreddits)} | <strong>Connections:</strong> {graph.number_of_edges()}</p>
            
            <div style='display: flex; gap: 20px;'>
                <div style='flex: 1;'>
                    <h4>👤 Top Authors</h4>
                    <ul>
        """
        
        # Add top authors by degree
        author_degrees = [(n, graph.degree(n)) for n in authors]
        author_degrees.sort(key=lambda x: x[1], reverse=True)
        
        for author, degree in author_degrees[:5]:
            author_name = graph.nodes[author].get('label', author)
            html += f"<li>{author_name} ({degree} subreddits)</li>"
        
        html += """
                    </ul>
                </div>
                <div style='flex: 1;'>
                    <h4>📋 Top Subreddits</h4>
                    <ul>
        """
        
        # Add top subreddits by degree
        subreddit_degrees = [(n, graph.degree(n)) for n in subreddits]
        subreddit_degrees.sort(key=lambda x: x[1], reverse=True)
        
        for subreddit, degree in subreddit_degrees[:5]:
            subreddit_name = graph.nodes[subreddit].get('label', subreddit)
            html += f"<li>{subreddit_name} ({degree} authors)</li>"
        
        html += """
                    </ul>
                </div>
            </div>
            
            <p style='margin-top: 20px; font-style: italic; color: #666;'>
                Interactive visualization temporarily unavailable. Network data shown above.
            </p>
        </div>
        """
        
        return html
    
    def create_summary_metrics_cards(self, stats: Dict[str, Any]) -> None:
        """
        Create metric cards for summary statistics using Streamlit.
        
        Args:
            stats: Dictionary containing summary statistics
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Posts",
                value=f"{stats.get('total_posts', 0):,}"
            )
        
        with col2:
            st.metric(
                label="Unique Authors",
                value=f"{stats.get('unique_authors', 0):,}"
            )
        
        with col3:
            st.metric(
                label="Avg Score",
                value=f"{stats.get('avg_score', 0):.1f}"
            )
        
        with col4:
            st.metric(
                label="Total Comments",
                value=f"{stats.get('total_comments', 0):,}"
            )
        
        # Additional info
        st.info(f"📅 **Date Range:** {stats.get('date_range', 'N/A')}")


def create_top_keywords_chart(keywords: List[tuple], title: str = "Top Keywords") -> go.Figure:
    """
    Create a horizontal bar chart for top keywords.
    
    Args:
        keywords: List of (keyword, count) tuples
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not keywords:
        fig = go.Figure()
        fig.add_annotation(
            text="No keywords found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title=title, height=300)
        return fig
    
    words, counts = zip(*keywords)
    
    fig = go.Figure(data=[
        go.Bar(
            x=counts,
            y=words,
            orientation='h',
            marker_color=px.colors.qualitative.Set3[0]
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Frequency",
        yaxis_title="Keywords",
        height=max(300, len(keywords) * 25),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig