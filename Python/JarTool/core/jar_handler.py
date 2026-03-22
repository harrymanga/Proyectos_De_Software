"""
Jar Handler Module
Manages JAR file operations using the jar command-line tool
"""

import os
import subprocess
import tempfile
from typing import List, Optional


class JarHandler:
    """Handles JAR file extraction and compression using jar command"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def extract_jar(self, jar_path: str, output_dir: Optional[str] = None) -> bool:
        """
        Extract a JAR file to specified directory
        
        Args:
            jar_path: Path to JAR file
            output_dir: Output directory (optional, defaults to jar_name_extracted)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(jar_path):
            return False
        
        if not output_dir:
            jar_name = os.path.splitext(os.path.basename(jar_path))[0]
            output_dir = f"{jar_name}_extracted"
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Use jar command to extract
            cmd = ['jar', 'xfv', jar_path]
            result = subprocess.run(
                cmd, 
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def extract_multiple_jars(self, jar_paths: List[str], base_output_dir: Optional[str] = None) -> dict:
        """
        Extract multiple JAR files
        
        Args:
            jar_paths: List of JAR file paths
            base_output_dir: Base directory for extractions (optional)
            
        Returns:
            dict: Results with jar paths as keys and success status as values
        """
        results = {}
        
        for jar_path in jar_paths:
            if not os.path.exists(jar_path):
                results[jar_path] = False
                continue
                
            jar_name = os.path.splitext(os.path.basename(jar_path))[0]
            
            if base_output_dir:
                output_dir = os.path.join(base_output_dir, jar_name)
            else:
                output_dir = f"{jar_name}_extracted"
            
            results[jar_path] = self.extract_jar(jar_path, output_dir)
        
        return results
    
    def create_jar(self, folder_path: str, jar_path: Optional[str] = None) -> bool:
        """
        Create JAR file from folder
        
        Args:
            folder_path: Path to folder to compress
            jar_path: Output JAR path (optional, defaults to folder_name.jar)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.isdir(folder_path):
            return False
        
        if not jar_path:
            jar_path = f"{os.path.basename(folder_path)}.jar"
        
        try:
            # Create manifest file
            manifest_content = "Manifest-Version: 1.0\nCreated-By: JarTool\n"
            manifest_path = os.path.join(self.temp_dir, "MANIFEST.MF")
            
            with open(manifest_path, 'w') as f:
                f.write(manifest_content)
            
            # Use jar command to create JAR
            cmd = ['jar', 'cfm', jar_path, manifest_path, '-C', folder_path, '.']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Clean up manifest
            os.remove(manifest_path)
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def create_multiple_jars(self, folder_paths: List[str], base_output_dir: Optional[str] = None) -> dict:
        """
        Create multiple JAR files from folders
        
        Args:
            folder_paths: List of folder paths
            base_output_dir: Base directory for JAR files (optional)
            
        Returns:
            dict: Results with folder paths as keys and success status as values
        """
        results = {}
        
        for folder_path in folder_paths:
            if not os.path.isdir(folder_path):
                results[folder_path] = False
                continue
                
            folder_name = os.path.basename(folder_path)
            
            if base_output_dir:
                jar_path = os.path.join(base_output_dir, f"{folder_name}.jar")
            else:
                jar_path = f"{folder_name}.jar"
            
            results[folder_path] = self.create_jar(folder_path, jar_path)
        
        return results
    
    def get_jar_contents(self, jar_path: str) -> List[str]:
        """
        Get list of files in JAR
        
        Args:
            jar_path: Path to JAR file
            
        Returns:
            List[str]: List of file paths in JAR
        """
        if not os.path.exists(jar_path):
            return []
        
        try:
            cmd = ['jar', 'tf', jar_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                return []
                
        except Exception:
            return []
