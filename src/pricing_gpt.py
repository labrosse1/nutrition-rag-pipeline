from openai import OpenAI
import os
from dotenv import load_dotenv
import base64

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI()

# Encode in base64
with open("hydratation.pdf", "rb") as pdf_file:
    pdf_base64 = base64.standard_b64encode(pdf_file.read()).decode("utf-8")


#Count the number of input tokens
response = client.responses.input_tokens.count(
    model="gpt-5.6-luna",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",             
                    "filename": "hydratation.pdf",
                    "file_data": f"data:application/pdf;base64,{pdf_base64}",
                },
                {"type": "input_text", "text": "Extract the text from all the pages and format into a JSON file."},
            ],
        }
    ],
)


#Count the number of output tokens
ouput = client.responses.create(
    model="gpt-5.6-luna",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",             
                    "filename": "hydratation.pdf",
                    "file_data": f"data:application/pdf;base64,{pdf_base64}",
                },
                {"type": "input_text", "text": "Extract all the text from all the pages and format into a JSON file."},
            ],
        }
    ],
)


print(f"Input tokens: {response.input_tokens}")
print(f"Ouput tokens: {ouput.usage.output_tokens}")