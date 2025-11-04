import logging
import os
import json
from datetime import datetime
from typing import Any, Dict

class AgentLogger:
    def __init__(self, run_id: str = None):
        """
        Initialize logger with timestamped output directory
        
        Args:
            run_id: Optional run identifier, defaults to timestamp
        """
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.run_id = run_id
        # Use relative path from project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(project_root, "test_outputs", run_id)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(f"agent_logger_{run_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(f"{self.output_dir}/full_log.txt")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        if level == "DEBUG":
            self.logger.debug(message)
        elif level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
    
    def save_json(self, filename: str, data: Any):
        """Save data as JSON file in output directory"""
        filepath = f"{self.output_dir}/{filename}"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        self.log(f"Saved {filename}")
    
    def save_text(self, filename: str, text: str):
        """Save text to file in output directory"""
        filepath = f"{self.output_dir}/{filename}"
        with open(filepath, 'w') as f:
            f.write(text)
        self.log(f"Saved {filename}")
    
    def get_output_dir(self) -> str:
        """Get the output directory path"""
        return self.output_dir

