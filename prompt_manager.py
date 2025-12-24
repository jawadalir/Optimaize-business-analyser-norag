import os
from config import config

class PromptManager:
    def __init__(self):
        self.prompts_dir = config.PROMPTS_DIR
        self.loaded_prompts = {}
        self.load_all_prompts()
    
    def load_all_prompts(self):
        """Load all prompt files from the prompts directory"""
        prompt_files = [
            "business_analyst_system",
            "requirements_elicitation", 
            "risk_assessment",
            "stakeholder_analysis",
            "document_templates"
        ]
        
        for prompt_name in prompt_files:
            file_path = os.path.join(self.prompts_dir, f"{prompt_name}.txt")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.loaded_prompts[prompt_name] = f.read()
            else:
                self.loaded_prompts[prompt_name] = f"# {prompt_name.replace('_', ' ').title()} Prompt"
    
    def get_prompt(self, prompt_name, variables=None):
        """Get a prompt with optional variable substitution"""
        prompt = self.loaded_prompts.get(prompt_name, "")
        
        if variables and prompt:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def get_system_prompt(self, project_name, project_details):
        """Get the main BA system prompt for a project"""
        return self.get_prompt("business_analyst_system", {
            "project_name": project_name,
            "project_details": project_details
        })