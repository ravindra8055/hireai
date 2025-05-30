import os
import sys
import gradio as gr
from typing import List, Dict, Any
import json
from datetime import datetime
from openai import AzureOpenAI
import re

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Azure OpenAI Configuration
AZURE_ENDPOINT = "https://openai-hackathonpoc-dev.openai.azure.com/"
AZURE_MODEL_NAME = "gpt-35-turbo"
AZURE_DEPLOYMENT = "hackathon-poc-turbo35"
AZURE_API_KEY = "d82d792194e949fe896c65340705abfe"
AZURE_API_VERSION = "2024-12-01-preview"

try:
    from hireai.core.resume_parser import ResumeParser
    from hireai.core.job_parser import JobRequestParser
    from hireai.core.similarity import SimilarityCalculator
    from hireai.database.supabase_client import SupabaseClient
    from hireai.visualization.skill_charts import SkillVisualizer
except ImportError as e:
    print(f"Error importing HireAI modules: {str(e)}")
    print("\nPlease ensure:")
    print("1. The package is installed in development mode: pip install -e .")
    print("2. All __init__.py files are created in the package directories")
    print("3. All required dependencies are installed")
    sys.exit(1)

class HireAIDemo:
    def __init__(self):
        """Initialize the HireAI demo with all components"""
        self.resume_parser = ResumeParser()
        self.job_parser = JobRequestParser()
        self.similarity_calculator = SimilarityCalculator()
        self.supabase_client = SupabaseClient()
        self.skill_visualizer = SkillVisualizer()
        self.match_threshold = 0.5  # 50% match threshold
        
        # Initialize Azure OpenAI client
        self.azure_client = AzureOpenAI(
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT
        )
        
        # Load sample resumes
        self.sample_resumes = self._load_sample_resumes()
        
    def _load_sample_resumes(self) -> List[Dict[str, Any]]:
        """Load sample resumes from the data directory"""
        sample_dir = os.path.join(project_root, "data", "sample_resumes")
        resumes = []
        
        if os.path.exists(sample_dir):
            for filename in os.listdir(sample_dir):
                if filename.endswith(('.pdf', '.docx')):
                    file_path = os.path.join(sample_dir, filename)
                    try:
                        resume_data = self.resume_parser.parse_resume(file_path)
                        resumes.append(resume_data)
                    except Exception as e:
                        print(f"Error parsing {filename}: {str(e)}")
        
        return resumes

    def process_resume(self, resume_file, name, email, phone) -> Dict[str, Any]:
        """Process a resume file and store in database"""
        try:
            # Parse resume
            resume_data = self.resume_parser.parse_resume(resume_file.name)
            
            # Use extracted information if not provided
            if not name:
                name = resume_data.get('name', '')
            if not email:
                email = resume_data.get('email', '')
            if not phone:
                phone = resume_data.get('phone', '')
            
            # Add user-provided information
            resume_data['name'] = name
            resume_data['email'] = email
            resume_data['phone'] = phone
            
            # Store in database
            candidate_id = self.supabase_client.insert_candidate(resume_data)
            resume_data['id'] = candidate_id
            
            return {
                "status": "success",
                "message": "Resume processed successfully!",
                "data": resume_data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def analyze_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Analyze job requirements using Azure OpenAI"""
        try:
            print("\n=== Starting Job Requirements Analysis ===")
            if not job_description or not isinstance(job_description, str):
                print("Invalid job description provided")
                raise ValueError("Job description must be a non-empty string")
            
            print(f"Job Description: {job_description[:200]}...")  # Print first 200 chars
            
            # Create a prompt for OpenAI
            prompt = f"""
            Analyze the following job description and extract key requirements.
            You must return a valid JSON object with the following structure:
            {{
                "required_skills": [<list of required technical skills>],
                "required_experience": {{
                    "years": <number of years>,
                    "level": <"Entry", "Mid", or "Senior">,
                    "description": <detailed experience requirements>
                }},
                "required_education": {{
                    "degree": <required degree>,
                    "field": <required field of study>,
                    "description": <detailed education requirements>
                }},
                "responsibilities": [<list of key responsibilities>],
                "preferred_qualifications": [<list of preferred qualifications>]
            }}

            Job Description:
            {job_description}

            Remember to return ONLY the JSON object, no additional text or explanation.
            """
            
            print("Sending request to Azure OpenAI...")
            # Call Azure OpenAI API
            response = self.azure_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a job analysis expert. Extract and structure job requirements from descriptions. You must return a valid JSON object with the exact structure specified. Do not include any additional text or explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            print("Received response from Azure OpenAI")
            response_content = response.choices[0].message.content.strip()
            print(f"Raw Response: {response_content}")
            
            if not response_content:
                print("Empty response received from Azure OpenAI")
                raise ValueError("Empty response from Azure OpenAI")
            
            # Try to parse the response
            try:
                # First try direct JSON parsing
                analysis = json.loads(response_content)
                print("Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print("Attempting to clean and parse response...")
                
                # Try to extract JSON from the response if it's wrapped in markdown or other text
                # Look for JSON object in the response
                json_match = re.search(r'\{[\s\S]*\}', response_content)
                if json_match:
                    try:
                        json_str = json_match.group()
                        # Clean up any potential markdown formatting
                        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
                        analysis = json.loads(json_str)
                        print("Successfully extracted and parsed JSON from response")
                    except json.JSONDecodeError as e2:
                        print(f"Failed to parse extracted JSON: {str(e2)}")
                        raise
                else:
                    print("No JSON object found in response")
                    raise
            
            # Validate the required structure
            required_keys = ["required_skills", "required_experience", "required_education", 
                           "responsibilities", "preferred_qualifications"]
            missing_keys = [key for key in required_keys if key not in analysis]
            
            if missing_keys:
                print(f"Missing required keys in response: {missing_keys}")
                # Add missing keys with default values
                for key in missing_keys:
                    if key == "required_skills":
                        analysis[key] = []
                    elif key in ["required_experience", "required_education"]:
                        analysis[key] = {
                            "years": 0,
                            "level": "Not specified",
                            "description": "Not specified"
                        }
                    else:
                        analysis[key] = []
            
            print("=== Completed Job Requirements Analysis ===\n")
            return analysis
            
        except Exception as e:
            print(f"\nError analyzing job requirements: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Return a default structure
            return {
                "required_skills": [],
                "required_experience": {
                    "years": 0,
                    "level": "Not specified",
                    "description": "Not specified"
                },
                "required_education": {
                    "degree": "Not specified",
                    "field": "Not specified",
                    "description": "Not specified"
                },
                "responsibilities": [],
                "preferred_qualifications": []
            }

    def analyze_candidate_match(self, job_requirements: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well a candidate matches the job requirements using Azure OpenAI"""
        try:
            print("\n=== Starting Candidate Analysis ===")
            print(f"Candidate type: {type(candidate)}")
            print(f"Candidate attributes: {dir(candidate)}")
            print(f"Candidate dict: {candidate.__dict__ if hasattr(candidate, '__dict__') else 'No __dict__'}")
            
            # Convert candidate object to dictionary if it's not already
            if hasattr(candidate, 'dict'):
                print("Converting Pydantic model to dictionary")
                candidate_dict = candidate.dict()
            elif hasattr(candidate, '__dict__'):
                print("Converting object to dictionary using __dict__")
                candidate_dict = candidate.__dict__
            else:
                print("Using candidate as is")
                candidate_dict = candidate
                
            print(f"Converted candidate type: {type(candidate_dict)}")
            print(f"Converted candidate content: {candidate_dict}")
            
            # Create a prompt for OpenAI
            prompt = f"""
            Compare the following candidate profile with job requirements:
            Give more score if 30 to 50 % of skills matches
            
            Candidate Profile:
            - Name: {candidate_dict.get('name', 'N/A')}
            - Skills: {', '.join(candidate_dict.get('skills', []))}
            - Education: {json.dumps(candidate_dict.get('education', []))}
            
            Job Requirements:
            {json.dumps(job_requirements, indent=2)}
            
            Please analyze and provide a JSON response with the following structure:
            {{
                "overall_score": <number between 0 and 100>,
                "skill_matches": {{
                    "matched_skills": [<list of matched skills>],
                    "unmatched_skills": [<list of unmatched skills>]
                }},
                "education_match": {{
                    "candidate_education": <candidate's education>,
                    "required_education": <required education>,
                    "match": <"High", "Medium", or "Low">
                }},
                "missing_requirements": [<list of missing requirements>]
            }}
            
            Note: Ignore experience requirements in the matching process. Focus on skills and education matches.
            """
            
            print("\nSending request to Azure OpenAI...")
            # Call Azure OpenAI API
            response = self.azure_client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a recruitment expert. Analyze candidate-job matches and provide detailed scoring. Always return a JSON object with the exact structure specified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            print("Received response from Azure OpenAI")
            print(f"Raw Response: {response.choices[0].message.content}")
            
            # Parse the response
            match_analysis = json.loads(response.choices[0].message.content)
            
            # Convert overall_score to a float between 0 and 1
            if isinstance(match_analysis.get('overall_score'), int):
                match_analysis['overall_score'] = match_analysis['overall_score'] / 100.0
            
            print("Successfully parsed response")
            print("=== Completed Candidate Analysis ===\n")
            
            return match_analysis
            
        except Exception as e:
            print(f"\nError analyzing candidate match: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "overall_score": 0.0,
                "skill_matches": {
                    "matched_skills": [],
                    "unmatched_skills": []
                },
                "education_match": {
                    "candidate_education": "N/A",
                    "required_education": "N/A",
                    "match": "Low"
                },
                "missing_requirements": []
            }

    def search_candidates(self, job_description: str) -> Dict[str, Any]:
        """Search for candidates matching the job description using AI"""
        try:
            print("\n=== Starting Candidate Search ===")
            print("Starting candidate search...")
            
            # Get all candidates from the database
            candidates = self.supabase_client.get_all_candidates()
            if not candidates:
                print("No candidates found in database")
                return {
                    "status": "error",
                    "message": "No candidates found in the database"
                }
            
            print(f"Found {len(candidates)} candidates in database")
            print(f"First candidate type: {type(candidates[0])}")
            print(f"First candidate content: {candidates[0]}")
            
            # Analyze job requirements using Azure OpenAI
            job_analysis = self.analyze_job_requirements(job_description)
            if not job_analysis:
                print("Failed to analyze job requirements")
                return {
                    "status": "error",
                    "message": "Failed to analyze job requirements"
                }
            
            print("Analyzing candidates...")
            matching_candidates = []
            
            # Analyze each candidate against job requirements
            for i, candidate in enumerate(candidates):
                print(f"\nProcessing candidate {i+1}/{len(candidates)}")
                match_score = self.analyze_candidate_match(job_analysis, candidate)
                if match_score["overall_score"] >= 0.5:  # 50% match threshold
                    matching_candidates.append({
                        "candidate": candidate,
                        "match_analysis": match_score
                    })
            
            # Sort candidates by match score
            matching_candidates.sort(key=lambda x: x["match_analysis"]["overall_score"], reverse=True)
            
            print(f"\nFound {len(matching_candidates)} matching candidates")
            print("=== Completed Candidate Search ===\n")
            
            return {
                "status": "success",
                "job_requirements": job_analysis,
                "matching_candidates": matching_candidates,
                "total_candidates": len(candidates),
                "matching_count": len(matching_candidates)
            }
            
        except Exception as e:
            print(f"\nError in candidate search: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error searching candidates: {str(e)}"
            }

    def generate_skills_chart(self) -> str:
        """Generate a chart of most common skills"""
        try:
            candidates = self.supabase_client.get_all_candidates()
            all_skills = []
            for candidate in candidates:
                all_skills.extend(candidate.get('skills', []))
            
            chart_path = self.skill_visualizer.plot_skill_frequency(all_skills)
            return chart_path
        except Exception as e:
            return f"Error generating chart: {str(e)}"

def create_demo_interface():
    """Create the Gradio interface for the demo"""
    demo = HireAIDemo()
    
    with gr.Blocks(title="HireAI - Smart Recruitment Platform", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # HireAI - Smart Recruitment Platform
        Welcome to HireAI, your intelligent recruitment assistant. We help connect talented candidates with the right opportunities.
        """)
        
        with gr.Tabs() as tabs:
            with gr.Tab("Home"):
                gr.Markdown("""
                ## About HireAI
                
                HireAI is an intelligent recruitment platform that uses AI to:
                - Parse and analyze resumes automatically
                - Match candidates with job requirements
                - Identify the best candidates for your positions
                - Streamline the recruitment process
                
                ### How it works
                1. **For Candidates**: Upload your resume and let our AI analyze your skills and experience
                2. **For HR**: Post job requirements and find the best matching candidates
                
                Get started by selecting the appropriate tab above!
                """)
            
            with gr.Tab("For Candidates"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Upload Your Resume")
                        resume_input = gr.File(
                            label="Upload Resume (PDF or DOCX)",
                            file_types=[".pdf", ".docx"]
                        )
                        
                        with gr.Group():
                            gr.Markdown("### Personal Information")
                            gr.Markdown("The following information will be automatically extracted from your resume. Please verify and update if needed.")
                            name_input = gr.Textbox(
                                label="Full Name",
                                placeholder="Your name will be extracted from the resume"
                            )
                            email_input = gr.Textbox(
                                label="Email",
                                placeholder="Your email will be extracted from the resume"
                            )
                            phone_input = gr.Textbox(
                                label="Phone",
                                placeholder="Your phone number will be extracted from the resume"
                            )
                        
                        upload_btn = gr.Button("Upload Resume", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("### Resume Analysis")
                        resume_output = gr.JSON(label="Analysis Results")
                
                def extract_info(resume_file):
                    if resume_file is None:
                        return "", "", ""
                    try:
                        resume_data = demo.resume_parser.parse_resume(resume_file.name)
                        return (
                            resume_data.get('name', ''),
                            resume_data.get('email', ''),
                            resume_data.get('phone', '')
                        )
                    except Exception as e:
                        return "", "", ""
                
                resume_input.change(
                    extract_info,
                    inputs=[resume_input],
                    outputs=[name_input, email_input, phone_input]
                )
                
                upload_btn.click(
                    demo.process_resume,
                    inputs=[resume_input, name_input, email_input, phone_input],
                    outputs=[resume_output]
                )
            
            with gr.Tab("For HR"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Search for Candidates")
                        job_description = gr.Textbox(
                            label="Job Description",
                            placeholder="""Enter detailed job description. Example:
Looking for a Senior Python Developer with 5+ years of experience in web development.
Must have strong skills in Python, Django, and PostgreSQL.
Location: New York, NY
Company: TechCorp Inc.

The ideal candidate should have experience with:
- RESTful APIs
- Microservices architecture
- AWS cloud services
- CI/CD pipelines""",
                            lines=10
                        )
                        search_btn = gr.Button("Search Candidates", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("### Search Results")
                        with gr.Tabs():
                            with gr.Tab("Grid View"):
                                candidates_grid = gr.Dataframe(
                                    headers=["Name", "Email", "Skills", "Experience"],
                                    datatype=["str", "str", "str", "str"],
                                    col_count=(4, "fixed")
                                )
                            with gr.Tab("Detailed View"):
                                search_output = gr.JSON(label="Matching Candidates")
                
                def format_candidate_grid(search_results):
                    print("\n=== Starting Grid Formatting ===")
                    print(f"Search results status: {search_results.get('status')}")
                    
                    if search_results["status"] != "success":
                        print("Search results status is not success")
                        return [], search_results
                    
                    print(f"Number of matching candidates: {len(search_results.get('matching_candidates', []))}")
                    grid_data = []
                    
                    for idx, match in enumerate(search_results["matching_candidates"]):
                        print(f"\nProcessing candidate {idx + 1}")
                        candidate = match["candidate"]
                        analysis = match["match_analysis"]
                        
                        print(f"Raw candidate type: {type(candidate)}")
                        print(f"Raw candidate data: {candidate}")
                        
                        # Convert candidate to dict if it's a string or Pydantic model
                        if isinstance(candidate, str):
                            # Try to extract data from Pydantic model string representation
                            try:
                                # Extract name
                                name_match = re.search(r"name='([^']*)'", candidate)
                                name = name_match.group(1) if name_match else "N/A"
                                
                                # Extract email
                                email_match = re.search(r"email='([^']*)'", candidate)
                                email = email_match.group(1) if email_match else "N/A"
                                
                                # Extract skills
                                skills_match = re.search(r"skills=\[(.*?)\]", candidate)
                                skills = []
                                if skills_match:
                                    skills_str = skills_match.group(1)
                                    skills = [s.strip("' ") for s in skills_str.split(',') if s.strip()]
                                
                                # Extract experience
                                exp_match = re.search(r"experience=\[(.*?)\]", candidate)
                                experience = "No experience listed"
                                if exp_match:
                                    exp_str = exp_match.group(1)
                                    title_match = re.search(r"title='([^']*)'", exp_str)
                                    company_match = re.search(r"company='([^']*)'", exp_str)
                                    if title_match and company_match:
                                        experience = f"{title_match.group(1)} at {company_match.group(1)}"
                                
                                # Create a dictionary with the extracted data
                                candidate = {
                                    "name": name,
                                    "email": email,
                                    "skills": skills,
                                    "experience": [{"title": title_match.group(1) if title_match else "N/A",
                                                  "company": company_match.group(1) if company_match else "N/A"}]
                                }
                                print("Successfully extracted data from string representation")
                            except Exception as e:
                                print(f"Warning: Could not parse candidate string: {str(e)}")
                                continue
                        elif hasattr(candidate, 'dict'):
                            candidate = candidate.dict()
                            print("Converted Pydantic model to dictionary")
                        elif hasattr(candidate, '__dict__'):
                            candidate = candidate.__dict__
                            print("Converted object to dictionary using __dict__")
                        
                        print(f"Processed candidate type: {type(candidate)}")
                        print(f"Processed candidate data: {candidate}")
                        
                        # Format skills for display
                        skills = []
                        if isinstance(candidate.get("skills"), list):
                            skills = candidate["skills"][:5]
                            print(f"Found skills list: {skills}")
                        elif isinstance(candidate.get("skills"), str):
                            skills = candidate["skills"].split(",")[:5]
                            print(f"Found skills string, split into: {skills}")
                        
                        skills_display = ", ".join(skills)
                        if len(skills) > 5:
                            skills_display += "..."
                        
                        # Format experience
                        experience = "No experience listed"
                        if candidate.get("experience"):
                            if isinstance(candidate["experience"], list) and len(candidate["experience"]) > 0:
                                exp = candidate["experience"][0]
                                if isinstance(exp, dict):
                                    experience = f"{exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}"
                                elif hasattr(exp, 'dict'):
                                    exp_dict = exp.dict()
                                    experience = f"{exp_dict.get('title', 'N/A')} at {exp_dict.get('company', 'N/A')}"
                        
                        # Get name and email
                        name = candidate.get("name", "N/A")
                        email = candidate.get("email", "N/A")
                        
                        print(f"Formatted row: [{name}, {email}, {skills_display}, {experience}]")
                        grid_data.append([
                            name,
                            email,
                            skills_display,
                            experience
                        ])
                    
                    print(f"\nFinal grid data length: {len(grid_data)}")
                    print("=== Completed Grid Formatting ===\n")
                    return grid_data, search_results
                
                search_btn.click(
                    demo.search_candidates,
                    inputs=[job_description],
                    outputs=[search_output]
                ).then(
                    format_candidate_grid,
                    inputs=[search_output],
                    outputs=[candidates_grid, search_output]
                )
    
    return interface

if __name__ == "__main__":
    interface = create_demo_interface()
    interface.launch(share=True) 