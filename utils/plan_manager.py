"""
Plan Manager for task planning and tracking
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class PlanManager:
    """
    Manages task plans and execution tracking
    """
    
    def __init__(self, plan_dir: str = None):
        """
        Initialize plan manager
        
        Args:
            plan_dir: Directory to store plans (defaults to agent_memory/plans)
        """
        if plan_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            plan_dir = os.path.join(project_root, "agent_memory", "plans")
        
        self.plan_dir = plan_dir
        os.makedirs(self.plan_dir, exist_ok=True)
    
    def create_plan(self, request_id: str, tasks: List[Dict]) -> str:
        """
        Create a new plan
        
        Args:
            request_id: Unique identifier for the request
            tasks: List of task dictionaries with name, description
        
        Returns:
            Plan ID
        """
        plan_id = f"plan_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = {
            "id": plan_id,
            "created_at": datetime.now().isoformat(),
            "request_id": request_id,
            "tasks": [
                {
                    "id": f"task_{i}",
                    "name": task.get("name", f"Task {i+1}"),
                    "description": task.get("description", ""),
                    "status": TaskStatus.PENDING.value,
                    "created_at": datetime.now().isoformat()
                }
                for i, task in enumerate(tasks)
            ]
        }
        
        # Save plan
        plan_file = os.path.join(self.plan_dir, f"{plan_id}.json")
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        
        return plan_id
    
    def update_task_status(self, plan_id: str, task_id: str, status: TaskStatus, result: Optional[Dict] = None):
        """
        Update task status
        
        Args:
            plan_id: Plan identifier
            task_id: Task identifier
            status: New task status
            result: Optional result data
        """
        plan_file = os.path.join(self.plan_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_file):
            return
        
        with open(plan_file, 'r') as f:
            plan = json.load(f)
        
        # Update task
        for task in plan["tasks"]:
            if task["id"] == task_id:
                task["status"] = status.value
                task["updated_at"] = datetime.now().isoformat()
                if result:
                    task["result"] = result
                break
        
        # Save updated plan
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """
        Get plan by ID
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Plan dictionary or None
        """
        plan_file = os.path.join(self.plan_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_file):
            return None
        
        with open(plan_file, 'r') as f:
            return json.load(f)

