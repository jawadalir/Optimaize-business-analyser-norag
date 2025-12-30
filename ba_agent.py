import json
import os
from typing import List, Dict, Optional
from openai import OpenAI
from datetime import datetime, timedelta
from config import config
from prompt_manager import PromptManager
from document_generator import DocumentGenerator

class BusinessAnalystAgent:
    VERSION = "4.1-simplified"

    def __init__(self):
        print(f"Initializing BA Agent Version: {self.VERSION}")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.prompt_manager = PromptManager()
        self.document_generator = DocumentGenerator(self.client, self.prompt_manager)
        self.chat_histories = self.load_all_chat_histories()
        self.project_memories = self.load_project_memories()
    
    def load_all_chat_histories(self) -> Dict[str, List[Dict]]:
        """Load chat histories for all projects from file, removing expired entries"""
        all_histories = {}
        try:
            if os.path.exists(config.CHAT_HISTORY_FILE):
                with open(config.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Filter out expired entries
                    filtered_data = []
                    for entry in data:
                        timestamp_str = entry.get("timestamp")
                        if timestamp_str:
                            try:
                                entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                # Check if entry is older than 24 hours
                                if datetime.now() - entry_time <= timedelta(hours=24):
                                    filtered_data.append(entry)
                            except ValueError:
                                # If timestamp format is invalid, keep the entry
                                filtered_data.append(entry)
                        else:
                            # If no timestamp, keep the entry
                            filtered_data.append(entry)
                    
                    # Save filtered data back to file
                    if len(filtered_data) < len(data):
                        with open(config.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f_write:
                            json.dump(filtered_data, f_write, indent=2)
                    
                    # Organize by project
                    for entry in filtered_data:
                        project_name = entry.get("project", "General")
                        if project_name not in all_histories:
                            all_histories[project_name] = []
                        all_histories[project_name].append(entry)
                        
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return all_histories
    
    def save_all_chat_histories(self):
        """Save all chat histories to file with expiration check"""
        all_entries = []
        current_time = datetime.now()
        
        for project_name, history in self.chat_histories.items():
            for entry in history:
                # Check if entry is within 24 hours
                timestamp_str = entry.get("timestamp")
                keep_entry = True
                
                if timestamp_str:
                    try:
                        entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if current_time - entry_time > timedelta(hours=24):
                            keep_entry = False
                    except ValueError:
                        # If timestamp format is invalid, keep the entry
                        pass
                
                if keep_entry:
                    entry_with_project = entry.copy()
                    entry_with_project["project"] = project_name
                    all_entries.append(entry_with_project)
        
        # Also check for orphaned entries (not in current memory but in file)
        try:
            if os.path.exists(config.CHAT_HISTORY_FILE):
                with open(config.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    
                    for entry in existing_data:
                        # Skip entries already processed
                        if any(e.get("timestamp") == entry.get("timestamp") and 
                               e.get("user_input") == entry.get("user_input") 
                               for e in all_entries):
                            continue
                            
                        # Check if entry is within 24 hours
                        timestamp_str = entry.get("timestamp")
                        if timestamp_str:
                            try:
                                entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                if current_time - entry_time <= timedelta(hours=24):
                                    all_entries.append(entry)
                            except ValueError:
                                # If timestamp format is invalid, keep the entry
                                all_entries.append(entry)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(config.CHAT_HISTORY_FILE), exist_ok=True)
        
        # Save to file
        with open(config.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2)
    
    def load_project_memories(self) -> Dict[str, Dict]:
        """Load project memories from file, removing expired memories"""
        memory_file = "chat_history/project_memories.json"
        try:
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
                    
                    # Check for timestamp in memories and remove expired ones
                    current_time = datetime.now()
                    updated_memories = {}
                    
                    for project_name, project_memories in memories.items():
                        updated_project_memories = {}
                        for key, value in project_memories.items():
                            # Check if memory has timestamp metadata
                            if isinstance(value, dict) and "timestamp" in value:
                                timestamp_str = value.get("timestamp")
                                try:
                                    memory_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                    if current_time - memory_time <= timedelta(hours=24):
                                        updated_project_memories[key] = value
                                except ValueError:
                                    updated_project_memories[key] = value
                            else:
                                # If no timestamp, keep it (add timestamp)
                                updated_project_memories[key] = {
                                    "value": value,
                                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                                }
                        
                        if updated_project_memories:
                            updated_memories[project_name] = updated_project_memories
                    
                    # Save updated memories back to file
                    with open(memory_file, 'w', encoding='utf-8') as f_write:
                        json.dump(updated_memories, f_write, indent=2)
                    
                    return updated_memories
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
    
    def save_project_memories(self):
        """Save project memories to file with timestamps"""
        memory_file = "chat_history/project_memories.json"
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        
        # Add timestamps to memories
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memories_with_timestamps = {}
        
        for project_name, project_memories in self.project_memories.items():
            memories_with_timestamps[project_name] = {}
            for key, value in project_memories.items():
                if isinstance(value, dict) and "timestamp" in value:
                    memories_with_timestamps[project_name][key] = value
                else:
                    memories_with_timestamps[project_name][key] = {
                        "value": value,
                        "timestamp": current_time
                    }
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memories_with_timestamps, f, indent=2)
    
    def get_project_history(self, project_name: str) -> List[Dict]:
        """Get chat history for a specific project (only recent 24 hours)"""
        history = self.chat_histories.get(project_name, [])
        # Filter to ensure only recent entries
        current_time = datetime.now()
        recent_history = []
        
        for entry in history:
            timestamp_str = entry.get("timestamp")
            if timestamp_str:
                try:
                    entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if current_time - entry_time <= timedelta(hours=24):
                        recent_history.append(entry)
                except ValueError:
                    recent_history.append(entry)
            else:
                recent_history.append(entry)
        
        return recent_history
    
    def add_to_history(self, project: str, user_input: str, response: str, 
                      analysis_type: str = "general", response_style: str = "detailed"):
        """Add a conversation to project-specific history with timestamp"""
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
        
        # Clean up old histories after adding new entry
        self.cleanup_old_histories()
    
    def clear_project_history(self, project_name: str):
        """Clear chat history for a specific project"""
        if project_name in self.chat_histories:
            self.chat_histories[project_name] = []
            self.save_all_chat_histories()
    
    def get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def update_project_memory(self, project_name: str, key: str, value: str):
        """Update memory for a project with timestamp"""
        if project_name not in self.project_memories:
            self.project_memories[project_name] = {}
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.project_memories[project_name][key] = {
            "value": value,
            "timestamp": current_time
        }
        self.save_project_memories()
    
    def get_project_memory(self, project_name: str, key: str) -> Optional[str]:
        """Get memory for a project, checking expiration"""
        if project_name in self.project_memories:
            memory_data = self.project_memories[project_name].get(key)
            if memory_data:
                # Check if memory is expired
                if isinstance(memory_data, dict) and "timestamp" in memory_data:
                    timestamp_str = memory_data.get("timestamp")
                    try:
                        memory_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if datetime.now() - memory_time > timedelta(hours=24):
                            # Remove expired memory
                            del self.project_memories[project_name][key]
                            self.save_project_memories()
                            return None
                        return memory_data.get("value", memory_data)
                    except ValueError:
                        return memory_data.get("value", memory_data)
                return memory_data
        return None
    
    def get_all_project_memories(self, project_name: str) -> Dict:
        """Get all memories for a project, filtering expired ones"""
        current_time = datetime.now()
        project_memories = self.project_memories.get(project_name, {})
        filtered_memories = {}
        
        for key, value in project_memories.items():
            # Check expiration
            if isinstance(value, dict) and "timestamp" in value:
                timestamp_str = value.get("timestamp")
                try:
                    memory_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if current_time - memory_time <= timedelta(hours=24):
                        filtered_memories[key] = value.get("value", value)
                except ValueError:
                    filtered_memories[key] = value.get("value", value)
            else:
                filtered_memories[key] = value
        
        return filtered_memories
    
    def clear_project_memories(self, project_name: str):
        """Clear all memories for a project"""
        if project_name in self.project_memories:
            self.project_memories[project_name] = {}
            self.save_project_memories()
    
    def cleanup_old_histories(self):
        """Clean up all old histories (older than 24 hours)"""
        current_time = datetime.now()
        cleaned_histories = {}
        
        for project_name, history in self.chat_histories.items():
            cleaned_history = []
            for entry in history:
                timestamp_str = entry.get("timestamp")
                if timestamp_str:
                    try:
                        entry_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if current_time - entry_time <= timedelta(hours=24):
                            cleaned_history.append(entry)
                    except ValueError:
                        cleaned_history.append(entry)
                else:
                    cleaned_history.append(entry)
            
            if cleaned_history:
                cleaned_histories[project_name] = cleaned_history
        
        self.chat_histories = cleaned_histories
        self.save_all_chat_histories()
    
    def extract_and_store_memory(self, project_name: str, user_input: str):
        """Extract personal information from user input and store in memory"""
        input_lower = user_input.lower()
        
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
                start_idx = input_lower.find(pattern) + len(pattern)
                value = user_input[start_idx:].strip()
                
                if value:
                    endings = ['.', ',', 'and', 'but', 'so']
                    for ending in endings:
                        if value.lower().endswith(f' {ending}'):
                            value = value[:-len(ending)-1]
                    
                    self.update_project_memory(project_name, memory_key, value)
                    break
    
    def analyze_with_options(self, project: Dict, user_input: str, 
                           prompt_type: str = "general",
                           response_style: str = "detailed",
                           scope: str = "specific",
                           strict_mode: bool = False):
        """Perform analysis with style, scope, and strict mode options"""
        project_name = project["product_name"]
        project_details = json.dumps(project["sections"], indent=2)
        
        self.extract_and_store_memory(project_name, user_input)
        
        project_memories = self.get_all_project_memories(project_name)
        memory_context = ""
        if project_memories:
            memory_context = "\n\nRELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS:\n"
            for key, value in project_memories.items():
                memory_context += f"- {key}: {value}\n"
        
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
            system_prompt = self.prompt_manager.get_system_prompt(project_name, project_details)
            
            style_instruction = ""
            if response_style == "simple":
                style_instruction = "Provide a concise, bullet-point summary. Focus on key takeaways only."
            else:
                style_instruction = "Provide comprehensive analysis with detailed explanations, examples, and actionable insights."
            
            scope_instruction = ""
            if scope == "specific":
                scope_instruction = "Focus specifically on this project's unique aspects. Provide project-specific recommendations."
            else:
                scope_instruction = "Provide general business analysis principles that apply broadly, then relate to this project."
            
            
            prompt = f"""
            {system_prompt}
            {memory_context}
            
            ANALYSIS STYLE: {style_instruction}
            SCOPE: {scope_instruction}
            
            
            USER QUESTION: {user_input}
            
            Please provide your analysis accordingly.
            """
            analysis_type = f"general_{response_style}_{scope}{'_strict' if strict_mode else ''}"
        
        response = self.get_openai_response(prompt, response_style, strict_mode)
        self.add_to_history(project_name, user_input, response, analysis_type, response_style)
        
        return response
    
    def get_openai_response(self, prompt: str, response_style: str = "detailed", strict_mode: bool = False) -> str:
        """Get response from OpenAI API with style and strict mode considerations"""
        try:
            if strict_mode:
                max_tokens = 200
                temperature = 0.1
            elif response_style == "simple":
                max_tokens = 500
                temperature = 0.3
            else:
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
                         detail_level: str = "Comprehensive",
                         include_diagrams: bool = False,
                         format_tables: bool = False) -> str:
        """Generate document using DocumentGenerator"""
        project_name = project["product_name"]
        
        document = self.document_generator.generate_document(
            project=project,
            document_type=document_type,
            detail_level=detail_level,
            # include_diagrams=include_diagrams,
            format_tables=format_tables
        )
        
        self.add_to_history(
            project_name,
            f"Generate {document_type} ({detail_level})",
            f"Generated {document_type} document",
            f"document_{document_type.lower().replace(' ', '_')}",
            "detailed"
        )
        
        return document.replace("**", "")

    
    def save_document_to_folder(self, document: str, project_name: str, 
                               document_type: str, detail_level: str = "Comprehensive"):
        """Save document to folder structure"""
        from datetime import datetime
        
        folder_structure = {
            "Business Requirements Document (BRD)": "BRD",
            "Functional Requirements Document (FRD)": "FRD",
            "Non-Functional Requirements (NFR)": "NFR",
            "Technical Specification Document": "Technical_Specs",
            "User Stories & Acceptance Criteria": "User_Stories",
            "Stakeholder Analysis Matrix": "Stakeholder_Analysis",
            "SWOT Analysis Report": "SWOT_Analysis",
            "Process Flow Diagrams (BPMN)": "Process_Flows",
            "System Architecture Document": "System_Architecture",
            "Project Charter & Scope": "Project_Charter"
        }
        
        base_folder = "generated_documents"
        doc_folder = folder_structure.get(document_type, "Other_Documents")
        
        project_folder = os.path.join(base_folder, project_name, doc_folder)
        os.makedirs(project_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{document_type.replace(' ', '_')}_{detail_level}_{timestamp}.md"
        filepath = os.path.join(project_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document)
        
        return filepath
    
    def get_chat_history_summary(self, project_name: str) -> str:
        """Get a summary of chat history for a project"""
        history = self.get_project_history(project_name)
        if not history:
            return "No recent chat history available for this project."
        
        summary = f"Chat History Summary for '{project_name}':\n"
        summary += f"Total conversations: {len(history)}\n\n"
        
        for i, entry in enumerate(history[-5:], 1):  # Last 5 entries
            timestamp = entry.get("timestamp", "Unknown time")
            user_input = entry.get("user_input", "")[:100] + "..." if len(entry.get("user_input", "")) > 100 else entry.get("user_input", "")
            
            summary += f"{i}. [{timestamp}] User: {user_input}\n"
            summary += f"   Type: {entry.get('analysis_type', 'general')}\n"
        
        return summary
    
    def export_chat_history(self, project_name: str, format: str = "json") -> str:
        """Export chat history for a project in specified format"""
        history = self.get_project_history(project_name)
        
        if format.lower() == "json":
            return json.dumps(history, indent=2)
        elif format.lower() == "text":
            text_output = f"Chat History Export for '{project_name}'\n"
            text_output += f"Generated: {self.get_timestamp()}\n"
            text_output += "=" * 50 + "\n\n"
            
            for entry in history:
                text_output += f"Timestamp: {entry.get('timestamp')}\n"
                text_output += f"Analysis Type: {entry.get('analysis_type')}\n"
                text_output += f"Style: {entry.get('response_style')}\n"
                text_output += f"User: {entry.get('user_input')}\n"
                text_output += f"Agent: {entry.get('agent_response')}\n"
                text_output += "-" * 40 + "\n"
            
            return text_output
        else:
            return "Unsupported format. Use 'json' or 'text'."

# Optional cleanup scheduler function
def start_cleanup_scheduler(agent: BusinessAnalystAgent, interval_hours: int = 1):
    """Start a scheduler to clean up old histories at regular intervals"""
    import threading
    import time
    
    def cleanup_task():
        while True:
            time.sleep(interval_hours * 3600)  # Convert hours to seconds
            print(f"Running scheduled cleanup of histories older than 24 hours...")
            agent.cleanup_old_histories()
            print("Cleanup completed.")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    return cleanup_thread