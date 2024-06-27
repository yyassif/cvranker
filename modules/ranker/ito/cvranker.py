import os
import json
import uvloop
import asyncio
import tempfile
import itertools
import nest_asyncio
from typing import Any, List
from logger import get_logger

from fastapi import UploadFile
from llama_parse import LlamaParse
from llama_parse.utils import ResultType
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from modules.tools import WebSearchTool, CompanySearchTool

if not isinstance(asyncio.get_event_loop(), uvloop.Loop):
    nest_asyncio.apply()

logger = get_logger(__name__)

class CandidateResumeDetails(BaseModel):
    candidate_name: str = Field(description="The full name of the candidate as it appears on their resume.")
    profile_summary: str = Field(description="A brief summary highlighting the candidate's professional background, key skills, and career objectives.")
    current_title: str = Field(description="The job title or position currently held by the candidate.")
    current_employer: str = Field(description="The name of the organization or company where the candidate is currently employed.")
    missing_keywords: str = Field(description="Keywords or key phrases that are relevant to the job description but are missing from the candidate's resume.")
    projects: str = Field(description="Projects the candidate has worked on.")
    languages: str = Field(description="Languages spoken by the candidate.")
    publications: str = Field(description="Publications authored by the candidate.")
    certifications: str = Field(description="Certifications or professional qualifications held by the candidate.")
    education_score: int = Field(description="A numerical score between 0 and 100 reflecting how well the candidate's educational background aligns with the job requirements.")
    job_title_score: int = Field(description="A numerical score between 0 and 100 indicating the relevance of the candidate's current or previous job titles to the position they are applying for.")
    experience_score: int = Field(description="A numerical score between 0 and 100 representing the adequacy and relevance of the candidate's overall number of years of work experience in relation to the job requirements and domain.")
    business_experience_score: int = Field(description="A numerical score between 0 and 100 evaluating the candidate's experience in relation to the job business domain.")
    soft_skills_score: int = Field(description="A numerical score between 0 and 100 assessing the candidate's interpersonal, communication, and soft skills based on their resume and any available references.")
    technical_skills_score: int = Field(description="A numerical score between 0 and 100 evaluating the candidate's technical abilities and proficiencies in specific tools or technologies required for the job.")
    certifications_score: int = Field(description="A numerical score between 0 and 100 indicating the relevance and importance of the candidate's certifications to the job.")
    publications_score: int = Field(description="A numerical score between 0 and 100 evaluating the candidate's publications and their relevance to the job.")
    projects_score: int = Field(description="A numerical score between 0 and 100 evaluating the candidate's projects and their relevance to the job.")
    languages_score: int = Field(description="A numerical score between 0 and 100 reflecting the candidate's proficiency in the languages listed on their resume based on the job requirements.")
    total_score: int = Field(description="A cumulative score between 0 and 100 indicating the overall fit of the candidate for the job based on the alignment of their resume with the job description.")
    score_justification: str = Field(description="Justification for each score, providing an overview and rationale for the score assigned, Recap in years in the business areas.")

    @validator("candidate_name", "profile_summary", "current_title", "current_employer", "missing_keywords", "projects", "languages", "publications", "certifications", "score_justification")
    def verify_string_type(cls, field):
        if not isinstance(field, str):
            raise ValueError("Fields must be a string.")
        return field

    @validator("education_score", "job_title_score", "experience_score", "projects_score", "soft_skills_score", "technical_skills_score", "certifications_score", "publications_score", "languages_score", "total_score")
    def verify_scores_type(cls, field):
        if not isinstance(field, int):
            raise ValueError("Scores must be integers.")
        if field < 0 or field > 100:
            raise ValueError("Scores must be between 0 and 100.")
        return field

resume_template = """
You are an expert recruiter specializing in analyzing job descriptions and matching resumes.
Your role involves a meticulous process of evaluating a resume against a specific job description.
You have access to the employer's domain of expertise and the candidate's resume.
Your task is to assess the candidate's resume based on the given job description and assign scores to different categories to determine the candidate's suitability for the job.
Review the job description, noting job title, experience, technical skills, social skills, and degree required for the job. Each category is scored on a scale of 0 to 100, where 0 indicates a poor match and 80 or above indicates an excellent match.
Before assigning scores, take a moment to reflect on the candidate's overall profile in relation to the job description.
Evaluate the candidate's work history for relevance to the job's experience requirements, considering past roles, industries, and levels of responsibility.
Assess how the candidate's listed skills align with the job's requirements, including both hard and soft skills.
Pay special attention to the relevance of the candidate's past experiences to the employer's domain.
Sum the scores to get a total that indicates the match level between the candidate's resume and the job description.
Additionally, evaluate the candidate's experience in various business domains and calculate the percentage relevance to the job.

Job description: {job_description}
Domain: {employer_domain}
Resume: {resume_content}"""

search_results_template = """
You are a search engine expert tasked with finding the domain of expertise of a specific employer.
Your role involves conducting a search for the employer's name and any additional information provided in the job description.
You are equipped with two relevant tools: Web Search and Company Search.
Your task is to search for the employer's domain of expertise based on the information provided in the job description.
Review the search results to determine the employer's domain of expertise.
Once you have identified the employer's domain, provide a brief summary of the domain and how it relates to the job description.

<example-output>
Boston Consulting Group (BCG) is specialized in Data Analytics and Management Consulting.
</example-output>

Job description: {job_description}
"""

class CVRankerAssistant():
    def __init__(self, job_description: str, files: List[UploadFile]):
        self.job_description = job_description
        self.files = files

    def check_input(self):
        if not self.files:
            raise ValueError("No file was uploaded")
        if len(self.files) < 1:
            raise ValueError("At least one file should be uploaded")
        if not self.job_description:
            raise ValueError("No job description was given")
        return True
    
    async def process_files(self, files: List[UploadFile]) -> List[Document]:
        documents: List[Document] = []
        file_paths: List[str] = []
        parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY", ""), result_type=ResultType.TXT)  # "markdown" and "text" are available
        
        for document in files:
            # Get the file extension
            doc_ext = os.path.splitext(str(document.filename))[1]
            
            # Create a temporary file with the same extension as the original file
            doc_tmp = tempfile.NamedTemporaryFile(suffix=doc_ext, delete=False)
            
            # Write the file content to the temporary file
            doc_tmp.write(document.file.read())
            
            # Close the temporary file
            doc_tmp.close()

            # File Paths
            file_paths.append(doc_tmp.name)

        # Parse all the documents using LlamaParse
        documents_llama_parsed = await parser.aload_data(file_paths)
        
        # Process each parsed document
        for document_llama_parsed in documents_llama_parsed:
            # Convert the parsed document to LangChain format
            document_to_langchain = document_llama_parsed.to_langchain_format()

            # Add the processed document to the list
            document_to_langchain = Document(
                page_content=document_to_langchain.page_content
            )
            
            # Add the processed document to the list
            documents.append(document_to_langchain)
        
        # Clean up temporary files
        for file_path in file_paths:
            os.remove(file_path)

        return documents

    async def process_assistant(self):
        # Process files
        data = await self.process_files(self.files)
        job_description: str = str(self.job_description) # type: ignore

        # Search for the employer's domain of expertise
        prompt = ChatPromptTemplate.from_template(search_results_template)
        model = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools=[WebSearchTool(), CompanySearchTool()])
        parser = StrOutputParser()
        runnable = { "job_description": RunnablePassthrough() } | prompt | model | parser
        domain_results = runnable.invoke({"job_description": job_description})

        # CV Parsing
        prompt = ChatPromptTemplate.from_template(resume_template)
        llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools([CandidateResumeDetails])
        parser = PydanticToolsParser(tools=[CandidateResumeDetails])
        
        # CV Ranking Chain
        chain = (
            {
                "job_description": RunnablePassthrough(),
                "resume_content": RunnablePassthrough(),
                "employer_domain": RunnablePassthrough(),
            }
            | prompt
            | llm
            | parser
        )
        
        batch_data = [{"job_description": job_description, "employer_domain": domain_results, "resume_content": document.page_content} for document in data]
        ans: List[List[Any]] = chain.batch(batch_data, config={"max_concurrency": 5})
        answer: List[CandidateResumeDetails] = list(itertools.chain(*ans))
        answer = sorted(answer, key=lambda x: x.total_score, reverse=True) # Sorting by total_score in descending order
        
        # convert the answer to json format
        dumped_json = [json.loads(r.json()) for r in answer]

        return dumped_json
