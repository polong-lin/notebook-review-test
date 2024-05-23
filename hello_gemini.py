import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

vertexai.init()

MODEL_ID = "gemini-1.5-flash-preview-0514"  # @param {type:"string"}

model = GenerativeModel(MODEL_ID)

# Load a example model with system instructions
example_model = GenerativeModel(
    MODEL_ID,
    system_instruction=[
        "You are a cheerful professor.",
    ],
)

prompt = """
  User input: Why is the sky blue?
  Answer:
"""


# Set contents to send to the model
contents = [prompt]

# Prompt the model to generate content
response = example_model.generate_content(
    contents,
)

# Print the model response
print(f"\nAnswer:\n{response.text}")
