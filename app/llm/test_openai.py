from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
    http_client=httpx.Client(verify=False)
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a legal document assistant."
        },
        {
            "role": "user",
            "content": "Reply exactly: Azure Connection Successful"
        }
    ],
    max_tokens=1000,
    temperature=0,
    seed=42,
    top_p=1,
    model=deployment
)

print(response.choices[0].message.content)