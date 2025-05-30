from setuptools import setup, find_packages

setup(
    name="hireai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gradio",
        "plotly",
        "pandas",
        "scikit-learn",
        "sentence-transformers",
        "openai",
        "supabase",
        "python-dotenv",
        "spacy",
        "pyresparser",
        "nltk",
        "pdfminer.six",
        "docx2txt",
        "beautifulsoup4"
    ],
    python_requires=">=3.8",
) 