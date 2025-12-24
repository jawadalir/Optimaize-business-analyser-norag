import streamlit as st
import json
import os
from datetime import datetime
import base64
from project_selector import ProjectSelector
from ba_agent import BusinessAnalystAgent
from document_generator import DocumentGenerator

# Page configuration
st.set_page_config(
    page_title="Business Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-like chat
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background-color: #f5f5f5;
    }
    
    /* Chat containers */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        max-width: 80%;
    }
    
    .chat-message.user {
        background-color: #e3f2fd;
        margin-left: auto;
        border-bottom-right-radius: 0.2rem;
    }
    
    .chat-message.assistant {
        background-color: #f5f5f5;
        margin-right: auto;
        border-bottom-left-radius: 0.2rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Message header */
    .message-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .message-header.user {
        color: #1976d2;
    }
    
    .message-header.assistant {
        color: #388e3c;
    }
    
    /* Timestamp */
    .message-timestamp {
        font-size: 0.8rem;
        color: #757575;
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    /* Chat input at bottom */
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background-color: white;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        z-index: 100;
    }
    
    /* Project selector */
    .project-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Response style pills */
    .style-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .style-pill.active {
        background-color: #4caf50;
        color: white;
        font-weight: bold;
    }
    
    .style-pill.inactive {
        background-color: #e0e0e0;
        color: #666;
        cursor: pointer;
    }
    
    /* Analysis type badge */
    .analysis-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
        background-color: #bbdefb;
        color: #1565c0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'agent' not in st.session_state:
        st.session_state.agent = BusinessAnalystAgent()
    
    if 'project_selector' not in st.session_state:
        st.session_state.project_selector = ProjectSelector()
    
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    
    if 'current_project_name' not in st.session_state:
        st.session_state.current_project_name = ""
    
    # Chat settings
    if 'response_style' not in st.session_state:
        st.session_state.response_style = "detailed"  # "simple" or "detailed"
    
    if 'response_scope' not in st.session_state:
        st.session_state.response_scope = "specific"  # "specific" or "general"
    
    # Chat input
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    # Keep track of current chat view
    if 'current_chat_view' not in st.session_state:
        st.session_state.current_chat_view = "chat"

init_session_state()

# Helper functions for chat display
def display_chat_message(role, content, timestamp=None, analysis_type=None):
    """Display a chat message in ChatGPT-like style"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user">
            <div class="message-header user">
                👤 You
            </div>
            <div>{content}</div>
            {f'<div class="message-timestamp">{timestamp}</div>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant">
            <div class="message-header assistant">
                🤖 Business Analyst
                {f'<span class="analysis-badge">{analysis_type}</span>' if analysis_type else ''}
            </div>
            <div>{content}</div>
            {f'<div class="message-timestamp">{timestamp}</div>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)

def get_project_history_display(project_name):
    """Get formatted chat history for display"""
    history = st.session_state.agent.get_project_history(project_name)
    display_history = []
    
    for entry in history[-20:]:  # Show last 20 messages
        display_history.append({
            "role": "user",
            "content": entry["user_input"],
            "timestamp": entry["timestamp"],
            "analysis_type": entry.get("analysis_type", "general")
        })
        display_history.append({
            "role": "assistant",
            "content": entry["agent_response"],
            "timestamp": entry["timestamp"],
            "analysis_type": entry.get("analysis_type", "general"),
            "response_style": entry.get("response_style", "detailed")
        })
    
    return display_history

# Header
st.markdown('<h1 style="text-align: center; color: #1976d2;">🤖 Business Analyst Agent</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">AI-powered business analysis with ChatGPT-like interface</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📋 Project Management")
    
    # Get all projects
    projects = st.session_state.project_selector.get_all_projects()
    project_names = [p["product_name"] for p in projects]
    
    # Project selection with visual indicator
    selected_project_name = st.selectbox(
        "Select a project:",
        ["-- Select a Project --"] + project_names,
        index=0
    )
    
    # Handle project selection
    if selected_project_name != "-- Select a Project --":
        if selected_project_name != st.session_state.current_project_name:
            st.session_state.selected_project = st.session_state.project_selector.get_project_by_name(selected_project_name)
            st.session_state.current_project_name = selected_project_name
            st.rerun()
    
    if st.session_state.selected_project:
        project = st.session_state.selected_project
        
        st.markdown(f"""
        <div class="project-selector">
            <h3>🎯 {project['product_name']}</h3>
            <p>Active Analysis Project</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Project stats
        history = st.session_state.agent.get_project_history(project['product_name'])
        st.metric("Chat Messages", len(history))
        
        st.markdown("---")
        
        # Response Style Selection
        st.markdown("### ⚙️ Response Settings")
        
        # Style selection
        col1, col2 = st.columns(2)
        with col1:
            style = st.radio(
                "Response Style:",
                ["Detailed", "Simple"],
                index=0 if st.session_state.response_style == "detailed" else 1,
                key="style_radio"
            )
            st.session_state.response_style = style.lower()
        
        with col2:
            scope = st.radio(
                "Response Scope:",
                ["Specific", "General"],
                index=0 if st.session_state.response_scope == "specific" else 1,
                key="scope_radio"
            )
            st.session_state.response_scope = scope.lower()
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📋 Requirements Analysis", use_container_width=True):
            st.session_state.user_input = "Perform comprehensive requirements analysis"
            st.rerun()
        
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            st.session_state.user_input = "Perform risk assessment"
            st.rerun()
        
        if st.button("👥 Stakeholder Analysis", use_container_width=True):
            st.session_state.user_input = "Analyze stakeholders"
            st.rerun()
        
        st.markdown("---")
        
        # Document Generation
        st.markdown("### 📄 Generate Documents")
        
        doc_type = st.selectbox(
            "Document Type:",
            ["BRD", "User Stories", "Risk Register", "Stakeholder Matrix", "SWOT Analysis"]
        )
        
        doc_map = {
            "BRD": "brd",
            "User Stories": "user_stories",
            "Risk Register": "risk_register",
            "Stakeholder Matrix": "stakeholder_matrix",
            "SWOT Analysis": "swot"
        }
        
        detail_level = st.radio("Detail Level:", ["Detailed", "Simple"], horizontal=True)
        
        if st.button("Generate Document", use_container_width=True, type="secondary"):
            with st.spinner(f"Generating {doc_type}..."):
                response = st.session_state.agent.generate_document(
                    project,
                    doc_map[doc_type],
                    detail_level.lower()
                )
                
                # Add to chat
                st.session_state.agent.add_to_history(
                    project['product_name'],
                    f"Generate {doc_type} ({detail_level})",
                    response,
                    f"document_{doc_map[doc_type]}",
                    detail_level.lower()
                )
                st.rerun()
        
        st.markdown("---")
        
        # Chat Management
        st.markdown("### 💬 Chat Management")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.agent.clear_project_history(project['product_name'])
            st.success(f"Chat history cleared for {project['product_name']}")
            st.rerun()
        
        if st.button("📥 Export Chat", use_container_width=True):
            # Export functionality
            history = st.session_state.agent.get_project_history(project['product_name'])
            export_data = {
                "project": project['product_name'],
                "export_date": datetime.now().isoformat(),
                "messages": history
            }
            
            json_str = json.dumps(export_data, indent=2)
            b64 = base64.b64encode(json_str.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="{project["product_name"]}_chat_export.json">Download Chat Export</a>'
            st.markdown(href, unsafe_allow_html=True)

# Main Content Area
if not st.session_state.selected_project:
    # Welcome screen when no project selected
    st.markdown("""
    <div style="text-align: center; padding: 4rem;">
        <h2>👋 Welcome to Business Analyst Agent</h2>
        <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
            Select a project from the sidebar to start your analysis
        </p>
        
        <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 3rem;">
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 10px; width: 200px;">
                <div style="font-size: 2rem;">📋</div>
                <h4>Requirements Analysis</h4>
                <p>Elicit and document project requirements</p>
            </div>
            
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 10px; width: 200px;">
                <div style="font-size: 2rem;">⚠️</div>
                <h4>Risk Assessment</h4>
                <p>Identify and mitigate project risks</p>
            </div>
            
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 10px; width: 200px;">
                <div style="font-size: 2rem;">👥</div>
                <h4>Stakeholder Analysis</h4>
                <p>Map and engage project stakeholders</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show available projects
    st.markdown("### Available Projects")
    for project in projects:
        with st.expander(f"📁 {project['product_name']}"):
            sections = project.get('sections', {})
            one_line = sections.get('One-Line Summary', sections.get('Solution', ''))
            if isinstance(one_line, str) and len(one_line) > 200:
                one_line = one_line[:200] + "..."
            st.write(one_line)
            if st.button(f"Select {project['product_name']}", key=f"select_{project['product_name']}"):
                st.session_state.selected_project = project
                st.session_state.current_project_name = project['product_name']
                st.rerun()
else:
    # Project is selected - Show chat interface
    project = st.session_state.selected_project
    
    # Header with project info
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.markdown(f"### 💬 Chat: **{project['product_name']}**")
    with col2:
        # Style indicators
        style_pill = "🟢 Detailed" if st.session_state.response_style == "detailed" else "⚪ Simple"
        scope_pill = "🎯 Specific" if st.session_state.response_scope == "specific" else "🌐 General"
        st.markdown(f"<div style='display: flex; gap: 0.5rem;'><span class='style-pill active'>{style_pill}</span><span class='style-pill active'>{scope_pill}</span></div>", unsafe_allow_html=True)
    with col3:
        if st.button("🔄 New Chat", use_container_width=True):
            # Create a new chat within same project (just clear current view)
            st.session_state.user_input = ""
            st.rerun()
    
    # Display chat history for current project
    chat_history = get_project_history_display(project['product_name'])
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        if chat_history:
            for message in chat_history:
                display_chat_message(
                    message["role"],
                    message["content"],
                    message.get("timestamp"),
                    message.get("analysis_type")
                )
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #666;">
                <h3>💬 No messages yet</h3>
                <p>Start a conversation with your Business Analyst Agent!</p>
                <p>Try asking about requirements, risks, stakeholders, or use the quick actions in the sidebar.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input at bottom (fixed position)
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_area(
            "Your message:",
            value=st.session_state.user_input,
            placeholder=f"Ask about {project['product_name']}... (e.g., 'What are the key success metrics?', 'Analyze the market positioning', 'Identify stakeholders')",
            height=100,
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        send_button = st.button("🚀 Send", use_container_width=True, type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle send button
    if send_button and user_input.strip():
        with st.spinner("🤔 Analyzing..."):
            # Check if user is mentioning another project
            detected_project = st.session_state.project_selector.detect_project_from_input(user_input)
            
            if detected_project and detected_project['product_name'] != st.session_state.current_project_name:
                # Switch to detected project
                st.info(f"🔍 Detected reference to **{detected_project['product_name']}**. Switching project...")
                st.session_state.selected_project = detected_project
                st.session_state.current_project_name = detected_project['product_name']
                st.session_state.user_input = user_input
                st.rerun()
            
            # Get analysis with selected style and scope
            response = st.session_state.agent.analyze_with_options(
                project,
                user_input,
                response_style=st.session_state.response_style,
                scope=st.session_state.response_scope
            )
            
            # Clear input
            st.session_state.user_input = ""
            st.rerun()
    
    # Quick suggestions
    st.markdown("### 💡 Quick Suggestions")
    
    suggestion_cols = st.columns(4)
    
    suggestions = [
        ("What are the main business requirements?", "📋"),
        ("Identify key stakeholders and their interests", "👥"),
        ("What are the biggest implementation risks?", "⚠️"),
        ("Suggest measurable success metrics/KPIs", "📊")
    ]
    
    for idx, (suggestion, icon) in enumerate(suggestions):
        with suggestion_cols[idx]:
            if st.button(f"{icon} {suggestion[:30]}...", use_container_width=True, key=f"sugg_{idx}"):
                st.session_state.user_input = suggestion
                st.rerun()
    
    # Project tabs for additional views
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Project Details", "📈 Analytics", "🔄 Switch Project"])
    
    with tab1:
        # Display project details
        sections = project.get('sections', {})
        
        for section_name, section_content in sections.items():
            with st.expander(f"**{section_name}**", expanded=(section_name in ["Problem Statement", "Solution"])):
                st.write(section_content)
    
    with tab2:
        # Analytics dashboard
        history = st.session_state.agent.get_project_history(project['product_name'])
        
        if history:
            # Count analysis types
            from collections import Counter
            analysis_types = [h.get("analysis_type", "general") for h in history]
            type_counts = Counter(analysis_types)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Analysis Distribution")
                if type_counts:
                    import pandas as pd
                    type_df = pd.DataFrame({
                        'Type': list(type_counts.keys()),
                        'Count': list(type_counts.values())
                    })
                    st.bar_chart(type_df.set_index('Type'))
            
            with col2:
                st.markdown("#### 🕒 Recent Activity")
                for entry in history[-3:]:
                    st.markdown(f"""
                    **{entry['timestamp']}**
                    - **Q:** {entry['user_input'][:50]}...
                    - **Style:** {entry.get('response_style', 'detailed')}
                    """)
        else:
            st.info("No analytics data yet. Start chatting to see insights!")
    
    with tab3:
        # Project switching interface
        st.markdown("### 🔄 Switch Project")
        
        for proj in projects:
            if proj['product_name'] != project['product_name']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{proj['product_name']}**")
                    sections = proj.get('sections', {})
                    one_line = str(sections.get('One-Line Summary', sections.get('Solution', '')))[:100] + "..."
                    st.caption(one_line)
                with col2:
                    if st.button("Switch", key=f"switch_{proj['product_name']}"):
                        st.session_state.selected_project = proj
                        st.session_state.current_project_name = proj['product_name']
                        st.rerun()
                st.markdown("---")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Business Analyst Agent v2.0 • ChatGPT-like interface • Separate project chats</div>", unsafe_allow_html=True)