# Create a small test script: test_serp.py
from brain import check_plagiarism_simple

# Use a common scientific fact often found in papers
test_text = "Preoperative anxiety affects 60-80% of surgical patients and can impact surgical outcomes."
result = check_plagiarism_simple(test_text)

print(f"Similarity: {result['similarity_score']}%")
print(f"Source: {result['source']}")
# SUCCESS if similarity > 80% and source is a medical journal/PubMed