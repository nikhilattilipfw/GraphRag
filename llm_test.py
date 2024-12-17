from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Load the tokenizer and model
model_name = "meta-llama/Llama-2-7b-chat-hf"  # Replace with your desired model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")

# Create a text generation pipeline
chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer, max_length=512, temperature=0.7)

# Input prompt
prompt = "How can I learn machine learning effectively?"

# Generate response
response = chatbot(prompt, num_return_sequences=1)

# Print the response
print("Chatbot response:")
print(response[0]["generated_text"])
