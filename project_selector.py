import json
import re
from typing import Dict, List, Optional
from config import config

class ProjectSelector:
    def __init__(self):
        self.projects = self.load_projects()
        self.project_names = [p["product_name"].lower() for p in self.projects]
    
    def load_projects(self) -> List[Dict]:
        """Load projects from JSON file"""
        try:
            with open(config.PROJECTS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Project file not found at {config.PROJECTS_JSON}")
            return []
    
    def detect_project_from_input(self, user_input: str) -> Optional[Dict]:
        """Detect which project the user is referring to"""
        input_lower = user_input.lower()
        
        # Check for exact product name matches
        for i, project in enumerate(self.projects):
            product_name_lower = project["product_name"].lower()
            
            # Direct mention of product name
            if product_name_lower in input_lower:
                return project
            
            # Check for keywords (first word or common abbreviations)
            first_word = product_name_lower.split()[0]
            if first_word in input_lower and len(first_word) > 3:
                # Check if it's likely referring to this project
                project_keywords = self.extract_keywords(project)
                for keyword in project_keywords:
                    if keyword in input_lower:
                        return project
        
        # If no direct match, return None (user will select manually)
        return None
    
    def extract_keywords(self, project: Dict) -> List[str]:
        """Extract relevant keywords from project data"""
        keywords = []
        
        # Add product name words
        name_words = project["product_name"].lower().split()
        keywords.extend([w for w in name_words if len(w) > 3])
        
        # Add category/key terms from sections
        sections = project.get("sections", {})
        for section_content in sections.values():
            # Extract capitalized words (likely important terms)
            caps_words = re.findall(r'\b[A-Z][a-z]+\b', section_content)
            keywords.extend([w.lower() for w in caps_words if len(w) > 3])
        
        return list(set(keywords))  # Remove duplicates
    
    def get_project_by_name(self, project_name: str) -> Optional[Dict]:
        """Get project by exact name"""
        for project in self.projects:
            if project["product_name"].lower() == project_name.lower():
                return project
        return None
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        return self.projects