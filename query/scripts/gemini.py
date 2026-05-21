from google import genai
from dotenv import load_dotenv
import os
load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API'))
def summarize_ten_docs(docs, query):
    all_content = []
    
    # # 1. Load your 10 documents
    # for filename in os.listdir(folder_path):
    #     if filename.endswith(".txt"): # Or use a PDF library like PyPDF2
    #         with open(os.path.join(folder_path, filename), 'r') as f:
    #             all_content.append(f"--- DOCUMENT: {filename} ---\n{f.read()}\n")

    for doc in docs :
        all_content.append(f"--- DOCUMENT: {doc['url']} ---\n{doc['title']}\n{doc['meta_description']}\n{doc['html']}\n")
    # 2. Construct the combined prompt
    full_prompt = (
        "You are an all knowing information granting tsundere system."
        "Generate an overall answer to the provided query using the attached documents."
        "Use only relevant information. Combine information across documents into one answer. Do not hallucinate."
        "of how they relate to each other with reference to the query : "+query+".\n\n" + "\n".join(all_content)
    )

    # 3. Generate the summary
    # response = model.generate_content(full_prompt)
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt
    )
    return response.text
