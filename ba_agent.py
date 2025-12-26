import json
import os
from typing import List, Dict, Optional
from openai import OpenAI
from config import config
from prompt_manager import PromptManager

class BusinessAnalystAgent:
    VERSION = "2.0-memory"  

    def __init__(self):
        print(f"Initializing BA Agent Version: {self.VERSION}")  # Debug
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.prompt_manager = PromptManager()
        self.chat_histories = self.load_all_chat_histories()
        self.project_memories = self.load_project_memories()  # NEW: Memory storage
    
    def load_all_chat_histories(self) -> Dict[str, List[Dict]]:
        """Load chat histories for all projects from file"""
        all_histories = {}
        try:
            if os.path.exists(config.CHAT_HISTORY_FILE):
                with open(config.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert from list format to project-based dictionary
                    for entry in data:
                        project_name = entry.get("project", "General")
                        if project_name not in all_histories:
                            all_histories[project_name] = []
                        all_histories[project_name].append(entry)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return all_histories
    
    def save_all_chat_histories(self):
        """Save all chat histories to file"""
        # Flatten the dictionary to a list
        all_entries = []
        for project_name, history in self.chat_histories.items():
            for entry in history[-config.MAX_HISTORY_PER_PROJECT:]:
                entry["project"] = project_name
                all_entries.append(entry)
        
        # Save to file
        os.makedirs(os.path.dirname(config.CHAT_HISTORY_FILE), exist_ok=True)
        with open(config.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2)
    
    def load_project_memories(self) -> Dict[str, Dict]:
        """Load project memories from file"""
        memory_file = "chat_history/project_memories.json"
        try:
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
    
    def save_project_memories(self):
        """Save project memories to file"""
        memory_file = "chat_history/project_memories.json"
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_memories, f, indent=2)
    
    def update_project_memory(self, project_name: str, key: str, value: str):
        """Update memory for a project"""
        if project_name not in self.project_memories:
            self.project_memories[project_name] = {}
        self.project_memories[project_name][key] = value
        self.save_project_memories()
    
    def get_project_memory(self, project_name: str, key: str) -> Optional[str]:
        """Get memory for a project"""
        if project_name in self.project_memories:
            return self.project_memories[project_name].get(key)
        return None
    
    def get_all_project_memories(self, project_name: str) -> Dict:
        """Get all memories for a project"""
        return self.project_memories.get(project_name, {})
    
    def clear_project_memories(self, project_name: str):
        """Clear all memories for a project"""
        if project_name in self.project_memories:
            self.project_memories[project_name] = {}
            self.save_project_memories()
    
    def get_project_history(self, project_name: str) -> List[Dict]:
        """Get chat history for a specific project"""
        return self.chat_histories.get(project_name, [])
    
    def add_to_history(self, project: str, user_input: str, response: str, 
                      analysis_type: str = "general", response_style: str = "detailed"):
        """Add a conversation to project-specific history"""
        history_entry = {
            "timestamp": self.get_timestamp(),
            "user_input": user_input,
            "agent_response": response,
            "analysis_type": analysis_type,
            "response_style": response_style
        }
        
        if project not in self.chat_histories:
            self.chat_histories[project] = []
        
        self.chat_histories[project].append(history_entry)
        self.save_all_chat_histories()
    
    def clear_project_history(self, project_name: str):
        """Clear chat history for a specific project"""
        if project_name in self.chat_histories:
            self.chat_histories[project_name] = []
            self.save_all_chat_histories()
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def analyze_with_options(self, project: Dict, user_input: str, 
                           prompt_type: str = "general",
                           response_style: str = "detailed",
                           scope: str = "specific",
                           strict_mode: bool = False):
        """Perform analysis with style, scope, and strict mode options"""
        project_name = project["product_name"]
        project_details = json.dumps(project["sections"], indent=2)
        
        # Extract and store personal information from user input
        self.extract_and_store_memory(project_name, user_input)
        
        # Get project memories for context
        project_memories = self.get_all_project_memories(project_name)
        memory_context = ""
        if project_memories:
            memory_context = "\n\nRELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS:\n"
            for key, value in project_memories.items():
                memory_context += f"- {key}: {value}\n"
        
        # Get base prompt
        if prompt_type in ["requirements", "requirements_elicitation"]:
            prompt = self.prompt_manager.get_prompt("requirements_elicitation", {
                "project_name": project_name,
                "project_details": project_details
            })
            analysis_type = "requirements_analysis"
        
        elif prompt_type in ["risk", "risk_assessment"]:
            prompt = self.prompt_manager.get_prompt("risk_assessment", {
                "project_name": project_name,
                "project_details": project_details
            })
            analysis_type = "risk_assessment"
        
        elif prompt_type in ["stakeholder", "stakeholder_analysis"]:
            prompt = self.prompt_manager.get_prompt("stakeholder_analysis", {
                "project_name": project_name,
                "project_details": project_details
            })
            analysis_type = "stakeholder_analysis"
        
        else:
            # General analysis with custom instructions
            system_prompt = self.prompt_manager.get_system_prompt(project_name, project_details)
            
            # Add style, scope, and strict mode instructions
            style_instruction = ""
            if response_style == "simple":
                style_instruction = "Provide a concise, bullet-point summary. Focus on key takeaways only."
            else:  # detailed
                style_instruction = "Provide comprehensive analysis with detailed explanations, examples, and actionable insights."
            
            scope_instruction = ""
            if scope == "specific":
                scope_instruction = "Focus specifically on this project's unique aspects. Provide project-specific recommendations."
            else:  # general
                scope_instruction = "Provide general business analysis principles that apply broadly, then relate to this project."
            
            # NEW: Strict mode instruction
            strict_instruction = ""
            if strict_mode:
                strict_instruction = """
                STRICT MODE ENABLED: 
                - Only answer what is directly asked. Do not add extra information.
                - Do not provide explanations unless explicitly asked.
                - Keep responses extremely brief and to the point.
                - If the question is about stored information, provide ONLY that information.
                """
            
            prompt = f"""
            {system_prompt}
            {memory_context}
            
            ANALYSIS STYLE: {style_instruction}
            SCOPE: {scope_instruction}
            {strict_instruction}
            
            USER QUESTION: {user_input}
            
            Please provide your analysis accordingly.
            """
            analysis_type = f"general_{response_style}_{scope}{'_strict' if strict_mode else ''}"
        
        # Get response from OpenAI with adjusted parameters for strict mode
        response = self.get_openai_response(prompt, response_style, strict_mode)
        
        # Save to history
        self.add_to_history(project_name, user_input, response, analysis_type, response_style)
        
        return response
    
    def extract_and_store_memory(self, project_name: str, user_input: str):
        """Extract personal information from user input and store in memory"""
        input_lower = user_input.lower()
        
        # Patterns for extracting information
        patterns = {
            "my name is": "name",
            "i am called": "name",
            "call me": "name",
            "i work as": "role",
            "my role is": "role",
            "i'm from": "company",
            "my company is": "company",
            "contact me at": "contact",
            "my email is": "email",
            "call me at": "phone"
        }
        
        for pattern, memory_key in patterns.items():
            if pattern in input_lower:
                # Extract the value after the pattern
                start_idx = input_lower.find(pattern) + len(pattern)
                value = user_input[start_idx:].strip()
                
                # Clean up the value (remove punctuation, etc.)
                if value:
                    # Remove common ending punctuation and words
                    endings = ['.', ',', 'and', 'but', 'so']
                    for ending in endings:
                        if value.lower().endswith(f' {ending}'):
                            value = value[:-len(ending)-1]
                    
                    # Store in memory
                    self.update_project_memory(project_name, memory_key, value)
                    break
    
    def get_openai_response(self, prompt: str, response_style: str = "detailed", strict_mode: bool = False) -> str:
        """Get response from OpenAI API with style and strict mode considerations"""
        try:
            # Adjust parameters based on mode
            if strict_mode:
                max_tokens = 200  # Very short responses in strict mode
                temperature = 0.1  # Very deterministic
            elif response_style == "simple":
                max_tokens = 500
                temperature = 0.3
            else:  # detailed
                max_tokens = 2000
                temperature = config.TEMPERATURE
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior Business Analyst providing professional analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting AI response: {str(e)}"
    
    def generate_document(self, project: Dict, document_type: str, 
                         detail_level: str = "detailed") -> str:
        """Generate a specific BA document with detail option"""
        project_name = project["product_name"]
        project_details = json.dumps(project["sections"], indent=2)
        
        document_prompts = {
            "brd": "Generate a Business Requirements Document (BRD)",
            "user_stories": "Generate user stories with acceptance criteria",
            "risk_register": "Generate a comprehensive risk register",
            "stakeholder_matrix": "Generate a stakeholder analysis matrix",
            "swot": "Perform SWOT analysis",
            "project_charter": "Generate a project charter document",
            "gap_analysis": "Perform gap analysis",
            "test_plan": "Create a test plan outline"
        }
        
        if document_type not in document_prompts:
            return f"Unknown document type. Available: {', '.join(document_prompts.keys())}"
        
        detail_instruction = "with comprehensive details and examples" if detail_level == "detailed" else "with concise, key information only"
        
        prompt = f"""
        PROJECT: {project_name}
        
        PROJECT DETAILS:
        {project_details}
        
        TASK: {document_prompts[document_type]} {detail_instruction}
        
        INSTRUCTIONS:
        1. Use professional business analysis format
        2. Make it actionable and specific to this project
        3. Use markdown formatting
        4. Detail level: {detail_level.upper()}
        """
        
        response = self.get_openai_response(prompt, detail_level)
        self.add_to_history(project_name, f"Generate {document_type} ({detail_level})", 
                           response, f"document_{document_type}", detail_level)
        
        return response