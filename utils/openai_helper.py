import os
import json
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI

class AzureOpenAIAnalyzer:
    """Uses Azure OpenAI to analyze GitHub repositories"""
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        # Load environment variables
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        
        if not all([self.api_key, self.endpoint, self.deployment]):
            raise ValueError("Missing Azure OpenAI configuration. Please set environment variables.")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
    
    def analyze_repo(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository data and extract required information"""
        # Prepare relevant content for analysis
        content = self._prepare_content_for_analysis(repo_data)
        
        # Create the prompt for analysis
        prompt = self._create_analysis_prompt(repo_data, content)
        
        # Send to Azure OpenAI for analysis
        response = self._get_openai_analysis(prompt)
        
        # Parse and return the analysis results
        return self._parse_analysis_results(response)
    
    def _prepare_content_for_analysis(self, repo_data: Dict[str, Any]) -> str:
        """Prepare repository content for analysis"""
        content_parts = []
        
        # Add README content
        if repo_data.get("readme"):
            content_parts.append("# README Content\n" + repo_data["readme"])
        
        # Add key files content (limit to avoid token limits)
        files_content = []
        total_chars = 0
        max_chars = 50000  # Limit total content to avoid token limits
        
        for file in repo_data.get("files", []):
            file_content = f"# File: {file['path']}\n{file['content']}"
            if total_chars + len(file_content) <= max_chars:
                files_content.append(file_content)
                total_chars += len(file_content)
            else:
                # Add a summary instead of full content
                files_content.append(f"# File: {file['path']} (summary only due to size)")
                
        if files_content:
            content_parts.append("# Key Files\n" + "\n\n".join(files_content))
        
        # Information about architecture diagrams
        if repo_data.get("architecture_diagrams"):
            diagrams = "\n".join([f"- {url}" for url in repo_data["architecture_diagrams"]])
            content_parts.append("# Architecture Diagrams\n" + diagrams)
            
        return "\n\n".join(content_parts)
    
    def _create_analysis_prompt(self, repo_data: Dict[str, Any], content: str) -> str:
        """Create a detailed prompt for Azure OpenAI analysis"""


        ask_sage_info = """a web based tool that provides access to large language models. including Azure OpenAI,
            It is a paid, licence based service.
            It is not Government Owned,
            It is RBAC enabled,
            It is deployed in Azure to Azure Government Cloud,
            It does provide chat history,
            It does allow file upload, 
            It does enable agents,
            It does not enables the use of organization data, 
            It does offer external APIs 
            It does offer tool usage"""

        nipr_gpt_info = """a web based tool that provides access to large language models.
            It is Government Owned,
            It is RBAC enabled,
            It does provide chat history,
            It does allow file upload, 
            It does not enable agents,
            It does not enables the use of organization data, 
            It does not offer external APIs 
            It does not offer tool usage"""

        camo_gpt_info = """a web based tool that provides access to large language models.
            It is Government Owned,
            It is RBAC enabled,
            It does provide chat history,
            It does allow file upload, 
            It does not enable agents,
            It does not enables the use of organization data, 
            It does offer external APIs 
            It does not offer tool usage"""
        
        aiflow_info = """a web based tool that provides access to large language models.
            It is Government Owned,
            It is RBAC enabled,
            It is deployed in Azure to Azure Government Cloud,
            It does provide chat history,
            It does allow file upload, 
            It does enable agents,
            It does enable the use of organization data, 
            It does offer external APIs 
            It does offer tool usage"""


        return f"""
You are a cloud architecture analyst specializing in Azure solutions. 
I need you to analyze the following GitHub repository and extract specific information.
Assume the repository ownership is {repo_data['owner']} and the repository name is {repo_data['name']}.  
If not explicitly stated, assume the repository is not owned by the US Government.

Repository: {repo_data['url']}
Owner: {repo_data['owner']}
Name: {repo_data['name']}

Here is the content from the repository:

{content}

Based on this content, answer the following questions in JSON format:

1. Is RBAC (Role-Based Access Control) enabled in this solution? Specifically, RBAC within the application (for uploading data, etc.), 
not Azure RBAC to the services.
2. Is this solution ready for Azure Government Cloud?
3. Is this solution ready for Azure Government SECRET or TOP SECRET Cloud?
4. Does this solution maintain chat history?
5. How many different Azure services are used in this solution?
6. Does this solution include architecture diagrams? If yes, describe them.
7. What are the key differentiators of this solution from AskSage {ask_sage_info}?
8. What are the key differentiators of this solution from NIPRGPT {nipr_gpt_info}?
9. What are the key differentiators of this solution from CamoGPT {camo_gpt_info}?
10. What are the key differentiators of this solution from AIFLow {aiflow_info}?
11. What deployment method does this solution use?
12. What is the estimated cost to deploy and run this solution?
13. Any additional notes or observations about this solution?

Format your response as a valid JSON with the following keys:
rbac_enabled, azure_gov_ready, azure_secret_ready, chat_history, azure_services_count, 
architecture_diagram_present, differentiators_from_asksage, differentiators_from_niprgpt, 
differentiators_from_camogpt, deployment_method, costs_estimate, notes

For each answer, provide a brief explanation and confidence level (high, medium, low).
Please ensure the JSON is well-structured and valid. 
use the key "answer" for the answer, "explanation" for the explanation, and "confidence" for the confidence level.
If the answer is a boolean, use "true" or "false" (without quotes).
"""
    
    def _get_openai_analysis(self, prompt: str) -> str:
        """Send prompt to Azure OpenAI and get analysis"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes GitHub repositories for Azure solutions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Azure OpenAI: {str(e)}")
            return "{}"  # Return empty JSON on error
    
    def _parse_analysis_results(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from Azure OpenAI"""
        try:
            # Extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Attempt to parse whole response
                return json.loads(response)
                
        except json.JSONDecodeError:
            # If parsing fails, create a structured response
            print("Failed to parse JSON response")
            return {
                "rbac_enabled": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "azure_gov_ready": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "azure_secret_ready": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "chat_history": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "azure_services_count": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "architecture_diagram_present": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "differentiators_from_asksage": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "differentiators_from_niprgpt": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "differentiators_from_camogpt": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "deployment_method": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "costs_estimate": {"value": "Unknown", "explanation": "Could not determine", "confidence": "low"},
                "notes": {"value": "Error processing repository data", "confidence": "low"}
            }
