"""
Data loading and preprocessing module for social media analytics dashboard.
Handles JSONL ingestion, cleaning, and normalization.
"""

import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urlparse


class SocialMediaDataLoader:
    """Handles loading and preprocessing of social media data from JSONL files."""
    
    def __init__(self):
        self.data = None
        self.processed_data = None
    
    def load_jsonl(self, file_path: str) -> pd.DataFrame:
        """
        Load JSONL file and convert to pandas DataFrame.
        
        Args:
            file_path: Path to the JSONL file
            
        Returns:
            DataFrame with loaded and cleaned data
        """
        posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        # Parse JSON line
                        post_data = json.loads(line.strip())
                        
                        # Extract Reddit post data from nested structure
                        if 'data' in post_data:
                            post = post_data['data']
                        else:
                            post = post_data
                        
                        # Extract relevant fields with safe handling
                        processed_post = self._extract_post_fields(post)
                        if processed_post:
                            posts.append(processed_post)
                            
                    except json.JSONDecodeError as e:
                        print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        print(f"Warning: Error processing line {line_num}: {e}")
                        continue
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        # Convert to DataFrame
        df = pd.DataFrame(posts)
        
        # Remove duplicates by ID
        if 'id' in df.columns:
            df = df.drop_duplicates(subset=['id'], keep='first')
        
        print(f"Loaded {len(df)} unique posts from {file_path}")
        return df
    
    def _extract_post_fields(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and normalize fields from a social media post.
        
        Args:
            post: Raw post data dictionary
            
        Returns:
            Dictionary with normalized fields or None if invalid
        """
        try:
            # Core fields
            extracted = {
                'id': post.get('id', ''),
                'title': post.get('title', ''),
                'text': post.get('selftext', ''),  # Reddit uses 'selftext'
                'author': post.get('author', 'unknown'),
                'platform': 'reddit',  # Since this is Reddit data
                'subreddit': post.get('subreddit', ''),
                'score': post.get('score', 0),
                'num_comments': post.get('num_comments', 0),
                'url': post.get('url', ''),
            }
            
            # Handle timestamp - Reddit uses created_utc
            timestamp = post.get('created_utc', post.get('created', None))
            if timestamp:
                try:
                    # Convert Unix timestamp to datetime
                    extracted['created_at'] = datetime.fromtimestamp(float(timestamp))
                except (ValueError, TypeError):
                    extracted['created_at'] = None
            else:
                extracted['created_at'] = None
            
            # Extract hashtags from title and text
            extracted['hashtags'] = self._extract_hashtags(
                extracted['title'] + ' ' + extracted['text']
            )
            
            # Extract domains from URLs
            extracted['domains'] = self._extract_domains([extracted['url']])
            
            # Extract mentions (Reddit uses u/username format)
            extracted['mentions'] = self._extract_mentions(
                extracted['title'] + ' ' + extracted['text']
            )
            
            return extracted
            
        except Exception as e:
            print(f"Warning: Error extracting fields from post: {e}")
            return None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        if not text:
            return []
        
        # Find hashtags (# followed by word characters)
        hashtags = re.findall(r'#(\w+)', text.lower())
        return list(set(hashtags))  # Remove duplicates
    
    def _extract_domains(self, urls: List[str]) -> List[str]:
        """Extract domains from list of URLs."""
        domains = []
        for url in urls:
            if url and isinstance(url, str):
                try:
                    parsed = urlparse(url)
                    if parsed.netloc:
                        # Remove www. prefix for consistency
                        domain = parsed.netloc.lower()
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        domains.append(domain)
                except Exception:
                    continue
        return list(set(domains))
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text (Reddit format: u/username)."""
        if not text:
            return []
        
        # Find Reddit-style mentions
        mentions = re.findall(r'u/(\w+)', text.lower())
        return list(set(mentions))
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply additional preprocessing to the loaded data.
        
        Args:
            df: Raw DataFrame from load_jsonl
            
        Returns:
            Preprocessed DataFrame
        """
        # Create a copy to avoid modifying original
        processed_df = df.copy()
        
        # Filter out posts without valid timestamps
        processed_df = processed_df.dropna(subset=['created_at'])
        
        # Add derived fields
        processed_df['date'] = processed_df['created_at'].dt.date
        processed_df['hour'] = processed_df['created_at'].dt.hour
        processed_df['day_of_week'] = processed_df['created_at'].dt.day_name()
        
        # Create combined text field for searching
        processed_df['combined_text'] = (
            processed_df['title'].fillna('') + ' ' + 
            processed_df['text'].fillna('')
        ).str.lower()
        
        # Convert list fields to string representation for display
        processed_df['hashtags_str'] = processed_df['hashtags'].apply(
            lambda x: ', '.join(x) if x else ''
        )
        processed_df['domains_str'] = processed_df['domains'].apply(
            lambda x: ', '.join(x) if x else ''
        )
        processed_df['mentions_str'] = processed_df['mentions'].apply(
            lambda x: ', '.join(x) if x else ''
        )
        
        print(f"Preprocessed {len(processed_df)} posts")
        return processed_df


def load_and_preprocess_data(file_path: str = "data/data.jsonl") -> pd.DataFrame:
    """
    Convenience function to load and preprocess data in one step.
    
    Args:
        file_path: Path to the JSONL data file
        
    Returns:
        Preprocessed DataFrame ready for analysis
    """
    loader = SocialMediaDataLoader()
    raw_data = loader.load_jsonl(file_path)
    processed_data = loader.preprocess_data(raw_data)
    return processed_data


if __name__ == "__main__":
    # Test the data loader
    df = load_and_preprocess_data()
    print(f"\nDataset shape: {df.shape}")
    print(f"Date range: {df['created_at'].min()} to {df['created_at'].max()}")
    print(f"Unique authors: {df['author'].nunique()}")
    print(f"Platforms: {df['platform'].unique()}")