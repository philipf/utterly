import os
import sys
import subprocess
import logging

class FileOpener:
    @staticmethod
    def open_file(path: str):
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                if sys.platform == 'darwin':
                    subprocess.run(['open', path])
                else:
                    subprocess.run(['xdg-open', path])
        except Exception as e:
            logging.warning(f"Could not open file '{path}': {e}")