from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint
from huggingface_hub import login
import os

def authenticate(api_token: str):
    os.environ['HUGGINGFACEHUB_API_TOKEN'] = api_token
    login(api_token)

def template() -> PromptTemplate:
    prompt = PromptTemplate(
        input_variables=["paragraph"],
        template="""
            Extract the following data from the resume and convert it to the specified JSON format:

            1. **User Information**:
               - **Name**: Extract the full name of the user.
               - **Designation**: Extract the current designation or job title of the user.
               - **Summary of Achievements**: A summary of key achievements.
               - **Skills**: List all mentioned skills.

            2. **Projects**:
               - Extract each project's title, description, technologies used, role, team size, and a brief summary of the project.

            JSON Format:
            {{
                "user": {{
                    "name": "Name of the user",
                    "designation": "Designation of the user",
                    "skills": ["skill1", "skill2", ...],
                    "summary": "Summary of achievements"
                }},
                "projects": [
                    {{
                        "title": "Title of the project",
                        "description": "Description of the project",
                        "tech": "Technologies used in the project",
                    }}
                ]
            }}

            Input Data: {paragraph}
            Answer:
        """
    )
    return prompt

def llmchain(api_token: str, repo_id: str, max_new_tokens: int) -> LLMChain:
    llm = HuggingFaceEndpoint(repo_id=repo_id, token=api_token, max_new_tokens=max_new_tokens)
    prompt = template()
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    return llm_chain

def extract_resume_data(api_token: str, repo_id: str, max_new_tokens: int, paragraph: str) -> str:
    authenticate(api_token)
    llm_chain = llmchain(api_token, repo_id, max_new_tokens)
    result = llm_chain.run(paragraph)
    return result

