import os
from supabase import create_client, Client
from typing import Dict, List, Optional, Any

# Load environment variables (supports both .env and AWS Parameter Store)
from utils.aws_env_loader import ensure_env_vars_loaded
ensure_env_vars_loaded()

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client from environment variables"""
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(url, key)
    
    def insert_input(self, user: str, source: str, input_text: str, subject: Optional[str]) -> Dict[str, Any]:
        """
        Insert a new input record into input_db table
        
        Args:
            user: User identifier
            source: Source of the message (email, whatsapp, etc.)
            input_text: The actual message content
            subject: Subject line (can be None for WhatsApp messages)
        
        Returns:
            Inserted record with id and created_at
        """
        try:
            response = (
                self.client.table("input_db")
                .insert({
                    "user": user,
                    "source": source,
                    "input": input_text,
                    "subject": subject
                })
                .execute()
            )
            return response.data[0] if response.data else {}
        except Exception as e:
            raise Exception(f"Failed to insert input: {str(e)}")
    
    def get_message_history(self, user: str, source: str, subject: Optional[str], current_created_at: str) -> Dict[str, Any]:
        """
        Get message history for building context
        
        Args:
            user: User identifier
            source: Current message source
            subject: Current message subject (can be None)
            current_created_at: Timestamp of current message to exclude it from history
        
        Returns:
            Dictionary with before_last_message_same_user_same_source_different_subject and last_message_same_user_different_source
        """
        history = {
            "before_last_message_same_user_same_source_different_subject": [],
            "last_message_same_user_different_source": []
        }
        
        try:
            # Get before-last message: same user, same source, different subject (unless source is NULL)
            # If source is NULL, can be same subject
            query = (
                self.client.table("input_db")
                .select("input, source, created_at")
                .eq("user", user)
                .eq("source", source)
                .lt("created_at", current_created_at)
                .order("created_at", desc=True)
            )
            
            # If subject is not None, filter by different subject
            if subject is not None:
                query = query.neq("subject", subject)
            
            response = query.limit(1).execute()
            
            if response.data:
                history["before_last_message_same_user_same_source_different_subject"] = response.data
            
            # Get last message from same user but different source
            response = (
                self.client.table("input_db")
                .select("input, source, created_at")
                .eq("user", user)
                .neq("source", source)
                .lt("created_at", current_created_at)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if response.data:
                history["last_message_same_user_different_source"] = response.data
            
            return history
        
        except Exception as e:
            raise Exception(f"Failed to get message history: {str(e)}")
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """
        Fetch all rules from rules_db table
        
        Returns:
            List of all rule records
        """
        try:
            response = (
                self.client.table("rules_db")
                .select("*")
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get rules: {str(e)}")
    
    def insert_rule(self, rule_maker: str, rule_org: str, rule_instruction: str) -> Dict[str, Any]:
        """
        Insert a new rule into rules_db table
        
        Args:
            rule_maker: Who created the rule
            rule_org: Organization or context for the rule
            rule_instruction: The actual rule instruction
        
        Returns:
            Inserted rule record
        """
        try:
            response = (
                self.client.table("rules_db")
                .insert({
                    "rule_maker": rule_maker,
                    "rule_org": rule_org,
                    "rule_instruction": rule_instruction
                })
                .execute()
            )
            return response.data[0] if response.data else {}
        except Exception as e:
            raise Exception(f"Failed to insert rule: {str(e)}")

