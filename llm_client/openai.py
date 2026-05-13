from openai import AzureOpenAI
from openai import OpenAI
import os

def _get_openai_client() -> AzureOpenAI:
    client = OpenAI(
                base_url =os.environ.get("AZURE_OPENAI_ENDPOINT", ""),  
                api_key=os.environ.get("AZURE_OPENAI_API_KEY", "") )
    return client