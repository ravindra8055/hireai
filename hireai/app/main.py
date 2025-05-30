import gradio as gr
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.parser import ResumeParser
from core.ranker import CandidateRanker
from core.search import JobSearch
from core.email import EmailGenerator
from database.supabase_client import SupabaseClient

class HireAIApp:
    def __init__(self):
        self.parser = ResumeParser()
        self.ranker = CandidateRanker()
        self.search = JobSearch()
        self.email_gen = EmailGenerator()
        self.db = SupabaseClient()

    def parse_resume(self, resume_file):
        """Parse resume and store in database"""
        if resume_file is None:
            return "Please upload a resume file"
        
        try:
            parsed_data = self.parser.parse(resume_file.name)
            self.db.store_candidate(parsed_data)
            return f"Successfully parsed resume for {parsed_data.get('name', 'Unknown')}"
        except Exception as e:
            return f"Error parsing resume: {str(e)}"

    def rank_candidates(self, job_description):
        """Rank candidates based on job description"""
        try:
            candidates = self.db.get_all_candidates()
            ranked_candidates = self.ranker.rank(candidates, job_description)
            return "\n".join([f"{c['name']}: {c['score']:.2f}" for c in ranked_candidates])
        except Exception as e:
            return f"Error ranking candidates: {str(e)}"

    def search_jobs(self, query):
        """Search jobs using natural language"""
        try:
            results = self.search.search(query)
            return "\n".join([f"{job['title']} at {job['company']}" for job in results])
        except Exception as e:
            return f"Error searching jobs: {str(e)}"

    def generate_email(self, candidate_name, job_title):
        """Generate outreach email"""
        try:
            candidate = self.db.get_candidate_by_name(candidate_name)
            email = self.email_gen.generate(candidate, job_title)
            return email
        except Exception as e:
            return f"Error generating email: {str(e)}"

    def create_ui(self):
        """Create Gradio interface"""
        with gr.Blocks(title="HireAI") as app:
            gr.Markdown("# HireAI - Intelligent Recruitment Assistant")
            
            with gr.Tab("Resume Parser"):
                resume_input = gr.File(label="Upload Resume (PDF/DOCX)")
                parse_output = gr.Textbox(label="Parsing Result")
                parse_btn = gr.Button("Parse Resume")
                parse_btn.click(self.parse_resume, resume_input, parse_output)

            with gr.Tab("Candidate Ranking"):
                job_desc = gr.Textbox(label="Job Description", lines=5)
                ranking_output = gr.Textbox(label="Ranked Candidates", lines=10)
                rank_btn = gr.Button("Rank Candidates")
                rank_btn.click(self.rank_candidates, job_desc, ranking_output)

            with gr.Tab("Job Search"):
                search_query = gr.Textbox(label="Search Query")
                search_output = gr.Textbox(label="Search Results", lines=10)
                search_btn = gr.Button("Search Jobs")
                search_btn.click(self.search_jobs, search_query, search_output)

            with gr.Tab("Email Generator"):
                candidate_name = gr.Textbox(label="Candidate Name")
                job_title = gr.Textbox(label="Job Title")
                email_output = gr.Textbox(label="Generated Email", lines=10)
                email_btn = gr.Button("Generate Email")
                email_btn.click(self.generate_email, [candidate_name, job_title], email_output)

        return app

def main():
    app = HireAIApp()
    ui = app.create_ui()
    ui.launch()

if __name__ == "__main__":
    main() 