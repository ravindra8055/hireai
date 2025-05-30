import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Union
import openai
from sentence_transformers import SentenceTransformer
import os
from openai import AzureOpenAI
from ..config.azure_config import (
    AZURE_ENDPOINT,
    AZURE_MODEL_NAME,
    AZURE_DEPLOYMENT,
    AZURE_SUBSCRIPTION_KEY,
    AZURE_API_VERSION
)

class SimilarityCalculator:
    def __init__(self, method: str = "tfidf"):
        """
        Initialize the similarity calculator
        
        Args:
            method (str): Method to use for similarity calculation ("tfidf" or "embeddings")
        """
        self.method = method
        
        if method == "tfidf":
            self.vectorizer = TfidfVectorizer()
        elif method == "embeddings":
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=AZURE_SUBSCRIPTION_KEY,
                api_version=AZURE_API_VERSION,
                azure_endpoint=AZURE_ENDPOINT
            )
            self.deployment = AZURE_DEPLOYMENT
        else:
            raise ValueError("Invalid method. Use 'tfidf' or 'embeddings'")

    def calculate_similarity(self, job_query: str, candidate_skills: List[str]) -> float:
        """
        Calculate similarity between job query and candidate skills
        
        Args:
            job_query (str): Job query text
            candidate_skills (List[str]): List of candidate skills
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if self.method == "tfidf":
            return self._calculate_tfidf_similarity(job_query, candidate_skills)
        else:
            return self._calculate_embedding_similarity(job_query, candidate_skills)

    def _calculate_tfidf_similarity(self, job_query: str, candidate_skills: List[str]) -> float:
        """Calculate similarity using TF-IDF"""
        # Combine candidate skills into a single string
        candidate_text = " ".join(candidate_skills)
        
        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform([job_query, candidate_text])
        
        # Calculate cosine similarity
        similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
        
        return float(similarity)

    def _calculate_embedding_similarity(self, job_query: str, candidate_skills: List[str]) -> float:
        """Calculate similarity using Azure OpenAI embeddings"""
        try:
            # Get embeddings for job query
            query_embedding = self._get_embedding(job_query)
            
            # Get embeddings for candidate skills
            candidate_text = " ".join(candidate_skills)
            candidate_embedding = self._get_embedding(candidate_text)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, candidate_embedding)
            
            return float(similarity)
            
        except Exception as e:
            raise Exception(f"Error calculating embedding similarity: {str(e)}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Azure OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Error getting embedding: {str(e)}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate dot product
        dot_product = np.dot(vec1, vec2)
        
        # Calculate magnitudes
        magnitude1 = np.sqrt(np.sum(vec1 ** 2))
        magnitude2 = np.sqrt(np.sum(vec2 ** 2))
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        return float(similarity)

    def calculate_similarity(self, 
                           job_info: Dict[str, Any], 
                           candidate: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate similarity between job requirements and candidate profile
        
        Args:
            job_info (Dict[str, Any]): Structured job information
            candidate (Dict[str, Any]): Candidate profile
            
        Returns:
            Tuple[float, Dict[str, float]]: Overall similarity score and detailed scores
        """
        if self.method == "tfidf":
            return self._calculate_tfidf_similarity(job_info, candidate)
        else:
            return self._calculate_embedding_similarity(job_info, candidate)

    def _calculate_tfidf_similarity(self, 
                                  job_info: Dict[str, Any], 
                                  candidate: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate similarity using TF-IDF"""
        # Prepare text for vectorization
        job_text = self._prepare_text_for_tfidf(job_info)
        candidate_text = self._prepare_text_for_tfidf(candidate)
        
        # Create TF-IDF vectors
        try:
            tfidf_matrix = self.vectorizer.fit_transform([job_text, candidate_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            # Handle case where vocabulary is empty
            similarity = 0.0
        
        # Calculate detailed scores
        detailed_scores = {
            'skills': self._calculate_skills_similarity(job_info.get('skills', []), 
                                                      candidate.get('skills', [])),
            'location': self._calculate_location_similarity(job_info.get('location', ''), 
                                                         candidate.get('location', '')),
            'experience': self._calculate_experience_similarity(job_info.get('experience_level', ''), 
                                                             candidate.get('experience_level', ''))
        }
        
        # Calculate weighted average
        weights = {'skills': 0.6, 'location': 0.2, 'experience': 0.2}
        weighted_score = sum(score * weights[category] 
                           for category, score in detailed_scores.items())
        
        return weighted_score, detailed_scores

    def _calculate_embedding_similarity(self, 
                                      job_info: Dict[str, Any], 
                                      candidate: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Calculate similarity using sentence embeddings"""
        # Prepare text for embedding
        job_text = self._prepare_text_for_embedding(job_info)
        candidate_text = self._prepare_text_for_embedding(candidate)
        
        # Get embeddings
        job_embedding = self.model.encode(job_text)
        candidate_embedding = self.model.encode(candidate_text)
        
        # Calculate cosine similarity
        similarity = cosine_similarity([job_embedding], [candidate_embedding])[0][0]
        
        # Calculate detailed scores using embeddings
        detailed_scores = {
            'skills': self._calculate_skills_embedding_similarity(
                job_info.get('skills', []), 
                candidate.get('skills', [])
            ),
            'location': self._calculate_location_embedding_similarity(
                job_info.get('location', ''), 
                candidate.get('location', '')
            ),
            'experience': self._calculate_experience_embedding_similarity(
                job_info.get('experience_level', ''), 
                candidate.get('experience_level', '')
            )
        }
        
        # Calculate weighted average
        weights = {'skills': 0.6, 'location': 0.2, 'experience': 0.2}
        weighted_score = sum(score * weights[category] 
                           for category, score in detailed_scores.items())
        
        return weighted_score, detailed_scores

    def _prepare_text_for_tfidf(self, data: Dict[str, Any]) -> str:
        """Prepare text for TF-IDF vectorization"""
        text_parts = []
        
        if 'skills' in data:
            text_parts.extend(data['skills'])
        
        if 'location' in data:
            text_parts.append(data['location'])
            
        if 'experience_level' in data:
            text_parts.append(data['experience_level'])
            
        return ' '.join(text_parts)

    def _prepare_text_for_embedding(self, data: Dict[str, Any]) -> str:
        """Prepare text for sentence embedding"""
        text_parts = []
        
        if 'skills' in data:
            text_parts.append(f"Skills: {', '.join(data['skills'])}")
        
        if 'location' in data:
            text_parts.append(f"Location: {data['location']}")
            
        if 'experience_level' in data:
            text_parts.append(f"Experience Level: {data['experience_level']}")
            
        return ' '.join(text_parts)

    def _calculate_skills_similarity(self, 
                                   job_skills: List[str], 
                                   candidate_skills: List[str]) -> float:
        """Calculate similarity between job and candidate skills using TF-IDF"""
        if not job_skills or not candidate_skills:
            return 0.0
            
        job_skills_text = ' '.join(job_skills)
        candidate_skills_text = ' '.join(candidate_skills)
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform([job_skills_text, candidate_skills_text])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            return 0.0

    def _calculate_location_similarity(self, 
                                     job_location: str, 
                                     candidate_location: str) -> float:
        """Calculate similarity between job and candidate locations"""
        if not job_location or not candidate_location:
            return 0.0
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform([job_location, candidate_location])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            return 0.0

    def _calculate_experience_similarity(self, 
                                       job_experience: str, 
                                       candidate_experience: str) -> float:
        """Calculate similarity between job and candidate experience levels"""
        if not job_experience or not candidate_experience:
            return 0.0
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform([job_experience, candidate_experience])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            return 0.0

    def _calculate_skills_embedding_similarity(self, 
                                             job_skills: List[str], 
                                             candidate_skills: List[str]) -> float:
        """Calculate similarity between job and candidate skills using embeddings"""
        if not job_skills or not candidate_skills:
            return 0.0
            
        job_skills_text = ' '.join(job_skills)
        candidate_skills_text = ' '.join(candidate_skills)
        
        job_embedding = self.model.encode(job_skills_text)
        candidate_embedding = self.model.encode(candidate_skills_text)
        
        return cosine_similarity([job_embedding], [candidate_embedding])[0][0]

    def _calculate_location_embedding_similarity(self, 
                                               job_location: str, 
                                               candidate_location: str) -> float:
        """Calculate similarity between job and candidate locations using embeddings"""
        if not job_location or not candidate_location:
            return 0.0
            
        job_embedding = self.model.encode(job_location)
        candidate_embedding = self.model.encode(candidate_location)
        
        return cosine_similarity([job_embedding], [candidate_embedding])[0][0]

    def _calculate_experience_embedding_similarity(self, 
                                                 job_experience: str, 
                                                 candidate_experience: str) -> float:
        """Calculate similarity between job and candidate experience levels using embeddings"""
        if not job_experience or not candidate_experience:
            return 0.0
            
        job_embedding = self.model.encode(job_experience)
        candidate_embedding = self.model.encode(candidate_experience)
        
        return cosine_similarity([job_embedding], [candidate_embedding])[0][0] 