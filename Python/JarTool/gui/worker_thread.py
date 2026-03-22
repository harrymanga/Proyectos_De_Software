"""
Worker Thread Module
Background processing for JAR operations
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QThread, pyqtSignal
from core import JarHandler


class JarWorkerThread(QThread):
    """Worker thread for JAR operations"""
    
    # Signals
    progress_updated = pyqtSignal(int, int, str)  # current, total, current_file
    operation_completed = pyqtSignal(dict)  # results
    operation_failed = pyqtSignal(str)  # error message
    log_message = pyqtSignal(str)  # log message
    
    def __init__(self, operation_type, paths, output_dir=None):
        super().__init__()
        self.operation_type = operation_type  # 'extract' or 'compress'
        self.paths = paths
        self.output_dir = output_dir
        self.jar_handler = JarHandler()
        self.should_stop = False
    
    def run(self):
        """Execute the operation in background"""
        try:
            if self.operation_type == 'extract':
                self.extract_files()
            elif self.operation_type == 'compress':
                self.compress_folders()
        except Exception as e:
            self.operation_failed.emit(str(e))
    
    def extract_files(self):
        """Extract multiple JAR files"""
        total_files = len(self.paths)
        
        for i, jar_path in enumerate(self.paths):
            if self.should_stop:
                break
            
            # Emit progress
            self.progress_updated.emit(i + 1, total_files, os.path.basename(jar_path))
            self.log_message.emit(f"Extracting: {os.path.basename(jar_path)}")
            
            # Extract file
            jar_name = os.path.splitext(os.path.basename(jar_path))[0]
            
            if self.output_dir:
                output_path = os.path.join(self.output_dir, jar_name)
            else:
                output_path = f"{jar_name}_extracted"
            
            success = self.jar_handler.extract_jar(jar_path, output_path)
            
            if not success:
                self.log_message.emit(f"Failed to extract: {jar_path}")
        
        # Emit completion
        self.progress_updated.emit(total_files, total_files, "Complete")
        self.operation_completed.emit({"status": "completed", "processed": total_files})
    
    def compress_folders(self):
        """Compress multiple folders"""
        total_folders = len(self.paths)
        
        for i, folder_path in enumerate(self.paths):
            if self.should_stop:
                break
            
            # Emit progress
            self.progress_updated.emit(i + 1, total_folders, os.path.basename(folder_path))
            self.log_message.emit(f"Compressing: {os.path.basename(folder_path)}")
            
            # Compress folder
            folder_name = os.path.basename(folder_path)
            
            if self.output_dir:
                jar_path = os.path.join(self.output_dir, f"{folder_name}.jar")
            else:
                jar_path = f"{folder_name}.jar"
            
            success = self.jar_handler.create_jar(folder_path, jar_path)
            
            if not success:
                self.log_message.emit(f"Failed to compress: {folder_path}")
        
        # Emit completion
        self.progress_updated.emit(total_folders, total_folders, "Complete")
        self.operation_completed.emit({"status": "completed", "processed": total_folders})
    
    def stop(self):
        """Stop the operation"""
        self.should_stop = True
