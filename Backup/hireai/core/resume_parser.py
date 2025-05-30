import os
import spacy
from typing import List, Dict, Any
import re
from pathlib import Path
import shutil
import docx2txt
from pdfminer.high_level import extract_text
from datetime import datetime

class ResumeParser:
    def __init__(self):
        """Initialize the resume parser"""
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, download it
            print("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        # Create config directory if it doesn't exist
        self.config_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Create config file if it doesn't exist
        self.config_file = self.config_dir / "config.cfg"
        if not self.config_file.exists():
            self._create_config_file()

    def _create_config_file(self):
        """Create the config file for resume parsing"""
        config_content = """[DEFAULT]
# Resume parsing configuration
skills_file = skills.txt
education_file = education.txt
experience_file = experience.txt

[PARSER]
# Parser settings
min_skill_length = 2
max_skill_length = 50
min_experience_length = 10
max_experience_length = 1000

[OUTPUT]
# Output settings
output_format = json
include_raw_text = false
"""
        with open(self.config_file, "w") as f:
            f.write(config_content)

    def _read_file(self, file_path: str) -> str:
        """
        Read text from different file formats
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Extracted text
        """
        print(f"Reading file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_extension = os.path.splitext(file_path)[1].lower()
        print(f"File extension: {file_extension}")
        
        try:
            text = None
            if file_extension == '.pdf':
                print("Processing PDF file...")
                text = extract_text(file_path)
            elif file_extension == '.docx':
                print("Processing DOCX file...")
                text = docx2txt.process(file_path)
            elif file_extension == '.txt':
                print("Processing TXT file...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
            if not text:
                raise ValueError("Could not extract text from file")
                
            if not isinstance(text, str):
                raise ValueError(f"Invalid text type: {type(text)}")
                
            text = text.strip()
            print(f"Successfully extracted text, length: {len(text)}")
            return text
            
        except Exception as e:
            import traceback
            error_msg = f"Error reading file: {str(e)}\nTraceback: {traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file and extract relevant information"""
        try:
            print(f"Starting to parse resume: {file_path}")
            
            # Read the file content
            content = self._read_file(file_path)
            print(f"File content length: {len(content) if content else 0}")
            
            if not content or not isinstance(content, str):
                raise ValueError("Invalid or empty file content")
            
            # Extract basic information
            print("Extracting name...")
            name = self._extract_name(content) or "Unknown"
            print(f"Extracted name: {name}")
            
            print("Extracting email...")
            email = self._extract_email(content) or "Not provided"
            print(f"Extracted email: {email}")
            
            print("Extracting phone...")
            phone = self._extract_phone(content) or "Not provided"
            print(f"Extracted phone: {phone}")
            
            print("Extracting skills...")
            skills = self._extract_skills(content) or []
            print(f"Extracted skills: {skills}")
            
            print("Extracting education...")
            education = self._extract_education(content) or []
            print(f"Extracted education: {education}")
            
            print("Extracting experience...")
            experience = self._extract_experience(content) or []
            print(f"Extracted experience: {experience}")
            
            print("Calculating total experience...")
            total_experience = self._calculate_total_experience(experience)
            print(f"Total experience: {total_experience}")
            
            # Validate the extracted data
            if not name and not email and not phone and not skills and not education and not experience:
                raise ValueError("Could not extract any information from the resume")
            
            result = {
                "name": name,
                "email": email,
                "phone": phone,
                "skills": skills,
                "education": education,
                "experience": experience,
                "total_experience": total_experience
            }
            print("Successfully parsed resume")
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Error parsing resume: {str(e)}\nTraceback: {traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)

    def _extract_name(self, text: str) -> str:
        """Extract name from resume text using NLP"""
        if not text:
            return "Unknown"
            
        doc = self.nlp(text)
        
        # Look for person names in the first few sentences
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        
        # Fallback: Look for capitalized words at the start of the document
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            words = line.strip().split()
            if len(words) >= 2:  # At least first and last name
                # Check if words are capitalized
                if all(word[0].isupper() for word in words[:2]):
                    return ' '.join(words[:2])
        
        return "Unknown"

    def _extract_email(self, text: str) -> str:
        """Extract email from resume text"""
        if not text:
            return "Not provided"
            
        # Enhanced email pattern to catch more variations
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Standard email
            r'\b[A-Za-z0-9._%+-]+\[at\][A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # [at] format
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email with spaces
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, text)
            if match:
                email = match.group(0)
                # Clean up the email
                email = email.replace('[at]', '@').replace(' ', '')
                return email.lower()
        
        return "Not provided"

    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume text"""
        if not text:
            return "Not provided"
            
        # Enhanced phone patterns to catch more variations
        phone_patterns = [
            r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Standard format
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Simple format
            r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',  # (XXX) XXX-XXXX format
            r'\b\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}\b'  # International format
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # Clean up the phone number
                phone = re.sub(r'[^\d+]', '', phone)  # Keep only digits and +
                return phone
        
        return "Not provided"

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        if not text:
            print("Empty text provided for skill extraction")
            return []
            
        print("Starting skill extraction...")
        # Common technical skills to look for
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "node.js", "express", "django", "flask", "spring", "aws", "azure", "gcp",
            "docker", "kubernetes", "jenkins", "git", "sql", "nosql", "mongodb",
            "postgresql", "mysql", "redis", "html", "css", "sass", "less", "bootstrap",
            "tailwind", "material-ui", "redux", "graphql", "rest", "api", "microservices",
            "ci/cd", "devops", "agile", "scrum", "jira", "confluence", "linux", "unix"
        ]
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Find skills in text
        found_skills = []
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        print(f"Found {len(found_skills)} skills: {found_skills}")
        return found_skills

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information from resume text"""
        education = []
        
        # Look for common education patterns
        education_patterns = [
            r'(?i)(bachelor|master|phd|b\.?s\.?|m\.?s\.?|b\.?e\.?|m\.?e\.?)',
            r'(?i)(university|college|institute)',
            r'(?i)(computer science|engineering|information technology|it)'
        ]
        
        # Split text into lines and look for education information
        lines = text.split('\n')
        current_edu = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains education-related information
            if any(re.search(pattern, line) for pattern in education_patterns):
                if current_edu:
                    # Only require essential fields
                    if current_edu["degree"] and current_edu["institution"]:
                        # Ensure all required fields have proper values
                        current_edu["field_of_study"] = current_edu["field_of_study"] or "Not specified"
                        current_edu["start_date"] = current_edu["start_date"] or datetime.now().strftime("%Y-%m-%d")
                        current_edu["end_date"] = current_edu["end_date"] or datetime.now().strftime("%Y-%m-%d")
                        current_edu["gpa"] = float(current_edu["gpa"]) if current_edu["gpa"] else 0.0
                        education.append(current_edu)
                
                current_edu = {
                    "degree": "",
                    "field_of_study": "Not specified",
                    "institution": "",
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d"),
                    "gpa": 0.0
                }
                
                # Extract degree
                degree_match = re.search(r'(?i)(bachelor|master|phd|b\.?s\.?|m\.?s\.?|b\.?e\.?|m\.?e\.?)', line)
                if degree_match:
                    current_edu["degree"] = degree_match.group(0)
                
                # Extract field of study
                field_match = re.search(r'(?i)(computer science|engineering|information technology|it)', line)
                if field_match:
                    current_edu["field_of_study"] = field_match.group(0)
                
                # Extract institution
                inst_match = re.search(r'(?i)(university|college|institute)', line)
                if inst_match:
                    current_edu["institution"] = line
                
                # Extract dates if present
                date_match = re.search(r'(\d{4})\s*-\s*(\d{4}|\w+)', line)
                if date_match:
                    start_year = date_match.group(1)
                    end_year = date_match.group(2)
                    
                    # Set start date
                    current_edu["start_date"] = f"{start_year}-01-01"
                    
                    # Set end date
                    if end_year.isdigit():
                        current_edu["end_date"] = f"{end_year}-12-31"
                    else:
                        current_edu["end_date"] = datetime.now().strftime("%Y-%m-%d")
                
                # Extract GPA if present
                gpa_match = re.search(r'(?i)(gpa|grade point average)[:\s]+(\d+\.?\d*)', line)
                if gpa_match:
                    try:
                        current_edu["gpa"] = float(gpa_match.group(2))
                    except ValueError:
                        current_edu["gpa"] = 0.0
        
        # Add the last education entry if exists and has essential fields
        if current_edu and current_edu["degree"] and current_edu["institution"]:
            # Ensure all required fields have proper values
            current_edu["field_of_study"] = current_edu["field_of_study"] or "Not specified"
            current_edu["start_date"] = current_edu["start_date"] or datetime.now().strftime("%Y-%m-%d")
            current_edu["end_date"] = current_edu["end_date"] or datetime.now().strftime("%Y-%m-%d")
            current_edu["gpa"] = float(current_edu["gpa"]) if current_edu["gpa"] else 0.0
            education.append(current_edu)
        
        return education

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from resume text"""
        if not text:
            print("Empty text provided for experience extraction")
            return []
            
        print("Starting experience extraction...")
        experience = []
        
        # Look for common experience patterns
        experience_patterns = [
            r'(?i)(experience|work|employment)',
            r'(?i)(years?|months?)',
            r'(?i)(developer|engineer|architect|consultant|manager)',
            r'(?i)(present|current|now)'
        ]
        
        try:
            # Split text into lines and look for experience information
            lines = text.split('\n')
            current_exp = None
            
            for line in lines:
                if not line or not isinstance(line, str):
                    continue
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line contains experience-related information
                has_experience_info = False
                for pattern in experience_patterns:
                    try:
                        if re.search(pattern, line):
                            has_experience_info = True
                            break
                    except Exception as e:
                        print(f"Error checking pattern {pattern}: {str(e)}")
                        continue
                
                if has_experience_info:
                    if current_exp:
                        # Only require essential fields
                        if current_exp["title"] and current_exp["company"]:
                            # Ensure all required fields have proper values
                            current_exp["description"] = current_exp["description"] or "No description provided"
                            current_exp["skills"] = current_exp["skills"] or []
                            current_exp["start_date"] = current_exp["start_date"] or datetime.now().strftime("%Y-%m-%d")
                            current_exp["end_date"] = current_exp["end_date"] or datetime.now().strftime("%Y-%m-%d")
                            experience.append(current_exp)
                    
                    current_exp = {
                        "title": "",
                        "company": "",
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d"),
                        "description": "No description provided",
                        "skills": []
                    }
                    
                    # Extract job title
                    try:
                        title_match = re.search(r'(?i)(developer|engineer|architect|consultant|manager)', line)
                        if title_match:
                            current_exp["title"] = title_match.group(0)
                    except Exception as e:
                        print(f"Error extracting title: {str(e)}")
                    
                    # Extract company name
                    try:
                        company_match = re.search(r'(?i)(inc\.?|ltd\.?|llc|corp\.?|company)', line)
                        if company_match:
                            current_exp["company"] = line
                    except Exception as e:
                        print(f"Error extracting company: {str(e)}")
                    
                    # Check if this is current experience
                    is_current = False
                    try:
                        is_current = bool(re.search(r'(?i)(present|current|now)', line))
                    except Exception as e:
                        print(f"Error checking current status: {str(e)}")
                    
                    # Extract dates if present and not current experience
                    if not is_current:
                        try:
                            date_match = re.search(r'(\d{4})\s*-\s*(\d{4}|\w+)', line)
                            if date_match:
                                start_year = date_match.group(1)
                                end_year = date_match.group(2)
                                
                                # Set start date
                                current_exp["start_date"] = f"{start_year}-01-01"
                                
                                # Set end date
                                if end_year.isdigit():
                                    current_exp["end_date"] = f"{end_year}-12-31"
                                else:
                                    current_exp["end_date"] = datetime.now().strftime("%Y-%m-%d")
                        except Exception as e:
                            print(f"Error extracting dates: {str(e)}")
                    else:
                        # For current experience, only set start date
                        try:
                            date_match = re.search(r'(\d{4})\s*-\s*(present|current|now)', line, re.IGNORECASE)
                            if date_match:
                                start_year = date_match.group(1)
                                current_exp["start_date"] = f"{start_year}-01-01"
                                current_exp["end_date"] = datetime.now().strftime("%Y-%m-%d")
                        except Exception as e:
                            print(f"Error extracting current experience dates: {str(e)}")
                    
                    # Extract skills mentioned in the experience
                    try:
                        skills = self._extract_skills(line)
                        if skills:
                            current_exp["skills"] = skills
                    except Exception as e:
                        print(f"Error extracting skills: {str(e)}")
            
            # Add the last experience entry if exists and has essential fields
            if current_exp and current_exp["title"] and current_exp["company"]:
                # Ensure all required fields have proper values
                current_exp["description"] = current_exp["description"] or "No description provided"
                current_exp["skills"] = current_exp["skills"] or []
                current_exp["start_date"] = current_exp["start_date"] or datetime.now().strftime("%Y-%m-%d")
                current_exp["end_date"] = current_exp["end_date"] or datetime.now().strftime("%Y-%m-%d")
                experience.append(current_exp)
            
            print(f"Found {len(experience)} experience entries")
            return experience
            
        except Exception as e:
            print(f"Error in experience extraction: {str(e)}")
            return []

    def _calculate_total_experience(self, experience: List[Dict[str, Any]]) -> float:
        """Calculate total years of experience"""
        total_years = 0.0
        
        for exp in experience:
            if exp.get("start_date") and exp.get("end_date"):
                try:
                    start = datetime.strptime(exp["start_date"], "%Y-%m-%d")
                    end = datetime.strptime(exp["end_date"], "%Y-%m-%d")
                    years = (end - start).days / 365.25
                    total_years += years
                except (ValueError, TypeError):
                    continue
        
        return round(total_years, 1) 