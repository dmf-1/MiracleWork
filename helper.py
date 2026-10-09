import subprocess
import os
import json
from pathlib import Path

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

class Helper:     
    def __init__(self, fname = '.credentials.json', path = SCRIPT_PATH):
        self.fname = fname
        self.path = path
        pass
    
    def load_credentials(self):
        if os.path.exists(self.fname):
            with open(self.fname, 'r') as of:
                self.credentials = json.load(of)
        else:
            self.credentials = {"name": "", "username": "", "is_password_set": False}
            with open(Path(self.path,self.fname), 'w') as of:
                json.dump(self.credentials, of)
    
    def is_password_set(self):
        return self.credentials['is_password_set']
    
    def set_publisher_name(self, name):
        self.credentials['name'] = name
        with open(Path(self.path,self.fname), 'w') as of:
            json.dump(self.credentials, of)
    
    def toggle_password_set(self):
        self.credentials["is_password_set"] = not self.credentials["is_password_set"] == True
        with open(self.fname, 'w') as op:
            json.dump(self.credentials, op)
    
    def git_discard(self):
        result = subprocess.run(["git", "restore", "."], cwd=self.path, capture_output=True, text=True)
        return result.stdout
    
    def git_pull(self):
        result = subprocess.run(["git", "reset", "--soft", "HEAD~1"], cwd=self.path, capture_output=True, text=True)
        result = subprocess.run(["git", "pull"], cwd=self.path, capture_output=True, text=True)
        return result.stdout
    
    def git_add(self):
        result = subprocess.run(["git", "add", "."], cwd=self.path, capture_output=True, text=True)
        return result.stdout
    
    def git_commit(self):
        result = subprocess.run(["git", "commit", "-m", "Auto commit"], cwd=self.path, capture_output=True, text=True)
        return result.stdout
    
    def git_push(self):
        result = subprocess.run(["git", "push"], cwd=self.path, capture_output=True, text=True)
        return result.stdout


    