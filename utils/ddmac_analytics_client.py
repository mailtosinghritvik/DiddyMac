"""
DDMac Analytics Supabase Client
Separate client for DDMac Analytics database (different from communication database)
"""
import os
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import pandas as pd

# Load environment variables (supports both .env and AWS Parameter Store)
from utils.aws_env_loader import ensure_env_vars_loaded
ensure_env_vars_loaded()

class DDMacAnalyticsClient:
    """Client for DDMac Analytics Supabase database"""
    
    def __init__(self):
        """Initialize DDMac Analytics Supabase client from environment variables"""
        url: str = os.environ.get("DDMAC_ANALYTICS_SUPABASE_URL")
        key: str = os.environ.get("DDMAC_ANALYTICS_SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("DDMAC_ANALYTICS_SUPABASE_URL and DDMAC_ANALYTICS_SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(url, key)
    
    def execute_rpc(self, function_name: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute Supabase RPC function
        
        Args:
            function_name: Name of the RPC function
            params: Parameters for the function
        
        Returns:
            List of result dictionaries
        """
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to execute RPC {function_name}: {str(e)}")
    
    def query_table(self, table_name: str, select_cols: str = "*", filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query a table with optional filters
        
        Args:
            table_name: Name of the table
            select_cols: Columns to select (default: *)
            filters: Dictionary of {column: value} filters
        
        Returns:
            List of result dictionaries
        """
        try:
            query = self.client.table(table_name).select(select_cols)
            
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to query table {table_name}: {str(e)}")
    
    def get_employee_list(self) -> List[Dict[str, Any]]:
        """Get list of all active employees"""
        try:
            response = self.client.table("users").select("id, username").eq("active", "TRUE").execute()
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get employee list: {str(e)}")
    
    def get_job_list(self) -> List[Dict[str, Any]]:
        """Get list of all jobs/projects"""
        try:
            response = self.client.table("jobcodes").select("id, name").execute()
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get job list: {str(e)}")
    
    def insert_task_progress(self, task_id: int, progress: float) -> Dict[str, Any]:
        """
        Insert task progress update
        
        Args:
            task_id: Task ID from accubid_breakdowns
            progress: Progress percentage (0-100)
        
        Returns:
            Inserted record
        """
        try:
            response = self.client.table("task_progress").insert({
                "task_id": task_id,
                "progress": progress
            }).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            raise Exception(f"Failed to insert task progress: {str(e)}")
    
    def get_latest_task_progress(self, task_id: int) -> Optional[float]:
        """
        Get latest progress for a task
        
        Args:
            task_id: Task ID
        
        Returns:
            Latest progress percentage or None
        """
        try:
            response = (
                self.client.table("task_progress")
                .select("progress, created_at")
                .eq("task_id", task_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("progress", 0)
            return None
        except Exception as e:
            raise Exception(f"Failed to get task progress: {str(e)}")

