import subprocess
import os
import json
import re
from pathlib import Path, PurePosixPath

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

# Characters invalid in Windows file names (<>:"/\|?*), control characters,
# and characters that break the generated links / CSS url() (#, %, ').
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*#%\'\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10)),
}

class Helper:     
    def __init__(self, fname = '.credentials.json', path = SCRIPT_PATH):
        self.fname = fname
        self.path = path
        pass
    
    @staticmethod
    def sanitize_filename(name, default='untitled'):
        """
        Converts user input into a name that is safe to use as a file name on
        Windows, Linux and macOS, and inside the generated html links.
        Spaces are replaced by underscores.
        """
        fname = re.sub(r'\s+', ' ', str(name))
        fname = INVALID_FILENAME_CHARS.sub('', fname)
        # Windows does not allow trailing dots or spaces
        fname = fname.strip().rstrip('. ').replace(' ', '_')
        if fname.split('.')[0].upper() in WINDOWS_RESERVED_NAMES:
            fname = f'_{fname}'
        return fname or default

    @staticmethod
    def web_path(*parts):
        """
        Joins path parts using forward slashes, as expected by html / css,
        regardless of the operating system.
        """
        return PurePosixPath(*parts).as_posix()

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
    
    def git_status(self):
        result = subprocess.run(["git", "status", "-s"], cwd=self.path, capture_output=True, text=True)
        return result.stdout

    def git_discard(self):
        result = subprocess.run(["git", "restore", "--staged", "."], cwd=self.path, capture_output=True, text=True)
        result = subprocess.run(["git", "clean", "-f", "."], cwd=self.path, capture_output=True, text=True)
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


    
