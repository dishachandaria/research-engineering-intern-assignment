"""
Analytics module for social media dashboard.
Provides aggregations, metrics, and data analysis functions.
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
from collections import Counter
import networkx as nx


class SocialMediaAnalytics:
    """Handles analytics and metrics calculation for social media data."""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
    
    def get_summary_stats(self, filtered_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate summary statistics for the filtered dataset.
        
        Args:
            filtered_data: Filtered DataFrame based on user selections
            
        Returns:
            Dictionary containing summary statistics
        """
        if filtered_data.empty:
            return {
                'total_posts': 0,
                'unique_authors': 0,
                'platforms': 0,
                'date_range': 'No data',
                'avg_score': 0,
                'total_comments': 0
            }
        
        stats = {
            'total_posts': len(filtered_data),
            'unique_authors': filtered_data['author'].nunique(),
            'platforms': filtered_data['platform'].nunique(),
            'avg_score': filtered_data['score'].mean(),
            'total_comments': filtered_data['num_comments'].sum()
        }
        
        # Date range
        if not filtered_data['created_at'].isna().all():
            min_date = filtered_data['created_at'].min().strftime('%Y-%m-%d')
            max_date = filtered_data['created_at'].max().strftime('%Y-%m-%d')
            stats['date_range'] = f"{min_date} to {max_date}"
        else:
            stats['date_range'] = 'No valid dates'
        
        return stats
    
    def get_time_series_data(self, filtered_data: pd.DataFrame, 
                           freq: str = 'D') -> pd.DataFrame:
        """
        Generate time series data for post volume over time.
        
        Args:
            filtered_data: Filtered DataFrame
            freq: Frequency for grouping ('D' for daily, 'H' for hourly, etc.)
            
        Returns:
            DataFrame with time series data
        """
        if filtered_data.empty or filtered_data['created_at'].isna().all():
            return pd.DataFrame(columns=['date', 'post_count'])
        
        # Group by time period
        time_series = (filtered_data.groupby(pd.Grouper(key='created_at', freq=freq))
                      .size()
                      .reset_index(name='post_count'))
        
        time_series['date'] = time_series['created_at']
        return time_series[['date', 'post_count']]
    
    def get_top_keywords(self, filtered_data: pd.DataFrame, 
                        top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Extract top keywords from posts for theme analysis.
        
        Args:
            filtered_data: Filtered DataFrame
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, count) tuples
        """
        if filtered_data.empty:
            return []
        
        # Combine all text
        all_text = ' '.join(filtered_data['combined_text'].fillna(''))
        
        # Simple keyword extraction (split on whitespace and punctuation)
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this',
            'that', 'these', 'those', 'are', 'was', 'were', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'shall', 'not', 'what',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'now', 'here',
            'there', 'then', 'them', 'they', 'their', 'his', 'her', 'its',
            'our', 'your', 'you', 'we', 'he', 'she', 'it', 'me', 'him',
            'us', 'my', 'mine', 'yours', 'ours', 'theirs'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count and return top keywords
        word_counts = Counter(filtered_words)
        return word_counts.most_common(top_n)
    
    def get_keyword_time_series(self, filtered_data: pd.DataFrame, 
                               keywords: List[str], freq: str = 'D') -> pd.DataFrame:
        """
        Generate time series data for specific keywords/themes.
        
        Args:
            filtered_data: Filtered DataFrame
            keywords: List of keywords to track
            freq: Frequency for grouping
            
        Returns:
            DataFrame with keyword time series data
        """
        if filtered_data.empty or not keywords:
            return pd.DataFrame()
        
        results = []
        
        for keyword in keywords:
            # Filter posts containing the keyword
            keyword_posts = filtered_data[
                filtered_data['combined_text'].str.contains(keyword.lower(), na=False)
            ]
            
            if not keyword_posts.empty:
                # Group by time period
                time_series = (keyword_posts.groupby(pd.Grouper(key='created_at', freq=freq))
                              .size()
                              .reset_index(name='count'))
                time_series['keyword'] = keyword
                results.append(time_series)
        
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame(columns=['created_at', 'count', 'keyword'])
    
    def get_top_contributors(self, filtered_data: pd.DataFrame, 
                           top_n: int = 10) -> pd.DataFrame:
        """
        Get top contributing authors by post count.
        
        Args:
            filtered_data: Filtered DataFrame
            top_n: Number of top contributors to return
            
        Returns:
            DataFrame with contributor statistics
        """
        if filtered_data.empty:
            return pd.DataFrame(columns=['author', 'post_count', 'percentage'])
        
        # Count posts per author
        author_counts = (filtered_data.groupby('author')
                        .agg({
                            'id': 'count',
                            'score': 'mean',
                            'num_comments': 'sum'
                        })
                        .reset_index())
        
        author_counts.columns = ['author', 'post_count', 'avg_score', 'total_comments']
        
        # Calculate percentage
        total_posts = len(filtered_data)
        author_counts['percentage'] = (author_counts['post_count'] / total_posts * 100).round(2)
        
        # Sort by post count and return top N
        return author_counts.sort_values('post_count', ascending=False).head(top_n)
    
    def build_top_author_subreddit_network(self, filtered_data: pd.DataFrame, 
                                          top_authors: int = 15, 
                                          top_subreddits: int = 10) -> nx.Graph:
        """
        Build a bipartite network graph showing top authors and their subreddit participation.
        
        Args:
            filtered_data: Filtered DataFrame
            top_authors: Number of top authors to include
            top_subreddits: Number of top subreddits to include
            
        Returns:
            NetworkX bipartite graph object
        """
        G = nx.Graph()
        
        if filtered_data.empty:
            return G
        
        # Get top authors by post count
        top_author_list = (filtered_data.groupby('author')
                          .size()
                          .sort_values(ascending=False)
                          .head(top_authors)
                          .index.tolist())
        
        # Get top subreddits by post count
        top_subreddit_list = (filtered_data.groupby('subreddit')
                             .size()
                             .sort_values(ascending=False)
                             .head(top_subreddits)
                             .index.tolist())
        
        # Filter data to only include top authors and subreddits
        filtered_top_data = filtered_data[
            (filtered_data['author'].isin(top_author_list)) &
            (filtered_data['subreddit'].isin(top_subreddit_list))
        ]
        
        if filtered_top_data.empty:
            return G
        
        # Count posts per author-subreddit combination
        author_subreddit_counts = (filtered_top_data.groupby(['author', 'subreddit'])
                                 .size()
                                 .reset_index(name='post_count'))
        
        # Only include connections with at least 1 post (automatic filtering)
        author_subreddit_counts = author_subreddit_counts[
            author_subreddit_counts['post_count'] >= 1
        ]
        
        # Add nodes and edges
        for _, row in author_subreddit_counts.iterrows():
            author = f"👤 {row['author']}"  # Prefix to distinguish authors
            subreddit = f"📋 r/{row['subreddit']}"  # Prefix to distinguish subreddits
            post_count = row['post_count']
            
            # Add nodes with attributes
            G.add_node(author, node_type='author', label=row['author'])
            G.add_node(subreddit, node_type='subreddit', label=f"r/{row['subreddit']}")
            
            # Add edge with weight based on post count
            G.add_edge(author, subreddit, weight=post_count, post_count=post_count)
        
        return G
    
    def get_weekly_posting_rhythm(self, filtered_data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze posting patterns by day of week.
        
        Args:
            filtered_data: Filtered DataFrame
            
        Returns:
            DataFrame with day of week posting patterns
        """
        if filtered_data.empty or filtered_data['created_at'].isna().all():
            return pd.DataFrame(columns=['day_of_week', 'post_count'])
        
        # Create day of week column if it doesn't exist
        df_copy = filtered_data.copy()
        df_copy['day_of_week'] = df_copy['created_at'].dt.day_name()
        
        # Group by day of week
        rhythm_data = (df_copy.groupby('day_of_week')
                      .size()
                      .reset_index(name='post_count'))
        
        # Ensure all days are represented in correct order
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Create complete data with all days
        complete_data = []
        for day in days_order:
            existing = rhythm_data[rhythm_data['day_of_week'] == day]
            if not existing.empty:
                complete_data.append({
                    'day_of_week': day,
                    'post_count': existing['post_count'].iloc[0]
                })
            else:
                complete_data.append({
                    'day_of_week': day,
                    'post_count': 0
                })
        
        return pd.DataFrame(complete_data)
    
    def get_network_stats(self, graph: nx.Graph) -> Dict[str, Any]:
        """
        Calculate network statistics.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Dictionary with network statistics
        """
        if graph.number_of_nodes() == 0:
            return {
                'nodes': 0,
                'edges': 0,
                'density': 0,
                'avg_clustering': 0,
                'connected_components': 0
            }
        
        stats = {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'density': nx.density(graph),
            'connected_components': nx.number_connected_components(graph)
        }
        
        # Calculate average clustering coefficient
        try:
            stats['avg_clustering'] = nx.average_clustering(graph)
        except:
            stats['avg_clustering'] = 0
        
        return stats


if __name__ == "__main__":
    # Test the analytics module
    from data_loader import load_and_preprocess_data
    
    print("Testing analytics module...")
    
    # Load test data
    df = load_and_preprocess_data()
    analytics = SocialMediaAnalytics(df)
    
    # Test summary stats
    stats = analytics.get_summary_stats(df)
    print(f"Summary stats: {stats}")
    
    # Test time series
    time_series = analytics.get_time_series_data(df)
    print(f"Time series shape: {time_series.shape}")
    
    # Test top keywords
    keywords = analytics.get_top_keywords(df, top_n=5)
    print(f"Top 5 keywords: {keywords}")
    
    # Test contributors
    contributors = analytics.get_top_contributors(df, top_n=5)
    print(f"Top contributors shape: {contributors.shape}")
    
    # Test network (small sample)
    sample_df = df.head(100)  # Use small sample for testing
    network = analytics.build_network_graph(sample_df, connection_type='subreddit')
    network_stats = analytics.get_network_stats(network)
    print(f"Network stats: {network_stats}")
    
    # Test weekly rhythm
    rhythm_data = analytics.get_weekly_posting_rhythm(df)
    print(f"Weekly rhythm data shape: {rhythm_data.shape}")
    print(f"Sample rhythm data:\n{rhythm_data.head()}")
    
    print("Analytics module test completed successfully!")