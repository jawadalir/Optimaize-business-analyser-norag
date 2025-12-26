import streamlit as st
import json
import os
from datetime import datetime
import base64
from project_selector import ProjectSelector
from ba_agent import BusinessAnalystAgent
from document_generator import DocumentGenerator
st.cache_resource.clear()  # Clear ALL caches
st.cache_data.clear()

# Page configuration
st.set_page_config(
    page_title="Business Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better display
st.markdown("""
<style>
    /* Style for the latest response box */
    .latest-response-box {
        background-color: #f8f9fa;
        border: 2px solid #1976d2;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .latest-response-title {
        color: #1976d2;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 10px;
        border-bottom: 2px solid #e3f2fd;
        padding-bottom: 8px;
    }
    
    .response-content {
        font-size: 1rem;
        line-height: 1.6;
        color: #333;
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
        background-color: white;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    
    /* Style for chat history messages */
    .chat-history-message {
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        background-color: #f5f5f5;
        border-left: 4px solid #1976d2;
    }
    
    .chat-history-user {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    
    .chat-history-assistant {
        background-color: #f1f8e9;
        border-left-color: #4caf50;
    }
    
    /* Style for timestamp */
    .timestamp {
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 5px;
    }
    
    /* Style for suggestions */
    .suggestion-button {
        margin: 5px 0;
    }
    
    /* Style pills for settings */
    .style-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        background-color: #4caf50;
        color: white;
        font-weight: bold;
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
        st.session_state.response_style = "detailed"
    
    if 'response_scope' not in st.session_state:
        st.session_state.response_scope = "specific"
    
    # NEW: Strict mode setting
    if 'strict_mode' not in st.session_state:
        st.session_state.strict_mode = False
    
    # Chat input
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    # Auto-send flag for suggestions
    if 'auto_send' not in st.session_state:
        st.session_state.auto_send = False
    
    # Show/hide chat history
    if 'show_chat_history' not in st.session_state:
        st.session_state.show_chat_history = False
    
    # Store messages for current session
    if 'session_messages' not in st.session_state:
        st.session_state.session_messages = {}
    
    # Store latest response
    if 'latest_response' not in st.session_state:
        st.session_state.latest_response = ""
    
    # NEW: Store generated document for download
    if 'generated_document' not in st.session_state:
        st.session_state.generated_document = None

init_session_state()

# Function to clean response text
def clean_response_text(text):
    """Remove unwanted formatting and extract clean text"""
    if not text:
        return ""
    
    # Remove markdown headers
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove markdown headers
        if line.startswith('# '):
            line = line[2:].strip()
        elif line.startswith('## '):
            line = line[3:].strip()
        elif line.startswith('### '):
            line = line[4:].strip()
        
        # Remove HTML tags if any
        import re
        line = re.sub(r'<[^>]+>', '', line)
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

# Function to get or create session messages for a project
def get_session_messages(project_name):
    """Get messages for current session"""
    if project_name not in st.session_state.session_messages:
        st.session_state.session_messages[project_name] = []
    return st.session_state.session_messages[project_name]

# Function to add message to session
def add_to_session_messages(project_name, role, content, timestamp=None):
    """Add message to session messages"""
    messages = get_session_messages(project_name)
    messages.append({
        "role": role,
        "content": clean_response_text(content),
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # Keep only last 20 messages in session
    st.session_state.session_messages[project_name] = messages[-20:]

# Header
st.title("🤖 Business Analyst Agent")
st.markdown("AI-powered business analysis for your projects")

# Sidebar
with st.sidebar:
    st.markdown("## 📋 Project Management")
    
    # Get all projects
    projects = st.session_state.project_selector.get_all_projects()
    project_names = [p["product_name"] for p in projects]
    
    # Project selection
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
            st.session_state.user_input = ""
            st.rerun()
    
    if st.session_state.selected_project:
        project = st.session_state.selected_project
        
        st.markdown(f"### 🎯 {project['product_name']}")
        
        # Get actual chat history from agent
        actual_history = st.session_state.agent.get_project_history(project['product_name'])
        st.metric("Total Messages", len(actual_history))
        
        st.markdown("---")
        
        # Response Settings
        st.markdown("### ⚙️ Response Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            style = st.radio(
                "Style:",
                ["Detailed", "Simple"],
                index=0 if st.session_state.response_style == "detailed" else 1,
                key="style_radio"
            )
            st.session_state.response_style = style.lower()
        
        with col2:
            scope = st.radio(
                "Scope:",
                ["Specific", "General"],
                index=0 if st.session_state.response_scope == "specific" else 1,
                key="scope_radio"
            )
            st.session_state.response_scope = scope.lower()
        
        # NEW: Response Mode
        st.markdown("### 🎯 Response Mode")
        col3, col4 = st.columns(2)
        with col3:
            strict_mode = st.checkbox(
                "Strict Mode",
                value=st.session_state.strict_mode,
                help="In strict mode, the agent only answers exactly what's asked, no extra information"
            )
            st.session_state.strict_mode = strict_mode
        
        with col4:
            # Show current memory count
            if st.session_state.selected_project:
                memories = st.session_state.agent.get_all_project_memories(
                    st.session_state.current_project_name
                )
                st.metric("Stored Facts", len(memories))
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📋 Requirements", use_container_width=True):
            st.session_state.user_input = "Perform comprehensive requirements analysis"
            st.session_state.auto_send = True
            st.rerun()
        
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            st.session_state.user_input = "Perform risk assessment"
            st.session_state.auto_send = True
            st.rerun()
        
        if st.button("👥 Stakeholders", use_container_width=True):
            st.session_state.user_input = "Analyze stakeholders"
            st.session_state.auto_send = True
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
        
        # Create two columns for generate and download buttons
        col_gen, col_dl = st.columns(2)
        
        with col_gen:
            if st.button("Generate Document", use_container_width=True):
                st.session_state.user_input = f"Generate {doc_type} document"
                st.session_state.auto_send = True
                st.rerun()
        
        with col_dl:
            # Download button for generated document
            if st.session_state.generated_document and st.session_state.generated_document['project'] == project['product_name']:
                doc_data = st.session_state.generated_document
                
                # Format document for download
                doc_content = f"""
# {doc_data['type']} - {project['product_name']}
**Generated:** {doc_data['timestamp']}
**Author:** Business Analyst Agent

---

{doc_data['content']}

---
*Document generated by Business Analyst Agent*
"""
                
                # Create download button
                st.download_button(
                    label="📥 Download",
                    data=doc_content,
                    file_name=f"{project['product_name'].replace(' ', '_')}_{doc_type.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"download_{doc_type}"
                )
            else:
                st.button("📥 Download", 
                         disabled=True, 
                         help="Generate a document first",
                         use_container_width=True,
                         key=f"disabled_download_{doc_type}")
        
        st.markdown("---")
        
        # Chat Management
        st.markdown("### 💬 Chat Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear History", use_container_width=True):
                # Clear both agent history and session messages
                st.session_state.agent.clear_project_history(project['product_name'])
                if project['product_name'] in st.session_state.session_messages:
                    st.session_state.session_messages[project['product_name']] = []
                st.session_state.latest_response = ""
                st.session_state.generated_document = None  # Clear generated document
                st.success(f"Chat history cleared for {project['product_name']}")
                st.rerun()
        
        with col2:
            # Toggle chat history visibility
            toggle_text = "📜 Show History" if not st.session_state.show_chat_history else "📜 Hide History"
            if st.button(toggle_text, use_container_width=True):
                st.session_state.show_chat_history = not st.session_state.show_chat_history
                st.rerun()

# Main Content Area
if not st.session_state.selected_project:
    # Welcome screen
    st.info("👈 Select a project from the sidebar to begin analysis")
    
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
    # Project is selected
    project = st.session_state.selected_project
    
    # Project header with strict mode indicator
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.markdown(f"### 💬 Chat: **{project['product_name']}**")
    with col2:
        # Style indicators with strict mode
        style_pill = "🟢 Detailed" if st.session_state.response_style == "detailed" else "⚪ Simple"
        scope_pill = "🎯 Specific" if st.session_state.response_scope == "specific" else "🌐 General"
        strict_pill = "🎯 Strict" if st.session_state.strict_mode else "⚪ Normal"
        st.markdown(
            f"<div style='display: flex; gap: 0.5rem; flex-wrap: wrap;'>"
            f"<span class='style-pill active'>{style_pill}</span>"
            f"<span class='style-pill active'>{scope_pill}</span>"
            f"<span class='style-pill active'>{strict_pill}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get session messages for this project
    session_messages = get_session_messages(project['product_name'])
    
    # --- QUICK SUGGESTIONS (ABOVE INPUT) ---
    st.markdown("### 💡 Quick Suggestions")
    
    suggestions = [
        ("What are the main business requirements?", "📋"),
        ("Identify key stakeholders and their interests", "👥"),
        ("What are the biggest implementation risks?", "⚠️"),
        ("Suggest measurable success metrics/KPIs", "📊")
    ]
    
    cols = st.columns(4)
    for idx, (suggestion, icon) in enumerate(suggestions):
        with cols[idx]:
            if st.button(f"{icon} {suggestion[:18]}...", use_container_width=True, key=f"sugg_{idx}"):
                st.session_state.user_input = suggestion
                st.session_state.auto_send = True
                st.rerun()
    
    # --- CHAT INPUT (TOP SECTION) ---
    st.markdown("### 💬 Your Question")
    
    # Handle auto-send from suggestions
    if st.session_state.auto_send and st.session_state.user_input:
        with st.spinner("🤔 Analyzing..."):
            # Add user message to session
            add_to_session_messages(project['product_name'], "user", st.session_state.user_input)
            
            # Check if this is a document generation request
            is_document_request = "generate" in st.session_state.user_input.lower() and "document" in st.session_state.user_input.lower()
            
            if is_document_request:
                # Extract document type from request
                doc_type = None
                doc_map = {
                    "BRD": "brd",
                    "User Stories": "user_stories",
                    "Risk Register": "risk_register",
                    "Stakeholder Matrix": "stakeholder_matrix",
                    "SWOT Analysis": "swot"
                }
                
                for doc_name, doc_key in doc_map.items():
                    if doc_name.lower() in st.session_state.user_input.lower():
                        doc_type = doc_name
                        # Generate document
                        response = st.session_state.agent.generate_document(
                            project,
                            doc_key,
                            "detailed"
                        )
                        
                        # Store generated document for download
                        st.session_state.generated_document = {
                            "content": response,
                            "type": doc_type,
                            "project": project['product_name'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        break
                
                if not doc_type:
                    # If document type not found, do regular analysis
                    response = st.session_state.agent.analyze_with_options(
                        project,
                        st.session_state.user_input,
                        response_style=st.session_state.response_style,
                        scope=st.session_state.response_scope,
                        strict_mode=st.session_state.strict_mode
                    )
            else:
                # Regular analysis
                response = st.session_state.agent.analyze_with_options(
                    project,
                    st.session_state.user_input,
                    response_style=st.session_state.response_style,
                    scope=st.session_state.response_scope,
                    strict_mode=st.session_state.strict_mode
                )
            
            # Add assistant response to session
            add_to_session_messages(project['product_name'], "assistant", response)
            
            # Store latest response
            st.session_state.latest_response = clean_response_text(response)
            
            # Clear auto-send flag
            st.session_state.auto_send = False
            st.session_state.user_input = ""
            st.rerun()
    
    # Input field
    user_input = st.text_area(
        "Type your question:",
        value=st.session_state.user_input,
        placeholder=f"Ask about {project['product_name']}...",
        height=80,
        key="chat_input",
        label_visibility="collapsed"
    )
    
    # Send button
    col1, col2 = st.columns([4, 1])
    with col1:
        pass
    with col2:
        send_button = st.button("🚀 Send", use_container_width=True, type="primary")
    
    # Handle send button
    if send_button and user_input.strip():
        with st.spinner("🤔 Analyzing..."):
            # Check if user is mentioning another project
            detected_project = st.session_state.project_selector.detect_project_from_input(user_input)
            
            if detected_project and detected_project['product_name'] != st.session_state.current_project_name:
                # Switch to detected project
                st.info(f"🔍 Switching to: **{detected_project['product_name']}**")
                st.session_state.selected_project = detected_project
                st.session_state.current_project_name = detected_project['product_name']
                st.session_state.user_input = user_input
                st.rerun()
            
            # Add user message to session
            add_to_session_messages(project['product_name'], "user", user_input)
            
            # Check if this is a document generation request
            is_document_request = "generate" in user_input.lower() and "document" in user_input.lower()
            
            if is_document_request:
                # Extract document type from request
                doc_type = None
                doc_map = {
                    "BRD": "brd",
                    "User Stories": "user_stories",
                    "Risk Register": "risk_register",
                    "Stakeholder Matrix": "stakeholder_matrix",
                    "SWOT Analysis": "swot"
                }
                
                for doc_name, doc_key in doc_map.items():
                    if doc_name.lower() in user_input.lower():
                        doc_type = doc_name
                        # Generate document
                        response = st.session_state.agent.generate_document(
                            project,
                            doc_key,
                            "detailed"
                        )
                        
                        # Store generated document for download
                        st.session_state.generated_document = {
                            "content": response,
                            "type": doc_type,
                            "project": project['product_name'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        break
                
                if not doc_type:
                    # If document type not found, do regular analysis
                    response = st.session_state.agent.analyze_with_options(
                        project,
                        user_input,
                        response_style=st.session_state.response_style,
                        scope=st.session_state.response_scope,
                        strict_mode=st.session_state.strict_mode
                    )
            else:
                # Regular analysis
                response = st.session_state.agent.analyze_with_options(
                    project,
                    user_input,
                    response_style=st.session_state.response_style,
                    scope=st.session_state.response_scope,
                    strict_mode=st.session_state.strict_mode
                )
            
            # Add assistant response to session
            add_to_session_messages(project['product_name'], "assistant", response)
            
            # Store latest response
            st.session_state.latest_response = clean_response_text(response)
            
            # Clear input
            st.session_state.user_input = ""
            st.rerun()
    
    # Divider
    st.markdown("---")
    
    # --- LATEST RESPONSE (BOLD AND CLEAR) ---
    if st.session_state.latest_response or session_messages:
        st.markdown("### 📋 **Latest Response**")
        
        # Get the latest assistant response
        latest_response = st.session_state.latest_response
        if not latest_response and session_messages:
            # Find the latest assistant message
            assistant_messages = [m for m in session_messages if m["role"] == "assistant"]
            if assistant_messages:
                latest_response = assistant_messages[-1]["content"]
        
        if latest_response:
            # Display in a styled box with bold, clear text
            st.markdown(f"""
            <div class="latest-response-box">
                <div class="latest-response-title">📋 Business Analyst Response</div>
                <div class="response-content">
                    <strong>{latest_response[:500]}</strong>
                    {latest_response[500:] if len(latest_response) > 500 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show timestamp for latest response
            if session_messages and session_messages[-1].get("timestamp"):
                st.caption(f"🕒 Generated: {session_messages[-1]['timestamp']}")
    
    # --- DOCUMENT DOWNLOAD SECTION (only if document was generated) ---
    if st.session_state.generated_document and st.session_state.generated_document['project'] == project['product_name']:
        st.markdown("---")
        st.markdown("### 📄 Generated Document")
        
        doc_data = st.session_state.generated_document
        
        # Display document info
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Document Type", doc_data['type'])
        with col_info2:
            st.metric("Project", doc_data['project'])
        with col_info3:
            st.metric("Generated", doc_data['timestamp'][11:16])
        
        # Document preview
        with st.expander("📋 Preview Document", expanded=False):
            preview_text = doc_data['content'][:1500]
            if len(doc_data['content']) > 1500:
                preview_text += "\n\n... [Document continues - Download to view full document]"
            st.markdown(preview_text)
        
        # Download options
        st.markdown("#### 📥 Download Options")
        
        col_md, col_txt = st.columns(2)
        
        with col_md:
            # Markdown format
            doc_content_md = f"""
# {doc_data['type']} - {project['product_name']}
**Generated:** {doc_data['timestamp']}
**Author:** Business Analyst Agent

---

{doc_data['content']}

---
*Document generated by Business Analyst Agent*
"""
            
            st.download_button(
                label="📄 Download as Markdown (.md)",
                data=doc_content_md,
                file_name=f"{project['product_name'].replace(' ', '_')}_{doc_data['type'].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_md_main"
            )
        
        with col_txt:
            # Plain text format
            import re
            # Clean markdown formatting
            clean_content = re.sub(r'#+\s*', '', doc_data['content'])  # Remove headers
            clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)  # Remove bold
            clean_content = re.sub(r'\*(.*?)\*', r'\1', clean_content)  # Remove italic
            
            doc_content_txt = f"""
{doc_data['type']} - {project['product_name']}
Generated: {doc_data['timestamp']}
Author: Business Analyst Agent

{clean_content}

---
Document generated by Business Analyst Agent
"""
            
            st.download_button(
                label="📝 Download as Text (.txt)",
                data=doc_content_txt,
                file_name=f"{project['product_name'].replace(' ', '_')}_{doc_data['type'].replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_txt_main"
            )
    
    # --- CHAT HISTORY (HIDDEN BY DEFAULT) ---
    if st.session_state.show_chat_history and len(session_messages) > 0:
        st.markdown("---")
        st.markdown("### 📜 Chat History")
        
        # Show all messages except the latest (which is already displayed above)
        history_messages = session_messages[:-1] if len(session_messages) > 1 else []
        
        if history_messages:
            # Reverse so newest appear at top
            history_messages_reversed = list(reversed(history_messages))
            
            for msg in history_messages_reversed:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-history-message chat-history-user">
                        <strong>👤 You:</strong> {msg['content'][:150]}{'...' if len(msg['content']) > 150 else ''}
                        <div class="timestamp">{msg.get('timestamp', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-history-message chat-history-assistant">
                        <strong>🤖 Business Analyst:</strong> {msg['content'][:150]}{'...' if len(msg['content']) > 150 else ''}
                        <div class="timestamp">{msg.get('timestamp', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show full message in expander
                with st.expander("View full message"):
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**Business Analyst:** {msg['content']}")
        else:
            st.info("No previous chat history.")
    elif st.session_state.show_chat_history:
        st.info("Start chatting to build history!")
    
    # Display stored memories if chat history is shown
    if st.session_state.selected_project and st.session_state.show_chat_history:
        # Get project memories
        memories = st.session_state.agent.get_all_project_memories(
            st.session_state.current_project_name
        )
        
        if memories:
            with st.expander("🧠 Stored Information (Click to view)"):
                for key, value in memories.items():
                    st.markdown(f"**{key.title()}:** {value}")
                
                # Clear memories button
                if st.button("Clear Stored Information", key="clear_memories"):
                    st.session_state.agent.clear_project_memories(
                        st.session_state.current_project_name
                    )
                    st.rerun()
    
    # --- PROJECT DETAILS TABS ---
    st.markdown("---")
    tab1, tab2 = st.tabs(["📊 Project Details", "🔄 Switch Project"])
    
    with tab1:
        # Display project details
        sections = project.get('sections', {})
        
        for section_name, section_content in sections.items():
            with st.expander(f"**{section_name}**", expanded=(section_name in ["Problem Statement", "Solution"])):
                st.write(section_content)
    
    with tab2:
        # Project switching
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
                        st.session_state.user_input = ""
                        st.session_state.latest_response = ""
                        st.session_state.generated_document = None
                        st.rerun()
                st.markdown("---")

# Footer
st.markdown("---")
st.caption("Business Analyst Agent • Chat History Preserved • Clear Response Display • Memory System • Strict Mode • Document Download")