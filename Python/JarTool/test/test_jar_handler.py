"""
Test Jar Handler Module
Tests for JAR file operations
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jar_handler import JarHandler


class TestJarHandler(unittest.TestCase):
    """Test cases for JarHandler class"""
    
    def setUp(self):
        """Setup test environment"""
        self.jar_handler = JarHandler()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test JarHandler initialization"""
        self.assertIsNotNone(self.jar_handler.temp_dir)
        self.assertTrue(os.path.exists(self.jar_handler.temp_dir))
    
    @patch('subprocess.run')
    def test_extract_jar_success(self, mock_run):
        """Test successful JAR extraction"""
        # Mock successful subprocess run
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        
        # Create a fake JAR file
        jar_path = os.path.join(self.temp_dir, "test.jar")
        with open(jar_path, 'w') as f:
            f.write("fake jar content")
        
        output_dir = os.path.join(self.temp_dir, "extracted")
        
        result = self.jar_handler.extract_jar(jar_path, output_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_dir))
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_extract_jar_file_not_exists(self, mock_run):
        """Test JAR extraction with non-existent file"""
        result = self.jar_handler.extract_jar("non_existent.jar")
        
        self.assertFalse(result)
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_extract_jar_subprocess_error(self, mock_run):
        """Test JAR extraction with subprocess error"""
        # Mock failed subprocess run
        mock_run.return_value.returncode = 1
        
        # Create a fake JAR file
        jar_path = os.path.join(self.temp_dir, "test.jar")
        with open(jar_path, 'w') as f:
            f.write("fake jar content")
        
        result = self.jar_handler.extract_jar(jar_path)
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_create_jar_success(self, mock_run):
        """Test successful JAR creation"""
        # Mock successful subprocess run
        mock_run.return_value.returncode = 0
        
        # Create a test folder
        folder_path = os.path.join(self.temp_dir, "test_folder")
        os.makedirs(folder_path)
        
        # Create a test file in the folder
        test_file = os.path.join(folder_path, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        jar_path = os.path.join(self.temp_dir, "test.jar")
        
        result = self.jar_handler.create_jar(folder_path, jar_path)
        
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    def test_create_jar_folder_not_exists(self):
        """Test JAR creation with non-existent folder"""
        result = self.jar_handler.create_jar("non_existent_folder")
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_get_jar_contents_success(self, mock_run):
        """Test getting JAR contents successfully"""
        # Mock successful subprocess run
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "file1.txt\nfile2.txt\nMETA-INF/\n"
        
        # Create a fake JAR file
        jar_path = os.path.join(self.temp_dir, "test.jar")
        with open(jar_path, 'w') as f:
            f.write("fake jar content")
        
        contents = self.jar_handler.get_jar_contents(jar_path)
        
        self.assertEqual(contents, ["file1.txt", "file2.txt", "META-INF/"])
        mock_run.assert_called_once()
    
    def test_get_jar_contents_file_not_exists(self):
        """Test getting JAR contents with non-existent file"""
        contents = self.jar_handler.get_jar_contents("non_existent.jar")
        
        self.assertEqual(contents, [])
    
    @patch('subprocess.run')
    def test_extract_multiple_jars(self, mock_run):
        """Test extracting multiple JAR files"""
        # Mock successful subprocess run
        mock_run.return_value.returncode = 0
        
        # Create fake JAR files
        jar_paths = []
        for i in range(3):
            jar_path = os.path.join(self.temp_dir, f"test{i}.jar")
            with open(jar_path, 'w') as f:
                f.write(f"fake jar content {i}")
            jar_paths.append(jar_path)
        
        results = self.jar_handler.extract_multiple_jars(jar_paths)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(results.values()))
        self.assertEqual(mock_run.call_count, 3)
    
    @patch('subprocess.run')
    def test_create_multiple_jars(self, mock_run):
        """Test creating multiple JAR files"""
        # Mock successful subprocess run
        mock_run.return_value.returncode = 0
        
        # Create test folders
        folder_paths = []
        for i in range(3):
            folder_path = os.path.join(self.temp_dir, f"folder{i}")
            os.makedirs(folder_path)
            
            test_file = os.path.join(folder_path, f"test{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"test content {i}")
            
            folder_paths.append(folder_path)
        
        results = self.jar_handler.create_multiple_jars(folder_paths)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(results.values()))
        self.assertEqual(mock_run.call_count, 3)


if __name__ == '__main__':
    unittest.main()
