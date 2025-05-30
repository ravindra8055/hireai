import os
from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from .models import Candidate, Job
from datetime import datetime
import json
from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing Supabase credentials. Please check your supabase_config.py file.")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self._create_candidates_table()

    def _create_candidates_table(self):
        """Create candidates table if it doesn't exist"""
        try:
            # Check if table exists by trying to select from it
            self.client.table('candidates').select('id').limit(1).execute()
        except Exception:
            # Table doesn't exist, create it
            self.client.table('candidates').insert({
                'name': 'test',
                'email': 'test@example.com',
                'phone': '1234567890',
                'skills': [],
                'education': [],
                'experience': [],
                'years_of_experience': 0  # Changed from total_experience to years_of_experience
            }).execute()
            
            # Delete the test record
            self.client.table('candidates').delete().eq('email', 'test@example.com').execute()

    def insert_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Insert a new candidate into the database"""
        try:
            # Prepare the data for insertion
            data = {
                'name': candidate_data.get('name', ''),
                'email': candidate_data.get('email', ''),
                'phone': candidate_data.get('phone', ''),
                'skills': candidate_data.get('skills', []),
                'education': candidate_data.get('education', []),
                'experience': candidate_data.get('experience', []),
                'years_of_experience': candidate_data.get('total_experience', 0)  # Map total_experience to years_of_experience
            }
            
            # Insert the candidate
            response = self.client.table('candidates').insert(data).execute()
            
            if response.data:
                return response.data[0]['id']
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            raise Exception(f"Error inserting candidate: {str(e)}")

    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Get a candidate by ID"""
        try:
            response = self.client.table('candidates').select('*').eq('id', candidate_id).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            raise Exception(f"Error getting candidate: {str(e)}")

    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates"""
        try:
            response = self.client.table('candidates').select('*').execute()
            return response.data
        except Exception as e:
            raise Exception(f"Error getting candidates: {str(e)}")

    def search_candidates(self, skills: List[str] = None, location: str = None, min_experience: int = None) -> List[Dict[str, Any]]:
        """Search for candidates matching criteria"""
        try:
            query = self.client.table('candidates').select('*')
            
            if skills:
                # Search for candidates with any of the required skills
                for skill in skills:
                    query = query.contains('skills', [skill])
            
            if location:
                # Search for candidates in the specified location
                query = query.ilike('location', f'%{location}%')
            
            if min_experience is not None:
                # Search for candidates with minimum years of experience
                query = query.gte('years_of_experience', min_experience)
            
            response = query.execute()
            return response.data
        except Exception as e:
            raise Exception(f"Error searching candidates: {str(e)}")

    def update_candidate(self, candidate_id: str, candidate_data: Dict[str, Any]) -> bool:
        """Update a candidate's information"""
        try:
            # Prepare the data for update
            data = {
                'name': candidate_data.get('name', ''),
                'email': candidate_data.get('email', ''),
                'phone': candidate_data.get('phone', ''),
                'skills': candidate_data.get('skills', []),
                'education': candidate_data.get('education', []),
                'experience': candidate_data.get('experience', []),
                'years_of_experience': candidate_data.get('total_experience', 0)  # Map total_experience to years_of_experience
            }
            
            response = self.client.table('candidates').update(data).eq('id', candidate_id).execute()
            return bool(response.data)
        except Exception as e:
            raise Exception(f"Error updating candidate: {str(e)}")

    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete a candidate"""
        try:
            response = self.client.table('candidates').delete().eq('id', candidate_id).execute()
            return bool(response.data)
        except Exception as e:
            raise Exception(f"Error deleting candidate: {str(e)}")

    def store_candidate(self, candidate_data: dict) -> str:
        """Store candidate data in Supabase"""
        response = self.client.table("candidates").insert(candidate_data).execute()
        return response.data[0]["id"]

    def get_candidate_by_name(self, name: str) -> Optional[Candidate]:
        """Retrieve candidate by name"""
        response = self.client.table("candidates").select("*").eq("name", name).execute()
        if response.data:
            return Candidate(**response.data[0])
        return None

    def get_all_candidates(self) -> List[Candidate]:
        """Retrieve all candidates"""
        response = self.client.table("candidates").select("*").execute()
        return [Candidate(**data) for data in response.data]

    def store_job(self, job_data: dict) -> str:
        """Store job data in Supabase"""
        response = self.client.table("jobs").insert(job_data).execute()
        return response.data[0]["id"]

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID"""
        response = self.client.table("jobs").select("*").eq("id", job_id).execute()
        if response.data:
            return Job(**response.data[0])
        return None

    def search_jobs(self, query: str) -> List[Job]:
        """Search jobs using full-text search"""
        response = self.client.table("jobs").select("*").textSearch("description", query).execute()
        return [Job(**data) for data in response.data] 