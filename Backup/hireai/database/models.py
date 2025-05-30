from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: datetime
    end_date: Optional[datetime]
    gpa: Optional[float]

class Experience(BaseModel):
    company: str
    title: str
    start_date: datetime
    end_date: Optional[datetime]
    description: str
    skills: List[str]

class Candidate(BaseModel):
    id: Optional[str]
    name: str
    email: EmailStr
    phone: Optional[str]
    location: Optional[str]
    skills: List[str]
    education: List[Education]
    experience: List[Experience]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class Job(BaseModel):
    id: Optional[str]
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    salary_range: Optional[str]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now() 