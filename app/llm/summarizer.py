from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    http_client=httpx.Client(verify=False)
)


def generate_summary(chunks, pdf_name, pdf_path):

    context = "\n\n".join(
        chunk["chunk_text"]
        for chunk in chunks
    )

    pages_used = sorted(
        list(
            {
                chunk["page_number"]
                for chunk in chunks
            }
        )
    )

    prompt = f"""
You are an expert Legal and Enterprise Document Analyst.

Analyze the document and generate a professional executive summary.

RULES:

1. Use ONLY information present in the document.

2. Do NOT invent facts.

3. First determine the document type.

4. Choose section headings that naturally fit the document.

5. Do NOT force irrelevant sections.

6. Focus on the information a lawyer, manager, compliance officer,
HR representative, auditor, or business stakeholder would care about.

7. Highlight obligations, responsibilities, deadlines, risks,
financial commitments, legal clauses, ownership, governance,
dispute resolution terms, and key stakeholders whenever applicable.

8. Be concise but complete.

OUTPUT FORMAT:

DOCUMENT SUMMARY

Document Type:
...

Executive Overview:
...

Key Parties / Stakeholders:
...

Key Terms / Obligations:
...

Important Dates / Timelines:
...

Important Financial or Business Terms:
...

Key Legal, Compliance, or Risk Considerations:
...

Additional Important Information:
...

DOCUMENT CONTENT:

{context}
"""
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": "You are a legal document summarization assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000,
        temperature=0,
        seed=42,
        top_p=1
    )

    summary = response.choices[0].message.content.strip()

    return f"""
{summary}

SOURCE

PDF Name : {pdf_name}
Pages Used : {", ".join(map(str, pages_used))}
PDF Path : {pdf_path}
"""