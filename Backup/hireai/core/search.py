import spacy
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class JobSearch:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def search(self, query: str, jobs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search jobs using natural language query"""
        if not jobs:
            # In a real application, you would fetch jobs from the database
            jobs = self._get_sample_jobs()

        # Prepare job texts
        job_texts = [self._prepare_job_text(job) for job in jobs]

        # Add query to the corpus
        all_texts = job_texts + [query]

        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Calculate similarity scores
        query_vector = tfidf_matrix[-1]
        job_vectors = tfidf_matrix[:-1]
        similarity_scores = cosine_similarity(job_vectors, query_vector).flatten()

        # Add scores to jobs
        scored_jobs = []
        for job, score in zip(jobs, similarity_scores):
            job_copy = job.copy()
            job_copy['score'] = float(score)
            scored_jobs.append(job_copy)

        # Sort by score in descending order
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)

        return scored_jobs

    def _prepare_job_text(self, job: Dict[str, Any]) -> str:
        """Prepare job text for comparison"""
        text_parts = []

        # Add job details
        text_parts.extend([
            job.get('title', ''),
            job.get('company', ''),
            job.get('description', '')
        ])

        # Add requirements
        if 'requirements' in job:
            text_parts.extend(job['requirements'])

        # Join all parts and clean
        text = ' '.join(text_parts)
        doc = self.nlp(text)
        
        # Remove stop words and lemmatize
        cleaned_text = ' '.join([token.lemma_ for token in doc if not token.is_stop])
        
        return cleaned_text

    def _get_sample_jobs(self) -> List[Dict[str, Any]]:
        """Return sample jobs for testing"""
        return [
            {
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "description": "We are looking for a Senior Python Developer to join our team...",
                "requirements": [
                    "5+ years of Python experience",
                    "Experience with Django or Flask",
                    "Strong knowledge of SQL",
                    "Experience with AWS"
                ]
            },
            {
                "title": "Machine Learning Engineer",
                "company": "AI Solutions",
                "location": "New York, NY",
                "description": "Join our AI team to build cutting-edge machine learning solutions...",
                "requirements": [
                    "MS or PhD in Computer Science or related field",
                    "Experience with PyTorch or TensorFlow",
                    "Strong background in machine learning",
                    "Experience with NLP"
                ]
            }
        ] 