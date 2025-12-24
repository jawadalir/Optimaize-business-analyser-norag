from datetime import datetime

class DocumentGenerator:
    @staticmethod
    def format_markdown_document(title: str, content: str, project: dict) -> str:
        """Format a document with proper markdown structure"""
        sections = project.get("sections", {})
        
        document = f"# {title}\n\n"
        document += f"**Project:** {project['product_name']}\n"
        document += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        document += f"**Author:** Business Analyst Agent\n\n"
        document += "---\n\n"
        
        # Add executive summary
        document += "## Executive Summary\n\n"
        one_line = sections.get('One-Line Summary', '') if isinstance(sections, dict) else ''
        if one_line:
            document += f"{one_line}\n\n"
        
        # Add the main content
        document += content
        
        # Add appendices
        document += "\n\n---\n\n"
        document += "## Appendices\n\n"
        document += "### Project Reference\n"
        
        for section_name, section_content in sections.items():
            if section_name != 'One-Line Summary':
                document += f"\n**{section_name}:**\n"
                document += f"{section_content[:200]}...\n"
        
        return document
    
    @staticmethod
    def create_download_link(content: str, filename: str) -> str:
        """Create a download link for Streamlit"""
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        return f'<a href="data:file/markdown;base64,{b64}" download="{filename}">Download {filename}</a>'