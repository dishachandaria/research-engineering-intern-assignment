"""
Gemini AI Chatbot for Social Media Analytics Dashboard
Provides AI-powered insights and answers questions about the data.
Redesigned with floating button and sidebar panel interface.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class GeminiChatbot:
    """AI chatbot powered by Google Gemini for social media analytics insights."""
    
    def __init__(self):
        self.model = None
        self.chat_session = None
        self.initialized = False
        
        # Load environment variables
        if DOTENV_AVAILABLE:
            load_dotenv()
        
        # Try to auto-initialize with environment variable
        self._try_auto_initialize()
    
    def _try_auto_initialize(self) -> bool:
        """
        Try to automatically initialize using environment variable.
        
        Returns:
            True if initialization successful, False otherwise
        """
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            return self.initialize(api_key)
        return False
        
    def initialize(self, api_key: str) -> bool:
        """
        Initialize the Gemini model with API key.
        
        Args:
            api_key: Google AI API key
            
        Returns:
            True if initialization successful, False otherwise
        """
        if not GEMINI_AVAILABLE:
            return False
            
        try:
            genai.configure(api_key=api_key)
            
            # Configure the model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=self._get_system_instruction()
            )
            
            self.chat_session = self.model.start_chat(history=[])
            self.initialized = True
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize Gemini: {str(e)}")
            return False
    
    def _get_system_instruction(self) -> str:
        """Get the system instruction for the AI assistant."""
        return """
You are an AI assistant specialized in social media analytics and investigative journalism. You help users analyze social media data, identify patterns, and generate insights.

Your capabilities include:
- Analyzing social media trends and patterns
- Explaining data visualizations and statistics
- Identifying potential coordination or amplification patterns
- Suggesting investigation strategies
- Interpreting network analysis results
- Providing context about social media behavior

Guidelines:
- Be helpful, accurate, and professional
- Focus on factual analysis rather than speculation
- Suggest actionable insights for investigation
- Explain technical concepts in accessible language
- Always consider ethical implications of social media analysis
- Respect privacy and avoid identifying specific individuals unless they are public figures
- Provide balanced perspectives on controversial topics

When analyzing data, consider:
- Temporal patterns (when activity occurs)
- Network structures (who connects to whom)
- Content themes and keywords
- Engagement patterns
- Potential coordination indicators
"""
    
    def generate_data_summary(self, summary_stats: Dict[str, Any], 
                            top_keywords: List[tuple], 
                            top_contributors: pd.DataFrame,
                            network_stats: Dict[str, Any]) -> str:
        """
        Generate a comprehensive data summary for the AI context.
        
        Args:
            summary_stats: Summary statistics dictionary
            top_keywords: List of (keyword, count) tuples
            top_contributors: DataFrame with contributor information
            network_stats: Network analysis statistics
            
        Returns:
            Formatted data summary string
        """
        # Format top keywords
        keywords_text = ", ".join([f"{kw} ({count})" for kw, count in top_keywords[:10]])
        
        # Format top contributors
        contributors_text = ""
        if not top_contributors.empty:
            contributors_text = ", ".join([
                f"{row['author']} ({row['post_count']} posts, {row['percentage']:.1f}%)"
                for _, row in top_contributors.head(5).iterrows()
            ])
        
        summary = f"""
CURRENT DATASET ANALYSIS:

OVERVIEW:
- Total Posts: {summary_stats.get('total_posts', 0):,}
- Unique Authors: {summary_stats.get('unique_authors', 0):,}
- Date Range: {summary_stats.get('date_range', 'N/A')}
- Average Score: {summary_stats.get('avg_score', 0):.1f}
- Total Comments: {summary_stats.get('total_comments', 0):,}

TOP KEYWORDS: {keywords_text}

TOP CONTRIBUTORS: {contributors_text}

NETWORK ANALYSIS:
- Nodes (Authors): {network_stats.get('nodes', 0)}
- Connections: {network_stats.get('edges', 0)}
- Network Density: {network_stats.get('density', 0):.3f}
- Connected Components: {network_stats.get('connected_components', 0)}

This data represents social media posts that have been filtered based on user selections. The user can ask questions about patterns, trends, or request analysis suggestions.
"""
        return summary
    
    def chat(self, user_message: str, data_context: str = "") -> str:
        """
        Send a message to the AI and get a response.
        
        Args:
            user_message: User's question or message
            data_context: Current data context/summary
            
        Returns:
            AI response string
        """
        if not self.initialized:
            return "❌ Chatbot not initialized. Please provide a valid Gemini API key."
        
        try:
            # Combine data context with user message
            full_message = f"""
DATA CONTEXT:
{data_context}

USER QUESTION:
{user_message}

Please provide insights, analysis, or suggestions based on the current data and user question.
"""
            
            response = self.chat_session.send_message(full_message)
            return response.text
            
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"
    
    def get_suggested_questions(self, data_context: str) -> List[str]:
        """
        Generate suggested questions based on the current data.
        
        Args:
            data_context: Current data summary
            
        Returns:
            List of suggested questions
        """
        if not self.initialized:
            return [
                "What patterns can you see in the posting times?",
                "Who are the most influential contributors?",
                "What topics are trending in this dataset?",
                "Are there any signs of coordinated activity?",
                "What investigation strategies would you recommend?"
            ]
        
        try:
            prompt = f"""
Based on this social media data summary, suggest 5 specific, actionable questions that would help with investigative analysis:

{data_context}

Return only the questions, one per line, without numbering or bullets.
"""
            
            response = self.chat_session.send_message(prompt)
            questions = [q.strip() for q in response.text.split('\n') if q.strip()]
            return questions[:5]  # Limit to 5 questions
            
        except Exception:
            # Fallback questions if AI fails
            return [
                "What patterns can you see in the posting times?",
                "Who are the most influential contributors?",
                "What topics are trending in this dataset?",
                "Are there any signs of coordinated activity?",
                "What investigation strategies would you recommend?"
            ]


def render_floating_chat_button():
    """Render floating chat button CSS and HTML."""
    st.markdown("""
    <style>
    .floating-chat-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        transition: all 0.3s ease;
        border: none;
        color: white;
        font-size: 24px;
        text-decoration: none;
    }
    
    .floating-chat-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    
    .chat-status-indicator {
        position: absolute;
        top: -2px;
        right: -2px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid white;
    }
    
    .status-ready { background: #2ecc71; }
    .status-setup { background: #f39c12; }
    .status-error { background: #e74c3c; }
    </style>
    """, unsafe_allow_html=True)


def render_chatbot_interface(chatbot: GeminiChatbot, 
                           summary_stats: Dict[str, Any],
                           top_keywords: List[tuple],
                           top_contributors: pd.DataFrame,
                           network_stats: Dict[str, Any]) -> None:
    """
    Render the floating chatbot button and handle sidebar panel.
    
    Args:
        chatbot: GeminiChatbot instance
        summary_stats: Current summary statistics
        top_keywords: Current top keywords
        top_contributors: Current top contributors
        network_stats: Current network statistics
    """
    # Initialize session state
    if "chat_panel_open" not in st.session_state:
        st.session_state.chat_panel_open = False
    
    # Render floating button CSS
    render_floating_chat_button()
    
    # Determine status indicator
    if chatbot.initialized:
        status_class = "status-ready"
        status_title = "AI Assistant Ready - Click to chat"
    else:
        status_class = "status-setup"
        status_title = "AI Assistant - Setup required"
    
    # Render floating button
    st.markdown(f"""
    <div class="floating-chat-btn" title="{status_title}" onclick="document.getElementById('chat_toggle_btn').click();">
        🤖
        <div class="chat-status-indicator {status_class}"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden button to handle clicks (Streamlit workaround)
    if st.button("", key="chat_toggle_btn", help="Toggle AI Assistant"):
        st.session_state.chat_panel_open = not st.session_state.chat_panel_open
    
    # Render sidebar panel if open
    if st.session_state.chat_panel_open:
        render_chat_sidebar(chatbot, summary_stats, top_keywords, top_contributors, network_stats)


def render_chat_sidebar(chatbot: GeminiChatbot, 
                       summary_stats: Dict[str, Any],
                       top_keywords: List[tuple],
                       top_contributors: pd.DataFrame,
                       network_stats: Dict[str, Any]) -> None:
    """Render the chat interface in the sidebar."""
    
    with st.sidebar:
        st.markdown("---")
        
        # Header with close button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("### 🤖 AI Assistant")
        with col2:
            if st.button("✕", key="close_chat", help="Close AI Assistant"):
                st.session_state.chat_panel_open = False
                st.rerun()
        
        # Status indicator
        if chatbot.initialized:
            st.success("✅ AI Ready")
        else:
            st.warning("⚠️ Setup Required")
            render_api_key_setup(chatbot)
            return
        
        # Generate data context
        data_context = chatbot.generate_data_summary(
            summary_stats, top_keywords, top_contributors, network_stats
        )
        
        # Chat interface
        st.markdown("**💬 Ask about your data:**")
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Quick questions
        st.markdown("**💡 Quick Questions:**")
        suggested_questions = chatbot.get_suggested_questions(data_context)
        
        for i, question in enumerate(suggested_questions[:3]):  # Show only 3 in sidebar
            if st.button(f"❓ {question[:40]}...", key=f"quick_{i}", help=question):
                with st.spinner("🤔 AI thinking..."):
                    ai_response = chatbot.chat(question, data_context)
                    st.session_state.chat_history.append({
                        "user": question,
                        "ai": ai_response,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
        
        # Custom question input
        user_question = st.text_input(
            "Your question:",
            placeholder="Ask about patterns, trends...",
            key="sidebar_chat_input"
        )
        
        if st.button("📤 Send", key="sidebar_send") and user_question:
            with st.spinner("🤔 AI thinking..."):
                ai_response = chatbot.chat(user_question, data_context)
                st.session_state.chat_history.append({
                    "user": user_question,
                    "ai": ai_response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                st.rerun()
        
        # Chat history (recent 3 conversations)
        if st.session_state.chat_history:
            st.markdown("**💬 Recent Conversations:**")
            
            recent_chats = st.session_state.chat_history[-3:]
            
            for chat in reversed(recent_chats):
                with st.expander(f"🙋 {chat['user'][:30]}... ({chat['timestamp']})"):
                    st.markdown(f"**You:** {chat['user']}")
                    st.markdown(f"**AI:** {chat['ai']}")
        
        # Clear chat button
        if st.session_state.chat_history and st.button("🗑️ Clear Chat", key="clear_sidebar_chat"):
            st.session_state.chat_history = []
            st.rerun()


def render_api_key_setup(chatbot: GeminiChatbot) -> None:
    """Render API key setup interface in sidebar."""
    
    st.markdown("**Setup Required:**")
    
    # Check if .env file exists
    env_exists = os.path.exists('.env')
    
    if env_exists:
        st.info("📁 `.env` file found! Restart dashboard if AI isn't working.")
    else:
        st.markdown("""
        **Quick Setup:**
        1. Get API key: [Google AI Studio](https://aistudio.google.com/app/apikey)
        2. Create `.env` file with: `GEMINI_API_KEY=your_key`
        3. Restart dashboard
        """)
        
        if st.button("📝 Create .env template", key="create_env_sidebar"):
            try:
                with open('.env', 'w') as f:
                    f.write('# Google Gemini API Key\n')
                    f.write('GEMINI_API_KEY=your_api_key_here\n')
                st.success("✅ `.env` created! Add your key and restart.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Temporary key input
    with st.expander("🔑 Temporary Key (This Session)"):
        api_key = st.text_input(
            "API Key:",
            type="password",
            placeholder="Paste key here...",
            key="temp_api_key"
        )
        
        if st.button("🚀 Initialize", key="init_temp_key") and api_key:
            with st.spinner("Initializing..."):
                if chatbot.initialize(api_key):
                    st.success("✅ AI Ready!")
                    st.rerun()
                else:
                    st.error("❌ Failed to initialize")


def is_gemini_available() -> bool:
    """Check if Gemini AI is available."""
    return GEMINI_AVAILABLE