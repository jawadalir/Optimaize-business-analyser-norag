import streamlit as st
import json
import os
from datetime import datetime
import base64
import traceback
import sys
from project_selector import ProjectSelector
from ba_agent import BusinessAnalystAgent

# Clear ALL caches
try:
    st.cache_resource.clear()
    st.cache_data.clear()
except Exception as e:
    st.warning(f"Could not clear caches: {str(e)}")

# Page configuration
try:
    st.set_page_config(
        page_title="Business Analyst Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    st.warning(f"Page configuration issue: {str(e)}")

# Custom CSS for better display - INCLUDING RADIO BUTTON STYLING
st.markdown("""
<style>
    /* Error Message Styling */
    .error-container {
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
    }
    
    .error-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .error-details {
        font-size: 0.9rem;
        color: #721c24;
        background-color: #f5c6cb;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
        border-left: 4px solid #dc3545;
        display: none;
    }
    
    .error-toggle {
        color: #0056b3;
        cursor: pointer;
        font-size: 0.8rem;
        margin-top: 5px;
        text-decoration: underline;
    }
    
    .error-toggle:hover {
        color: #003d82;
    }
    
    .warning-container {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }
    
    /* Radio Button Styling */
    .radio-group-custom {
        margin: 15px 0;
        padding: 10px;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    
    .radio-label-custom {
        display: block;
        position: relative;
        padding-left: 35px;
        margin-bottom: 12px;
        cursor: pointer;
        font-size: 1rem;
        user-select: none;
        color: #2c3e50;
        transition: all 0.3s;
    }
    
    .radio-label-custom:hover {
        color: #3498db;
    }
    
    .radio-label-custom input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
    }
    
    .checkmark-custom {
        position: absolute;
        top: 0;
        left: 0;
        height: 22px;
        width: 22px;
        background-color: #e9ecef;
        border-radius: 50%;
        transition: all 0.3s;
        border: 2px solid #dee2e6;
    }
    
    .radio-label-custom:hover input ~ .checkmark-custom {
        background-color: #ddd;
        border-color: #3498db;
    }
    
    .radio-label-custom input:checked ~ .checkmark-custom {
        background-color: #3498db;
        border-color: #2980b9;
    }
    
    .checkmark-custom:after {
        content: "";
        position: absolute;
        display: none;
    }
    
    .radio-label-custom input:checked ~ .checkmark-custom:after {
        display: block;
    }
    
    .radio-label-custom .checkmark-custom:after {
        top: 5px;
        left: 5px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: white;
    }
    
    /* Card Style Radio Buttons */
    .card-radio-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0;
    }
    
    .card-radio-item {
        flex: 1;
        min-width: 120px;
    }
    
    .card-radio-input {
        display: none;
    }
    
    .card-radio-label {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 15px 10px;
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        height: 100%;
    }
    
    .card-radio-label:hover {
        border-color: #3498db;
        background: #e3f2fd;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .card-radio-input:checked + .card-radio-label {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border-color: #2980b9;
        box-shadow: 0 6px 12px rgba(52, 152, 219, 0.3);
    }
    
    .card-radio-label i {
        font-size: 1.5rem;
        margin-bottom: 8px;
    }
    
    .card-radio-label small {
        font-size: 0.8rem;
        opacity: 0.8;
        margin-top: 5px;
    }
    
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
    
    /* Enhanced document display */
    .document-section {
        background-color: #fff;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .document-header {
        background-color: #f8f9fa;
        padding: 10px;
        border-left: 4px solid #1976d2;
        margin-bottom: 15px;
    }
    
    .document-meta {
        font-size: 0.85rem;
        color: #666;
        display: flex;
        gap: 15px;
        margin-bottom: 10px;
    }
    
    .download-buttons {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 15px 0;
    }
    
    .diagram-placeholder {
        background-color: #f0f8ff;
        border: 1px dashed #4caf50;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
        text-align: center;
    }
    
    .diagram-placeholder code {
        background-color: #fff;
        padding: 10px;
        border-radius: 3px;
        display: block;
        text-align: left;
        margin: 10px 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    
    .comprehensive-badge {
        background-color: #ff9800;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }
    
    /* Form Group Styling */
    .form-group-custom {
        margin-bottom: 20px;
        padding: 15px;
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    .form-label-custom {
        display: block;
        margin-bottom: 8px;
        font-weight: 600;
        color: #2c3e50;
        font-size: 1.1rem;
    }
    
    .form-label-custom.required::after {
        content: " *";
        color: #e74c3c;
    }
    
    /* Required Field Indicator */
    .required-field::after {
        content: " *";
        color: #e74c3c;
    }
    
    /* Validation Styles */
    .validation-error {
        color: #e74c3c;
        font-size: 0.9rem;
        margin-top: 5px;
        padding: 8px;
        background: #fde8e8;
        border-radius: 4px;
        border-left: 4px solid #e74c3c;
    }
    
    /* Success Message */
    .success-message {
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        margin: 20px 0;
        display: none;
        animation: slideIn 0.5s ease;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Document Selection Grid */
    .doc-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .doc-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        position: relative;
        overflow: hidden;
    }
    
    .doc-card:hover {
        border-color: #3498db;
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .doc-card.selected {
        border-color: #3498db;
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        box-shadow: 0 6px 12px rgba(52, 152, 219, 0.2);
    }
    
    .doc-card i {
        font-size: 2rem;
        color: #3498db;
        margin-bottom: 10px;
    }
    
    .doc-card.selected i {
        color: #1976d2;
    }
    
    .doc-title {
        font-weight: 600;
        color: #2c3e50;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
    
    .doc-desc {
        font-size: 0.75rem;
        color: #7f8c8d;
        margin-top: 8px;
    }
    
    /* Generate Button */
    .generate-btn {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
        margin-top: 20px;
    }
    
    .generate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(52, 152, 219, 0.3);
    }
    
    .generate-btn:active {
        transform: translateY(0);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .doc-grid {
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        }
        
        .card-radio-item {
            min-width: 100px;
        }
    }
</style>

<script>
function toggleErrorDetails(id) {
    var element = document.getElementById(id);
    if (element.style.display === "none" || element.style.display === "") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}
</script>
""", unsafe_allow_html=True)

# Global error display function
def display_error(error_msg, detailed_error=None, error_type="error"):
    """Display error messages without blocking the app"""
    try:
        error_id = f"error_{datetime.now().strftime('%H%M%S%f')}"
        
        if error_type == "error":
            st.markdown(f"""
            <div class="error-container">
                <div class="error-title">⚠️ Error: {error_msg}</div>
                <div class="error-toggle" onclick="toggleErrorDetails('{error_id}')">
                    Click here to view technical details
                </div>
                <div id="{error_id}" class="error-details">
                    {detailed_error or "No additional details available"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="warning-container">
                <div class="error-title">⚠️ Warning: {error_msg}</div>
                {f'<div style="font-size: 0.9rem; margin-top: 5px;">{detailed_error}</div>' if detailed_error else ''}
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        # Fallback to simple error display
        st.error(f"Error: {error_msg}")

# Safe initialization function
def safe_initialize():
    """Initialize session state with error handling"""
    try:
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
        
        # Store generated documents
        if 'generated_documents' not in st.session_state:
            st.session_state.generated_documents = {}
        
        # Store last document for download
        if 'last_document' not in st.session_state:
            st.session_state.last_document = None
        if 'last_document_name' not in st.session_state:
            st.session_state.last_document_name = ""
        
        # Document generation progress
        if 'doc_generation_progress' not in st.session_state:
            st.session_state.doc_generation_progress = 0
        
        # Document selection state
        if 'selected_document_type' not in st.session_state:
            st.session_state.selected_document_type = None
        
        if 'document_generation_form' not in st.session_state:
            st.session_state.document_generation_form = {}
        
        # Initialize document form values
        if 'doc_detail_level' not in st.session_state:
            st.session_state.doc_detail_level = "Comprehensive"
        
        if 'doc_format_tables' not in st.session_state:
            st.session_state.doc_format_tables = True
        
        if 'doc_validation_errors' not in st.session_state:
            st.session_state.doc_validation_errors = {}
            
        if 'app_errors' not in st.session_state:
            st.session_state.app_errors = []
            
    except Exception as e:
        display_error("Failed to initialize session state", str(e))
        # Set minimal defaults to keep app running
        st.session_state.selected_project = None
        st.session_state.session_messages = {}

# Function to clean markdown formatting
def clean_markdown_formatting(text):
    """Remove markdown formatting from text"""
    try:
        if not text:
            return ""
        
        # Remove markdown headers
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove markdown headers (###, ##, #)
            if line.startswith('# '):
                line = line[2:].strip()
            elif line.startswith('## '):
                line = line[3:].strip()
            elif line.startswith('### '):
                line = line[4:].strip()
            elif line.startswith('#### '):
                line = line[5:].strip()
            
            # Remove bold (**text**)
            line = line.replace('**', '')
            
            # Remove asterisks for emphasis
            line = line.replace('*', '')
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    except Exception as e:
        display_error("Error cleaning markdown formatting", str(e))
        return text or ""

# Function to clean response text for display
def clean_response_text(text):
    """Remove unwanted formatting and extract clean text"""
    try:
        if not text:
            return ""
        
        # Clean markdown formatting
        text = clean_markdown_formatting(text)
        
        # Remove HTML tags if any
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    except Exception as e:
        display_error("Error cleaning response text", str(e))
        return text or ""

# Function to create a Word document from text
def create_comprehensive_word_document(content, filename, project):
    """Create a comprehensive Word document with professional formatting"""
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.style import WD_STYLE_TYPE
        
        doc = Document()
        
        # Add professional styles
        styles = doc.styles
        
        # Title style
        title_style = styles.add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
        title_style.font.name = 'Calibri Light'
        title_style.font.size = Pt(28)
        title_style.font.bold = True
        title_style.font.color.rgb = RGBColor(0, 0, 0)
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_style.paragraph_format.space_after = Pt(24)
        
        # Heading 1 style
        h1_style = styles.add_style('CustomH1', WD_STYLE_TYPE.PARAGRAPH)
        h1_style.font.name = 'Calibri'
        h1_style.font.size = Pt(18)
        h1_style.font.bold = True
        h1_style.font.color.rgb = RGBColor(0, 51, 102)
        h1_style.paragraph_format.space_before = Pt(24)
        h1_style.paragraph_format.space_after = Pt(12)
        
        # Heading 2 style
        h2_style = styles.add_style('CustomH2', WD_STYLE_TYPE.PARAGRAPH)
        h2_style.font.name = 'Calibri'
        h2_style.font.size = Pt(14)
        h2_style.font.bold = True
        h2_style.font.color.rgb = RGBColor(0, 102, 153)
        h2_style.paragraph_format.space_before = Pt(18)
        h2_style.paragraph_format.space_after = Pt(6)
        
        # Normal style
        normal_style = styles.add_style('CustomNormal', WD_STYLE_TYPE.PARAGRAPH)
        normal_style.font.name = 'Calibri'
        normal_style.font.size = Pt(11)
        normal_style.paragraph_format.line_spacing = 1.5
        normal_style.paragraph_format.space_after = Pt(6)
        
        # Cover Page
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run(f"{project['product_name']}\n")
        run.font.size = Pt(36)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 32, 96)
        
        doc.add_paragraph().add_run("\n")
        
        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = subtitle.add_run(f"{filename.replace('.docx', '').split('_')[-3:]}\n")
        run.font.size = Pt(24)
        run.font.bold = True
        
        doc.add_paragraph().add_run("\n\n")
        
        info = doc.add_paragraph()
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info.add_run(f"Version: 1.0\n")
        info.add_run(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        info.add_run(f"Status: Draft\n")
        info.add_run(f"Confidentiality: Internal Use Only\n")
        
        doc.add_page_break()
        
        # Parse and add content
        lines = content.split('\n')
        current_heading = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                # Main title
                section_name = line.replace('# ', '').strip()
                p = doc.add_paragraph(style='CustomTitle')
                p.add_run(section_name)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
            elif line.startswith('## '):
                # H1
                section_name = line.replace('## ', '').strip()
                p = doc.add_paragraph(style='CustomH1')
                p.add_run(section_name)
                
            elif line.startswith('### '):
                # H2
                section_name = line.replace('### ', '').strip()
                p = doc.add_paragraph(style='CustomH2')
                p.add_run(section_name)
                
            elif line.startswith('#### '):
                # H3
                section_name = line.replace('#### ', '').strip()
                p = doc.add_paragraph()
                p.add_run(section_name).bold = True
                
            elif line.startswith('```mermaid'):
                # Diagram placeholder
                p = doc.add_paragraph(style='CustomH2')
                p.add_run("[Diagram Placeholder]")
                p = doc.add_paragraph(style='CustomNormal')
                p.add_run("Note: This section contains Mermaid.js diagram code. Use markdown viewer to render the diagram.")
                
            elif line.startswith('```'):
                # Skip code block delimiters
                continue
                
            elif line.startswith('- ') or line.startswith('* '):
                # Bullet points
                p = doc.add_paragraph(style='CustomNormal')
                p.add_run(f"• {line[2:]}")
                p.paragraph_format.left_indent = Inches(0.25)
                
            elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
                # Numbered list
                p = doc.add_paragraph(style='CustomNormal')
                p.add_run(line)
                p.paragraph_format.left_indent = Inches(0.25)
                
            else:
                # Normal paragraph
                p = doc.add_paragraph(style='CustomNormal')
                p.add_run(line)
        
        # Add appendices
        doc.add_page_break()
        p = doc.add_paragraph(style='CustomH1')
        p.add_run("Appendices")
        
        # Add revision history table
        p = doc.add_paragraph(style='CustomH2')
        p.add_run("Revision History")
        
        # Create table
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light Shading Accent 1'
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Version'
        hdr_cells[1].text = 'Date'
        hdr_cells[2].text = 'Author'
        hdr_cells[3].text = 'Changes'
        
        # Data row
        row_cells = table.add_row().cells
        row_cells[0].text = '1.0'
        row_cells[1].text = datetime.now().strftime('%Y-%m-%d')
        row_cells[2].text = 'AI Business Analyst'
        row_cells[3].text = 'Initial Draft'
        
        # Save to bytes
        import io
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream
        
    except ImportError:
        # Fallback to simple document if python-docx not installed
        display_error("python-docx not installed, using simple format", error_type="warning")
        return create_simple_word_document(content, filename, project)
    except Exception as e:
        display_error("Error creating comprehensive Word document", str(e))
        return create_simple_word_document(content, filename, project)

def create_simple_word_document(text, filename, project):
    """Create a simple Word document from text using python-docx (fallback)"""
    try:
        from docx import Document
        doc = Document()
        
        # Clean markdown from the text
        clean_text = clean_markdown_formatting(text)
        
        # Extract project name from filename
        project_name = filename.replace('.docx', '').split('_')[0] if '_' in filename else filename.replace('.docx', '')
        
        # Add title
        doc.add_heading(project_name, 0)
        doc.add_heading(f"Document: {filename.replace('.docx', '')}", 1)
        
        # Add timestamp
        from datetime import datetime
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("")
        
        # Split text into paragraphs and add to document
        sections = clean_text.split('\n\n')
        for section in sections:
            if section.strip():
                # Check if this looks like a section header (all caps or starts with numbers)
                lines = section.strip().split('\n')
                if len(lines) > 0:
                    first_line = lines[0].strip()
                    # If line is short and looks like a heading, add as heading
                    if len(first_line) < 100 and (first_line.isupper() or first_line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '- '))):
                        doc.add_heading(first_line, level=2)
                        if len(lines) > 1:
                            for line in lines[1:]:
                                if line.strip():
                                    doc.add_paragraph(line.strip())
                    else:
                        doc.add_paragraph(section.strip())
        
        # Add page break for new section
        doc.add_page_break()
        
        # Save to bytes
        import io
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream
    except ImportError:
        display_error("python-docx library not installed", "Install it with: pip install python-docx", "warning")
        return None
    except Exception as e:
        display_error("Error creating simple Word document", str(e))
        return None

# Function to format document content properly
def format_document_content(content, doc_type):
    """Format document content to remove AI-generated markdown"""
    try:
        if not content:
            return ""
        
        # First clean markdown
        content = clean_markdown_formatting(content)
        
        # Specific formatting for different document types
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove any remaining markdown indicators
            line = line.replace('####', '').replace('###', '').replace('##', '').replace('#', '')
            line = line.replace('**', '').replace('*', '')
            
            # Format based on document type
            if doc_type == "SWOT Analysis Report":
                if any(word in line.lower() for word in ['strength', 'weakness', 'opportunity', 'threat', 'conclusion']):
                    formatted_lines.append(f"\n{line.upper()}\n" + "="*len(line))
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    formatted_lines.append(f"  {line}")
                else:
                    formatted_lines.append(line)
            elif doc_type == "Business Requirements Document (BRD)":
                if any(word in line.lower() for word in ['executive', 'overview', 'objective', 'scope', 'requirement', 'stakeholder', 'assumption', 'constraint']):
                    formatted_lines.append(f"\n{line.upper()}\n" + "-"*len(line))
                else:
                    formatted_lines.append(line)
            elif doc_type == "Functional Requirements Document (FRD)":
                if any(word in line.lower() for word in ['functional', 'requirement', 'specification', 'interface', 'system', 'module']):
                    formatted_lines.append(f"\n{line.upper()}\n")
                else:
                    formatted_lines.append(line)
            elif doc_type == "Non-Functional Requirements (NFR)":
                if any(word in line.lower() for word in ['performance', 'security', 'scalability', 'availability', 'reliability']):
                    formatted_lines.append(f"\n{line.upper()}\n")
                else:
                    formatted_lines.append(line)
            elif doc_type == "Process Flow Diagrams (BPMN)":
                if any(word in line.lower() for word in ['process', 'flow', 'diagram', 'activity', 'decision', 'gateway']):
                    formatted_lines.append(f"\n{line.upper()}\n")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    except Exception as e:
        display_error("Error formatting document content", str(e))
        return content or ""

# Function to get or create session messages for a project
def get_session_messages(project_name):
    """Get messages for current session"""
    try:
        if project_name not in st.session_state.session_messages:
            st.session_state.session_messages[project_name] = []
        return st.session_state.session_messages[project_name]
    except Exception as e:
        display_error("Error getting session messages", str(e))
        return []

# Function to add message to session
def add_to_session_messages(project_name, role, content, timestamp=None):
    """Add message to session messages"""
    try:
        messages = get_session_messages(project_name)
        messages.append({
            "role": role,
            "content": clean_response_text(content),
            "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        # Keep only last 20 messages in session
        st.session_state.session_messages[project_name] = messages[-20:]
    except Exception as e:
        display_error("Error adding message to session", str(e))

# Function to validate document generation form
def validate_document_form():
    """Validate document generation form"""
    try:
        errors = {}
        
        if not st.session_state.selected_document_type:
            errors['document_type'] = "Please select a document type"
        
        if not st.session_state.selected_project:
            errors['project'] = "Please select a project first"
        
        st.session_state.doc_validation_errors = errors
        return len(errors) == 0
    except Exception as e:
        display_error("Error validating document form", str(e))
        return False

# Safe function to get projects
def safe_get_projects():
    """Safely get projects with error handling"""
    try:
        return st.session_state.project_selector.get_all_projects()
    except Exception as e:
        display_error("Could not load projects", str(e))
        return []

# Safe function to analyze with options
def safe_analyze_with_options(project, user_input, response_style="detailed", scope="specific"):
    """Safely analyze with error handling"""
    try:
        return st.session_state.agent.analyze_with_options(
            project,
            user_input,
            response_style=response_style,
            scope=scope
        )
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        display_error(error_msg, traceback.format_exc())
        return f"I encountered an error while analyzing your request. Please try again or rephrase your question.\n\nError: {str(e)}"

# Safe function to generate document
def safe_generate_document(project, document_type, format_tables=True):
    """Safely generate document with error handling"""
    try:
        return st.session_state.agent.generate_document(
            project=project,
            document_type=document_type,
            format_tables=format_tables
        )
    except Exception as e:
        error_msg = f"Document generation failed: {str(e)}"
        display_error(error_msg, traceback.format_exc())
        return f"# Error Generating Document\n\nI encountered an error while generating the {document_type}.\n\n**Error Details:** {str(e)}\n\nPlease try again or select a different document type."

# Header with error boundary
try:
    st.title("🤖 Business Analyst Agent")
    st.markdown("AI-powered business analysis for your projects")
except Exception as e:
    display_error("Error displaying header", str(e))

# Initialize session state safely
try:
    safe_initialize()
except Exception as e:
    display_error("Critical initialization error", str(e))
    st.stop()

# Sidebar with error boundary
try:
    with st.sidebar:
        st.markdown("## 📋 Project Management")
        
        # Get all projects safely
        projects = safe_get_projects()
        project_names = ["-- Select a Project --"]
        if projects:
            project_names.extend([p.get("product_name", "Unknown") for p in projects])
        
        # Project selection
        selected_project_name = st.selectbox(
            "Select a project:",
            project_names,
            index=0
        )
        
        # Handle project selection
        if selected_project_name != "-- Select a Project --":
            try:
                if selected_project_name != st.session_state.current_project_name:
                    st.session_state.selected_project = st.session_state.project_selector.get_project_by_name(selected_project_name)
                    st.session_state.current_project_name = selected_project_name
                    st.session_state.user_input = ""
                    st.rerun()
            except Exception as e:
                display_error("Error selecting project", str(e))
        
        if st.session_state.selected_project:
            try:
                project = st.session_state.selected_project
                
                st.markdown(f"### 🎯 {project['product_name']}")
                
                # Get actual chat history from agent
                try:
                    actual_history = st.session_state.agent.get_project_history(project['product_name'])
                    st.metric("Total Messages", len(actual_history))
                except:
                    st.metric("Total Messages", 0)
                
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
                
                # Show current memory count
                col3, col4 = st.columns(2)
                with col3:
                    if st.session_state.selected_project:
                        try:
                            memories = st.session_state.agent.get_all_project_memories(
                                st.session_state.current_project_name
                            )
                            st.metric("Stored Facts", len(memories))
                        except:
                            st.metric("Stored Facts", 0)
                
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
                
                # Chat Management
                st.markdown("### 💬 Chat Management")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Clear History", use_container_width=True):
                        try:
                            # Clear both agent history and session messages
                            st.session_state.agent.clear_project_history(project['product_name'])
                            if project['product_name'] in st.session_state.session_messages:
                                st.session_state.session_messages[project['product_name']] = []
                            st.session_state.latest_response = ""
                            st.success(f"Chat history cleared for {project['product_name']}")
                            st.rerun()
                        except Exception as e:
                            display_error("Error clearing history", str(e))
                
                with col2:
                    # Toggle chat history visibility
                    toggle_text = "📜 Show History" if not st.session_state.show_chat_history else "📜 Hide History"
                    if st.button(toggle_text, use_container_width=True):
                        st.session_state.show_chat_history = not st.session_state.show_chat_history
                        st.rerun()
                        
            except Exception as e:
                display_error("Error displaying project details", str(e))
except Exception as e:
    display_error("Sidebar error", str(e))

# Main Content Area with comprehensive error handling
try:
    if not st.session_state.selected_project:
        # Welcome screen
        st.info("👈 Select a project from the sidebar to begin analysis")
        
        # Show available projects
        st.markdown("### Available Projects")
        if projects:
            for project in projects:
                try:
                    with st.expander(f"📁 {project.get('product_name', 'Unknown Project')}"):
                        sections = project.get('sections', {})
                        one_line = sections.get('One-Line Summary', sections.get('Solution', ''))
                        if isinstance(one_line, str) and len(one_line) > 200:
                            one_line = one_line[:200] + "..."
                        st.write(one_line)
                        if st.button(f"Select {project.get('product_name', 'Project')}", key=f"select_{project.get('product_name', '')}"):
                            try:
                                st.session_state.selected_project = project
                                st.session_state.current_project_name = project.get('product_name', '')
                                st.rerun()
                            except Exception as e:
                                display_error("Error selecting project", str(e))
                except Exception as e:
                    display_error(f"Error displaying project {project.get('product_name', 'Unknown')}", str(e))
        else:
            st.warning("No projects available. Check if project data is loaded correctly.")
    
    else:
        # Project is selected
        try:
            project = st.session_state.selected_project
            
            # Project header
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"### 💬 Chat: **{project.get('product_name', 'Unknown Project')}**")
            with col2:
                # Style indicators
                style_pill = "🟢 Detailed" if st.session_state.response_style == "detailed" else "⚪ Simple"
                scope_pill = "🎯 Specific" if st.session_state.response_scope == "specific" else "🌐 General"
                st.markdown(
                    f"<div style='display: flex; gap: 0.5rem; flex-wrap: wrap;'>"
                    f"<span class='style-pill active'>{style_pill}</span>"
                    f"<span class='style-pill active'>{scope_pill}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col3:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Create tabs
            try:
                tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Document Generation", "📊 Project Details"])
                
                with tab1:
                    try:
                        # Get session messages for this project
                        session_messages = get_session_messages(project.get('product_name', ''))
                        
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
                            try:
                                with st.spinner("🤔 Analyzing..."):
                                    # Add user message to session
                                    add_to_session_messages(project.get('product_name', ''), "user", st.session_state.user_input)
                                    
                                    # Get analysis from agent
                                    response = safe_analyze_with_options(
                                        project,
                                        st.session_state.user_input,
                                        response_style=st.session_state.response_style,
                                        scope=st.session_state.response_scope
                                    )
                                    
                                    # Add assistant response to session
                                    add_to_session_messages(project.get('product_name', ''), "assistant", response)
                                    
                                    # Store latest response
                                    st.session_state.latest_response = clean_response_text(response)
                                    
                                    # Clear auto-send flag
                                    st.session_state.auto_send = False
                                    st.session_state.user_input = ""
                                    st.rerun()
                            except Exception as e:
                                display_error("Error processing auto-send", str(e))
                                st.session_state.auto_send = False
                        
                        # Input field
                        user_input = st.text_area(
                            "Type your question:",
                            value=st.session_state.user_input,
                            placeholder=f"Ask about {project.get('product_name', 'the project')}...",
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
                            try:
                                with st.spinner("🤔 Analyzing..."):
                                    # Check if user is mentioning another project
                                    try:
                                        detected_project = st.session_state.project_selector.detect_project_from_input(user_input)
                                        
                                        if detected_project and detected_project.get('product_name', '') != st.session_state.current_project_name:
                                            # Switch to detected project
                                            st.info(f"🔍 Switching to: **{detected_project.get('product_name', 'Unknown')}**")
                                            st.session_state.selected_project = detected_project
                                            st.session_state.current_project_name = detected_project.get('product_name', '')
                                            st.session_state.user_input = user_input
                                            st.rerun()
                                    except:
                                        pass  # Ignore project detection errors
                                    
                                    # Add user message to session
                                    add_to_session_messages(project.get('product_name', ''), "user", user_input)
                                    
                                    # Get analysis from agent
                                    response = safe_analyze_with_options(
                                        project,
                                        user_input,
                                        response_style=st.session_state.response_style,
                                        scope=st.session_state.response_scope
                                    )
                                    
                                    # Add assistant response to session
                                    add_to_session_messages(project.get('product_name', ''), "assistant", response)
                                    
                                    # Store latest response
                                    st.session_state.latest_response = clean_response_text(response)
                                    
                                    # Clear input
                                    st.session_state.user_input = ""
                                    st.rerun()
                            except Exception as e:
                                display_error("Error processing your question", str(e))
                        
                        # Divider
                        st.markdown("---")
                        
                        # --- LATEST RESPONSE (BOLD AND CLEAR) ---
                        if st.session_state.latest_response or session_messages:
                            st.markdown("### 📋 **Latest Response**")
                            
                            # Get the latest assistant response
                            latest_response = st.session_state.latest_response
                            if not latest_response and session_messages:
                                # Find the latest assistant message
                                assistant_messages = [m for m in session_messages if m.get("role") == "assistant"]
                                if assistant_messages:
                                    latest_response = assistant_messages[-1].get("content", "")
                            
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
                                
                                # Download button for latest response as Word
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    # Show timestamp for latest response
                                    if session_messages and session_messages[-1].get("timestamp"):
                                        st.caption(f"🕒 Generated: {session_messages[-1]['timestamp']}")
                                with col2:
                                    # Create Word document for the response
                                    response_filename = f"{project.get('product_name', 'Project')}_Response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                                    try:
                                        word_doc = create_comprehensive_word_document(latest_response, response_filename, project)
                                        if word_doc:
                                            st.download_button(
                                                label="📄 Download as Word",
                                                data=word_doc,
                                                file_name=response_filename,
                                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                use_container_width=True
                                            )
                                    except Exception as e:
                                        display_error("Error creating Word document", str(e), "warning")
                        
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
                                    if msg.get("role") == "user":
                                        st.markdown(f"""
                                        <div class="chat-history-message chat-history-user">
                                            <strong>👤 You:</strong> {msg.get('content', '')[:150]}{'...' if len(msg.get('content', '')) > 150 else ''}
                                            <div class="timestamp">{msg.get('timestamp', '')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class="chat-history-message chat-history-assistant">
                                            <strong>🤖 Business Analyst:</strong> {msg.get('content', '')[:150]}{'...' if len(msg.get('content', '')) > 150 else ''}
                                            <div class="timestamp">{msg.get('timestamp', '')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Show full message in expander
                                    with st.expander("View full message"):
                                        if msg.get("role") == "user":
                                            st.markdown(f"**You:** {msg.get('content', '')}")
                                        else:
                                            st.markdown(f"**Business Analyst:** {msg.get('content', '')}")
                            else:
                                st.info("No previous chat history.")
                        elif st.session_state.show_chat_history:
                            st.info("Start chatting to build history!")
                        
                        # Display stored memories if chat history is shown
                        if st.session_state.selected_project and st.session_state.show_chat_history:
                            try:
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
                                            try:
                                                st.session_state.agent.clear_project_memories(
                                                    st.session_state.current_project_name
                                                )
                                                st.rerun()
                                            except Exception as e:
                                                display_error("Error clearing memories", str(e))
                            except:
                                pass  # Silently ignore memory errors
                                
                    except Exception as e:
                        display_error("Error in chat tab", str(e))
                
                with tab2:
                    try:
                        st.markdown("## 📄 Document Generation")
                        st.info("Select a document type and configure options to generate professional documents")
                        
                        # Document type selection using HTML grid
                        st.markdown("### 📋 Select Document Type")
                        
                        document_types = [
                            {
                                "type": "Business Requirements Document (BRD)",
                                "icon": "📋",
                                "description": "Comprehensive business requirements"
                            },
                            {
                                "type": "Functional Requirements Document (FRD)",
                                "icon": "⚙️",
                                "description": "Detailed functional specifications"
                            },
                            {
                                "type": "Non-Functional Requirements (NFR)",
                                "icon": "📊",
                                "description": "Performance, security, scalability"
                            },
                            {
                                "type": "User Stories & Acceptance Criteria",
                                "icon": "👥",
                                "description": "User stories with acceptance criteria"
                            },
                            {
                                "type": "Stakeholder Analysis Matrix",
                                "icon": "🤝",
                                "description": "Stakeholder analysis & engagement"
                            },
                            {
                                "type": "SWOT Analysis Report",
                                "icon": "🔍",
                                "description": "Strengths, weaknesses, opportunities, threats"
                            },
                            {
                                "type": "Process Flow Diagrams (BPMN)",
                                "icon": "🔄",
                                "description": "Business process modeling"
                            },
                        ]
                        
                        # Create document selection grid
                        cols = st.columns(5)
                        for idx, doc_info in enumerate(document_types):
                            col_idx = idx % 5
                            with cols[col_idx]:
                                is_selected = st.session_state.selected_document_type == doc_info["type"]
                                
                                st.markdown(f"""
                                <div class="doc-card {'selected' if is_selected else ''}" onclick="document.getElementById('doc_{idx}').click()">
                                    <div style="font-size: 2rem; margin-bottom: 10px;">{doc_info['icon']}</div>
                                    <div class="doc-title">{doc_info['type'].split('(')[0].strip()}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if st.button(f"Select {doc_info['type'][:10]}", 
                                           key=f"doc_{idx}",
                                           type="primary" if is_selected else "secondary",
                                           use_container_width=True):
                                    st.session_state.selected_document_type = doc_info["type"]
                                    st.rerun()
                        
                        # Show selected document
                        if st.session_state.selected_document_type:
                            st.markdown(f"""
                            <div class="form-group-custom">
                                <div class="form-label-custom">✅ Selected Document</div>
                                <div style="font-size: 1.2rem; color: #2c3e50; padding: 10px; background: #e8f4fc; border-radius: 5px;">
                                    📄 <strong>{st.session_state.selected_document_type}</strong>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Generate Button
                        st.markdown("---")
                        if st.button("🚀 Generate Document", type="primary", use_container_width=True):
                            if not st.session_state.selected_document_type:
                                display_error("Please select a document type first!", error_type="warning")
                            else:
                                # Generate document
                                with st.spinner(f"🧠 Generating {st.session_state.selected_document_type}..."):
                                    try:
                                        document = safe_generate_document(
                                            project=project,
                                            document_type=st.session_state.selected_document_type,
                                            format_tables=st.session_state.doc_format_tables
                                        )
                                        
                                        # Store for download
                                        st.session_state.last_document = document
                                        st.session_state.last_document_name = f"{project.get('product_name', 'Project')}_{st.session_state.selected_document_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                                        
                                        # Store in generated documents
                                        project_name = project.get('product_name', '')
                                        if project_name not in st.session_state.generated_documents:
                                            st.session_state.generated_documents[project_name] = {}
                                        st.session_state.generated_documents[project_name][st.session_state.selected_document_type] = document
                                        
                                        st.success(f"✅ {st.session_state.selected_document_type} generated successfully!")
                                    except Exception as e:
                                        display_error(f"Error generating {st.session_state.selected_document_type}", str(e))
                        
                        # Display generated documents for this project
                        project_name = project.get('product_name', '')
                        if project_name in st.session_state.generated_documents:
                            st.markdown("---")
                            st.markdown("### 📂 Generated Documents")
                            
                            for doc_type, doc_content in st.session_state.generated_documents[project_name].items():
                                try:
                                    with st.expander(f"📄 {doc_type}"):
                                        # Show document metadata
                                        st.markdown(f"""
                                        <div class="document-meta">
                                            <span>📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                                            <span>📏 Pages: ~{len(doc_content.split())//500}</span>
                                            <span>🔤 Words: {len(doc_content.split())}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Show preview (first 3000 characters)
                                        preview_text = doc_content[:3000]
                                        if len(doc_content) > 3000:
                                            preview_text += "\n\n... [Document continues] ..."
                                        
                                        # Check for diagrams
                                        if "```mermaid" in preview_text:
                                            st.markdown("""
                                            <div class="diagram-placeholder">
                                                📊 <strong>Diagrams Included</strong>
                                                <p>This document contains Mermaid.js diagrams that will render in markdown viewers.</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        st.text_area(
                                            f"Preview of {doc_type}",
                                            value=preview_text,
                                            height=300,
                                            disabled=True,
                                            key=f"preview_{doc_type}"
                                        )
                                        
                                        # Download buttons
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            # Word download
                                            doc_filename = f"{project_name}_{doc_type.replace(' ', '_')}.docx"
                                            try:
                                                word_doc = create_comprehensive_word_document(doc_content, doc_filename, project)
                                                if word_doc:
                                                    st.download_button(
                                                        label="📄 Word",
                                                        data=word_doc,
                                                        file_name=doc_filename,
                                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                        use_container_width=True,
                                                        key=f"word_{doc_type}"
                                                    )
                                            except Exception as e:
                                                display_error("Error creating Word document", str(e), "warning")
                                        
                                        with col2:
                                            # Markdown download
                                            st.download_button(
                                                label="📝 Markdown",
                                                data=doc_content,
                                                file_name=f"{project_name}_{doc_type.replace(' ', '_')}.md",
                                                mime="text/markdown",
                                                use_container_width=True,
                                                key=f"md_{doc_type}"
                                            )
                                        
                                        with col3:
                                            # PDF download (placeholder)
                                            if st.button("📄 PDF", use_container_width=True, key=f"pdf_{doc_type}"):
                                                st.info("PDF export coming soon!")
                                except Exception as e:
                                    display_error(f"Error displaying document {doc_type}", str(e))
                    except Exception as e:
                        display_error("Error in document generation tab", str(e))
                
                with tab3:
                    try:
                        # Display project details
                        st.markdown("## 📊 Project Details")
                        
                        sections = project.get('sections', {})
                        
                        if sections:
                            for section_name, section_content in sections.items():
                                try:
                                    with st.expander(f"**{section_name}**", expanded=(section_name in ["Problem Statement", "Solution"])):
                                        st.write(section_content)
                                except Exception as e:
                                    display_error(f"Error displaying section {section_name}", str(e))
                        else:
                            st.info("No project details available.")
                    except Exception as e:
                        display_error("Error in project details tab", str(e))
                        
            except Exception as e:
                display_error("Error creating tabs", str(e))
                
        except Exception as e:
            display_error("Error displaying project content", str(e))
            st.info("Please select a different project or refresh the page.")

except Exception as e:
    # Catch any unhandled exceptions in the main content area
    display_error("Unexpected error in main application", str(e))
    st.error("The application encountered an unexpected error. Please refresh the page or try again later.")
    
    # Show recovery options
    if st.button("🔄 Reset Application"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Footer with error boundary
try:
    st.markdown("---")
    st.caption(f"Business Analyst Agent v1.0 • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
except:
    pass  # Silently ignore footer errors