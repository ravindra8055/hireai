import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.parser import ResumeParser

def main():
    # Initialize parser
    parser = ResumeParser()
    
    # Get resume file path from command line argument or use default
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        print("Please provide the path to a resume file (PDF or DOCX)")
        return
    
    try:
        # Parse resume
        print(f"Parsing resume: {resume_path}")
        parsed_data = parser.parse(resume_path)
        
        # Print extracted information
        print("\nExtracted Information:")
        print("-" * 50)
        print(f"Name: {parsed_data['name']}")
        print(f"Email: {parsed_data['email']}")
        print(f"Phone: {parsed_data['phone']}")
        print(f"Location: {parsed_data['location']}")
        print(f"Total Experience: {parsed_data['total_experience']} years")
        
        print("\nSkills:")
        for skill in parsed_data['skills']:
            print(f"- {skill}")
        
        print("\nEducation:")
        for edu in parsed_data['education']:
            print(f"- {edu['degree']} in {edu['field_of_study']}")
        
        print("\nExperience:")
        for exp in parsed_data['experience']:
            print(f"- {exp['title']} at {exp['company']}")
            print(f"  Description: {exp['description']}")
        
        # Save to JSON
        output_path = f"{os.path.splitext(resume_path)[0]}_parsed.json"
        parser.save_to_json(parsed_data, output_path)
        print(f"\nParsed data saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 