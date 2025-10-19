import re
question="Compare Samsung Galaxy M36 and Samsung Galaxy F56"


models = re.findall(r'(?:Samsung\s)?(?:Galaxy\s)?([A-Z]\d+(?:\s\w+)?)(?=\s+(?:and|or|vs)|$)', question, re.IGNORECASE)
models = [m.strip() for m in models if m.strip()]
print(f"Extracted models from query: {models}")