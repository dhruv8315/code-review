import subprocess
import json
import logging

class SecurityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run_bandit_scan(self, target_path='.'):
        try:
            command = ['bandit', '-r', target_path, '-f', 'json']
            result  = subprocess.run(command, capture_output=True, text=True)

            if result.stdout:
                output = json.loads(result.stdout)
                self.logger.info(f"File: {__file__} Bandit scan completed with output.")
                return output
            
            self.logger.info(f"File: {__file__} Bandit scan completed with no output.")
            return {}
        
        except Exception as e:
            self.logger.error(f"File: {__file__} Error running Bandit: {e}")
            return None