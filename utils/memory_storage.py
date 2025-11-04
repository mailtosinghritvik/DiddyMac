"""
Memory Storage for intermediate results and context
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

class MemoryStorage:
    """
    Manages intermediate results and context storage
    """
    
    def __init__(self, memory_dir: str = None):
        """
        Initialize memory storage
        
        Args:
            memory_dir: Directory to store memory (defaults to agent_memory)
        """
        if memory_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_dir = os.path.join(project_root, "agent_memory")
        
        self.memory_dir = memory_dir
        self.intermediate_dir = os.path.join(memory_dir, "intermediate_results")
        self.context_dir = os.path.join(memory_dir, "context")
        
        os.makedirs(self.intermediate_dir, exist_ok=True)
        os.makedirs(self.context_dir, exist_ok=True)
    
    def store_intermediate_result(self, request_id: str, agent_name: str, result: Dict[str, Any]):
        """
        Store intermediate result from an agent
        
        Args:
            request_id: Request identifier
            agent_name: Name of the agent
            result: Result data to store
        """
        filename = f"{request_id}_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.intermediate_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "request_id": request_id,
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }, f, indent=2, default=str)
    
    def get_intermediate_results(self, request_id: str) -> list:
        """
        Get all intermediate results for a request
        
        Args:
            request_id: Request identifier
        
        Returns:
            List of intermediate results
        """
        results = []
        
        for filename in os.listdir(self.intermediate_dir):
            if filename.startswith(request_id):
                filepath = os.path.join(self.intermediate_dir, filename)
                with open(filepath, 'r') as f:
                    results.append(json.load(f))
        
        return sorted(results, key=lambda x: x.get("timestamp", ""))
    
    def store_context(self, request_id: str, context: Dict[str, Any]):
        """
        Store context for a request
        
        Args:
            request_id: Request identifier
            context: Context data
        """
        filename = f"{request_id}_context.json"
        filepath = os.path.join(self.context_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "context": context
            }, f, indent=2, default=str)
    
    def get_context(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context for a request
        
        Args:
            request_id: Request identifier
        
        Returns:
            Context data or None
        """
        filename = f"{request_id}_context.json"
        filepath = os.path.join(self.context_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get("context")

