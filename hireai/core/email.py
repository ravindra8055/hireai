from typing import Dict, Any
import openai
import os

class EmailGenerator:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("Missing OpenAI API key")

    def generate(self, candidate: Dict[str, Any], job_title: str) -> str:
        """Generate personalized outreach email"""
        # Prepare prompt for OpenAI
        prompt = self._create_prompt(candidate, job_title)
        
        try:
            # Generate email using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional recruiter writing a personalized outreach email."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating email: {str(e)}"

    def _create_prompt(self, candidate: Dict[str, Any], job_title: str) -> str:
        """Create prompt for email generation"""
        # Extract relevant information from candidate
        name = candidate.get('name', '')
        skills = ', '.join(candidate.get('skills', []))
        
        # Get most recent experience
        experience = candidate.get('experience', [])
        recent_exp = experience[0] if experience else {}
        company = recent_exp.get('company', '')
        position = recent_exp.get('title', '')
        
        # Create prompt
        prompt = f"""
        Write a personalized outreach email to {name} for a {job_title} position.
        
        Candidate Information:
        - Name: {name}
        - Key Skills: {skills}
        - Current/Most Recent Position: {position} at {company}
        
        The email should:
        1. Be personalized and engaging
        2. Mention their relevant experience and skills
        3. Explain why they would be a good fit for the role
        4. Include a clear call to action
        5. Be professional but conversational
        6. Be concise (2-3 paragraphs)
        
        Format the email with proper greeting and signature.
        """
        
        return prompt 