import os
from typing import Dict, Any
from openai import AzureOpenAI
from ..config.azure_config import (
    AZURE_ENDPOINT,
    AZURE_MODEL_NAME,
    AZURE_DEPLOYMENT,
    AZURE_SUBSCRIPTION_KEY,
    AZURE_API_VERSION
)

class JobRequestParser:
    def __init__(self):
        """Initialize the job request parser with Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=AZURE_SUBSCRIPTION_KEY,
            api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT
        )
        self.deployment = AZURE_DEPLOYMENT

    def parse_job_request(self, job_request: str) -> Dict[str, Any]:
        """
        Parse a natural language job request into a structured format
        
        Args:
            job_request (str): Natural language job request
            
        Returns:
            Dict[str, Any]: Structured job information
        """
        try:
            # Create the prompt for the model
            prompt = f"""
            Parse the following job request into a structured format. Extract the following information:
            - job_title: The title of the position
            - required_skills: List of required technical skills
            - preferred_skills: List of preferred technical skills
            - experience_years: Required years of experience
            - location: Job location (if specified)
            - job_type: Type of employment (full-time, contract, etc.)
            - industry: Industry or domain (if specified)
            
            Job Request: {job_request}
            
            Return the information in a JSON format.
            """
            
            # Call Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a job request parser that extracts structured information from natural language job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Extract and parse the response
            parsed_response = response.choices[0].message.content
            
            # Convert the response to a dictionary
            import json
            job_info = json.loads(parsed_response)
            
            return job_info
            
        except Exception as e:
            raise Exception(f"Error parsing job request: {str(e)}")

    def normalize_job_info(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the job information to ensure consistent format
        
        Args:
            job_info (Dict[str, Any]): Raw job information
            
        Returns:
            Dict[str, Any]: Normalized job information
        """
        normalized = {
            'job_title': job_info.get('job_title', '').lower(),
            'required_skills': [skill.lower() for skill in job_info.get('required_skills', [])],
            'preferred_skills': [skill.lower() for skill in job_info.get('preferred_skills', [])],
            'experience_years': job_info.get('experience_years', 0),
            'location': job_info.get('location', '').lower(),
            'job_type': job_info.get('job_type', '').lower(),
            'industry': job_info.get('industry', '').lower()
        }
        
        return normalized 