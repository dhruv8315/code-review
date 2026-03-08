import subprocess
import os
import json
import logging

class StaticAnalysisService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run_analysis(self, project_path):
        try:

            command = [ "semgrep", "scan", "--config", "auto", "--json"]
            
            # Run the static analysis tool (e.g., Bandit for Python)
            result = subprocess.run(command, capture_output=True, text=True)
            if result.stdout :
                output = json.loads(result.stdout)
                self.logger.info(f"File: {__file__} Static analysis completed with output.")
                return output
            
            self.logger.info(f"File: {__file__} Static analysis completed with no output.")
            return{}
            
        except Exception as e:
            self.logger.exception(f"File: {__file__} Error running static analysis: {e}")
            return None