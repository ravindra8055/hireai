import os
import nltk
from pyresparser import ResumeParser
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re
import json

class ResumeParser:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Initialize skill mappings
        self.skill_mappings = {
            # Programming Languages
            'js': 'javascript',
            'typescript': 'typescript',
            'ts': 'typescript',
            'py': 'python',
            'c#': 'csharp',
            'c++': 'cpp',
            'c plus plus': 'cpp',
            'ruby on rails': 'ruby',
            'ror': 'ruby',
            
            # Databases
            'postgres': 'postgresql',
            'postgresql': 'postgresql',
            'mssql': 'sql server',
            'ms sql': 'sql server',
            'mysql': 'mysql',
            'mongodb': 'mongodb',
            'nosql': 'nosql',
            
            # Cloud Platforms
            'aws': 'amazon web services',
            'azure': 'microsoft azure',
            'gcp': 'google cloud platform',
            'google cloud': 'google cloud platform',
            
            # Web Technologies
            'react.js': 'react',
            'reactjs': 'react',
            'react js': 'react',
            'angular.js': 'angular',
            'angularjs': 'angular',
            'vue.js': 'vue',
            'vuejs': 'vue',
            'node.js': 'nodejs',
            'node js': 'nodejs',
            'express.js': 'express',
            'expressjs': 'express',
            
            # Machine Learning
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'deep learning': 'deep learning',
            'dl': 'deep learning',
            'nlp': 'natural language processing',
            'computer vision': 'computer vision',
            'cv': 'computer vision',
            
            # DevOps
            'ci/cd': 'continuous integration',
            'cicd': 'continuous integration',
            'docker': 'docker',
            'kubernetes': 'kubernetes',
            'k8s': 'kubernetes',
            
            # Methodologies
            'agile': 'agile methodology',
            'scrum': 'scrum methodology',
            'waterfall': 'waterfall methodology',
            'devops': 'devops',
            'git': 'git',
            'github': 'git',
            'gitlab': 'git',
        }

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Normalize and clean a list of skills.
        
        Args:
            skills (List[str]): List of skills to normalize
            
        Returns:
            List[str]: Normalized list of skills
        """
        if not skills:
            return []
            
        normalized_skills = set()
        
        for skill in skills:
            if not isinstance(skill, str):
                continue
                
            # Convert to lowercase and remove special characters
            skill = re.sub(r'[^\w\s]', ' ', skill.lower())
            
            # Split on common delimiters
            skill_parts = re.split(r'[,/&+]', skill)
            
            for part in skill_parts:
                # Clean and normalize each part
                part = part.strip()
                if not part or len(part) < 2:  # Skip empty or single-character skills
                    continue
                    
                # Check for common variations
                normalized = self.skill_mappings.get(part, part)
                
                # Remove common words that aren't skills
                if normalized not in {'and', 'or', 'with', 'using', 'via', 'through'}:
                    normalized_skills.add(normalized)
        
        # Sort skills alphabetically
        return sorted(list(normalized_skills))

    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from a text string.
        
        Args:
            text (str): Text to extract skills from
            
        Returns:
            List[str]: List of extracted skills
        """
        if not text:
            return []
            
        # Convert to lowercase
        text = text.lower()
        
        # Find all potential skills
        found_skills = set()
        
        # Check for each skill in the mappings
        for skill, normalized in self.skill_mappings.items():
            if skill in text:
                found_skills.add(normalized)
        
        return sorted(list(found_skills))

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume file and extract structured information using pyresparser
        
        Args:
            file_path (str): Path to the resume file (PDF or DOCX)
            
        Returns:
            Dict[str, Any]: Structured resume data
        """
        try:
            # Parse resume using pyresparser
            data = ResumeParser(file_path).get_extracted_data()
            
            # Extract and normalize skills from different sources
            skills_from_parser = data.get('skills', [])
            skills_from_experience = []
            
            # Extract skills from experience descriptions
            for exp in data.get('experience', []):
                if isinstance(exp, str):
                    skills_from_experience.extend(self.extract_skills_from_text(exp))
            
            # Combine and normalize all skills
            all_skills = skills_from_parser + skills_from_experience
            normalized_skills = self.normalize_skills(all_skills)
            
            # Convert to our standardized format
            parsed_data = {
                "name": data.get('name', ''),
                "email": data.get('email', ''),
                "phone": data.get('phone_number', ''),
                "skills": normalized_skills,  # Use normalized skills
                "education": self._process_education(data.get('degree', [])),
                "experience": self._process_experience(data.get('experience', [])),
                "location": data.get('location', ''),
                "total_experience": data.get('total_experience', 0),
                "company_names": data.get('company_names', []),
                "designation": data.get('designation', []),
                "raw_data": data  # Keep raw data for reference
            }
            
            return parsed_data
            
        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    def _process_skills(self, skills: List[str]) -> List[str]:
        """Process and clean skills list"""
        if not skills:
            return []
            
        # Clean and standardize skills
        cleaned_skills = []
        for skill in skills:
            # Remove special characters and extra spaces
            skill = re.sub(r'[^\w\s]', '', skill).strip()
            if skill and len(skill) > 1:  # Avoid single characters
                cleaned_skills.append(skill.lower())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(cleaned_skills))

    def _process_education(self, degrees: List[str]) -> List[Dict[str, Any]]:
        """Process education information"""
        education = []
        for degree in degrees:
            if isinstance(degree, str):
                # Try to extract degree and field of study
                degree_parts = degree.split(' in ')
                if len(degree_parts) > 1:
                    degree_name = degree_parts[0].strip()
                    field = degree_parts[1].strip()
                else:
                    degree_name = degree.strip()
                    field = "Unknown"
                
                education.append({
                    "degree": degree_name,
                    "field_of_study": field,
                    "institution": "Unknown",  # pyresparser doesn't extract this
                    "start_date": None,
                    "end_date": None,
                    "gpa": None
                })
        
        return education

    def _process_experience(self, experiences: List[str]) -> List[Dict[str, Any]]:
        """Process work experience information"""
        processed_experiences = []
        
        for exp in experiences:
            if isinstance(exp, str):
                # Try to extract company and title
                company = "Unknown"
                title = "Unknown"
                
                # Look for common patterns in experience text
                if " at " in exp:
                    parts = exp.split(" at ")
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif " with " in exp:
                    parts = exp.split(" with ")
                    title = parts[0].strip()
                    company = parts[1].strip()
                
                processed_experiences.append({
                    "company": company,
                    "title": title,
                    "description": exp,
                    "start_date": None,
                    "end_date": None,
                    "skills": []  # Could be extracted from description if needed
                })
        
        return processed_experiences

    def save_to_json(self, parsed_data: Dict[str, Any], output_path: str) -> None:
        """Save parsed resume data to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error saving parsed data: {str(e)}")

    def load_from_json(self, json_path: str) -> Dict[str, Any]:
        """Load parsed resume data from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading parsed data: {str(e)}") 