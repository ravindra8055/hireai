import spacy
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CandidateRanker:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def rank(self, candidates: List[Dict[str, Any]], job_description: str) -> List[Dict[str, Any]]:
        """Rank candidates based on job description"""
        # Prepare candidate texts
        candidate_texts = []
        for candidate in candidates:
            text = self._prepare_candidate_text(candidate)
            candidate_texts.append(text)

        # Add job description to the corpus
        all_texts = candidate_texts + [job_description]

        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Calculate similarity scores
        job_vector = tfidf_matrix[-1]
        candidate_vectors = tfidf_matrix[:-1]
        similarity_scores = cosine_similarity(candidate_vectors, job_vector).flatten()

        # Add scores to candidates
        ranked_candidates = []
        for candidate, score in zip(candidates, similarity_scores):
            candidate_copy = candidate.copy()
            candidate_copy['score'] = float(score)
            ranked_candidates.append(candidate_copy)

        # Sort by score in descending order
        ranked_candidates.sort(key=lambda x: x['score'], reverse=True)

        return ranked_candidates

    def _prepare_candidate_text(self, candidate: Dict[str, Any]) -> str:
        """Prepare candidate text for comparison"""
        text_parts = []

        # Add skills
        if 'skills' in candidate:
            text_parts.extend(candidate['skills'])

        # Add education
        if 'education' in candidate:
            for edu in candidate['education']:
                if isinstance(edu, dict):
                    text_parts.extend([
                        edu.get('institution', ''),
                        edu.get('degree', ''),
                        edu.get('field_of_study', '')
                    ])

        # Add experience
        if 'experience' in candidate:
            for exp in candidate['experience']:
                if isinstance(exp, dict):
                    text_parts.extend([
                        exp.get('company', ''),
                        exp.get('title', ''),
                        exp.get('description', '')
                    ])
                    if 'skills' in exp:
                        text_parts.extend(exp['skills'])

        # Join all parts and clean
        text = ' '.join(text_parts)
        doc = self.nlp(text)
        
        # Remove stop words and lemmatize
        cleaned_text = ' '.join([token.lemma_ for token in doc if not token.is_stop])
        
        return cleaned_text 