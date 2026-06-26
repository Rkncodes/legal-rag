from openai import AzureOpenAI
from dotenv import load_dotenv
from app.config import DEBUG
from app.config import VERBOSE
import os
import httpx

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    http_client=httpx.Client(verify=False)
)


def generate_answer(question, ranked_results):

    top_chunks = [item for item in ranked_results[:15] if len(item["chunk"].strip()) > 200]

    if not top_chunks:
        return "I don't know anything about that from the provided documents."

    if DEBUG:
        print("\nTOP CHUNKS SENT TO LLM\n")
        for i, item in enumerate(top_chunks, start=1):
            print(
                f"{i}. {item['metadata']['pdf_name']} | "
                f"Page {item['metadata']['page_number']} | "
                f"Score {item['score']}"
            )

    chunks   = [item["chunk"]    for item in top_chunks]
    metadata = [item["metadata"] for item in top_chunks]

    if DEBUG:
        print(f"\nChunks sent to LLM: {len(chunks)}")

    context_parts = []
    chunk_map     = {}

    for i, chunk in enumerate(chunks, start=1):
        chunk_id = f"CHUNK_{i:03d}"
        chunk_map[chunk_id] = metadata[i - 1]
        context_parts.append(f"""
{chunk_id}

CONTENT:
{chunk}
""")
        
        print("\nCHUNK MAP DEBUG:")
    for cid, meta in chunk_map.items():
        print(f"  {cid} -> page={meta['page_number']} heading={meta.get('heading','')[:50]}")

    context = "\n\n".join(context_parts)
    
    print("\nCHUNK MAP:")
    for cid, meta in list(chunk_map.items())[:5]:
        print(f"  {cid} -> page={meta['page_number']} chunk_id={meta.get('chunk_id')} heading={meta.get('heading','')[:40]}")

    if VERBOSE:
        print("\nCHUNKS SENT TO LLM\n")
        for i, chunk in enumerate(chunks, start=1):
            print(f"\nCHUNK {i}")
            print(
                f"PDF: {metadata[i-1]['pdf_name']} | "
                f"Page: {metadata[i-1]['page_number']}"
            )
            print(chunk)
            print("=" * 100)

    prompt = f"""
You are a Legal Document Assistant.

IMPORTANT RULES:

1. Answer ONLY using the provided context.

2. When answering factual questions, provide the exact wording from the document whenever possible.

3. Do NOT use outside knowledge.

4. Do NOT make assumptions.

5. Do NOT infer facts.

6. If neither the answer nor a matching heading/section title
is present in the context, respond EXACTLY:

I don't know anything about that from the provided documents.

Information may appear inside tables, lists, OCR text, or poorly formatted text.

If the answer can be directly determined from the provided context, extract it even when the formatting is broken.

Do not require perfectly formatted tables.

Use nearby values and row structure when identifying quantities, item names, clause numbers, or document fields.

7. After your answer, write:

USED_CHUNKS:
CHUNK_XXX
CHUNK_YYY

List ONLY chunks whose content directly contains the clause text you quoted in your answer.
Do NOT cite chunks that are merely referenced or mentioned in passing.
Do NOT cite chunks that contain related but different clauses.
Only use chunk IDs that appear in the provided context.
Do not invent chunk IDs.

8. After USED_CHUNKS, add one line:

CONFIDENCE: X%

Where X is your honest estimate (0-100) of how completely
the provided context answered the question.
- 90-100%: full clause text found, complete answer
- 70-89%: most of the clause found, minor gaps
- 50-69%: partial clause found, some content missing
- Below 50%: very little relevant content found

Only base this on what is actually in the context.

9. If the user asks for:

- a section
- a clause
- obligations
- responsibilities
- definitions
- terms
- conditions
- provisions
- schedules
- annexures
- agreement contents
- policy contents
- contract contents

then return the complete relevant text available in the provided context.

If the user's question matches or closely resembles a section title,
clause title, heading, subsection title, schedule title,
annexure title, policy title, or contract heading present in the context:

treat the question as a request for the contents of that section.

Return the full text associated with that heading.

Do NOT require the heading to contain a formal definition.

Do NOT summarize, shorten, paraphrase, compress, or omit sub-clauses.

Include all numbered clauses, sub-clauses, bullet points, and items available in the retrieved context.

When returning a clause or section, always start with the full heading exactly as it appears in the document,
followed by the clause number if present, then the full text.

10. Only provide a summary, analysis, interpretation, explanation, comparison,
or simplification when the user explicitly asks for one.

11. If the user explicitly asks for an explanation, summary, interpretation, or analysis:

1. First provide the relevant clause(s) from the document.

2. Then provide a separate section titled:

EXPLANATION

3. Explain the clause in plain English using only information present in the provided context.

4. Break the explanation into logical headings and bullet points wherever appropriate.

5. Describe:
   - what the clause means
   - what obligations it creates
   - what rights it grants
   - what consequences follow
   - any deadlines, payment periods, notice periods,
     percentages, penalties, service credits,
     termination rights, or monetary amounts
     explicitly mentioned in the clause

6. Do not introduce facts that are not supported by the context.

Use the following style:

EXPLANATION

Meaning:
...

Key Obligations:
...

Rights:
...

Consequences:
...

Exceptions:
...

CONTEXT:

{context}

QUESTION:

{question}
"""

    print("\n" + "=" * 100)
    print("CONTEXT SENT TO GPT")
    print("=" * 100)
    print(context)
    print("=" * 100)
    print("\nQUESTION:", question)

    if VERBOSE:
        print("\nPROMPT SENT TO GPT\n")
        print(prompt)

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a legal document assistant."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=1500,
        temperature=0,
        top_p=1,
        seed=42
    )

    print("\nCONTEXT LENGTH:", len(context))

    answer = response.choices[0].message.content.strip()

    if VERBOSE:
        print("\nRAW LLM RESPONSE\n")
        print(answer)
        print("=" * 100)

    # ── parse used chunks ─────────────────────────────────────────────
    best_source    = metadata[0]
    used_sources   = []
    unique_sources = []

    if "USED_CHUNKS:" in answer:
        used_chunks_text = answer.split("USED_CHUNKS:")[1]
        used_chunk_ids = [
            line.strip()
            for line in used_chunks_text.splitlines()
            if line.strip().startswith("CHUNK_")
        ]

        for chunk_id in used_chunk_ids:
            if chunk_id in chunk_map:
                used_sources.append(chunk_map[chunk_id])

        if used_sources:
            for source in used_sources:
                if source not in unique_sources:
                    unique_sources.append(source)

            # sort by page number so lowest page cited first
            unique_sources.sort(key=lambda x: x.get("page_number", 0))
            best_source = unique_sources[0]

        print("\nUSED SOURCES:")
        for source in used_sources:
            print(source["pdf_name"], source["page_number"])

        print("\nCITATION SOURCE:")
        print(best_source)

    if answer.startswith(
        "I don't know anything about that from the provided documents."
    ):
        return "I don't know anything about that from the provided documents."

    if DEBUG:
        print(
            f"\nFINAL SOURCE: "
            f"{best_source.get('pdf_name')} | "
            f"Page {best_source.get('page_number')}"
        )

    # ── build sources text ────────────────────────────────────────────
    sources_to_use = unique_sources if unique_sources else [best_source]

    sources_text = ""
    for source in sources_to_use:
        sources_text += (
            f"PDF Name : {source.get('pdf_name', 'Unknown')}\n"
            f"Page No  : {source.get('page_number', 'Unknown')}\n"
            f"PDF Path : {source.get('pdf_path', 'Unknown')}\n\n"
        )

    return f"""
{answer}

SOURCES USED

{sources_text}
"""