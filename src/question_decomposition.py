import json
from llm_caller import LLMCaller

class QuestionDecomposer:
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller

    def analyze(self, question: str):
        prompt = f"""You are an expert assistant tasked with analyzing user questions to prepare them for further processing. Analyze the following question and provide a structured JSON response with the following fields:

1. **intent**: Describe the main goal or purpose of the user's question.
2. **key_components**: List the key topics, concepts, or keywords present in the question that are essential to understanding it.
3. **context**: Provide any relevant background information inferred from the question (e.g., domain, subject matter, or situational details).

Here is an example of how you should respond:
{{
    "intent": "Explain a concept",
    "key_components": ["machine learning", "bias", "variance"],
    "context": "Technical inquiry about statistical modeling in machine learning"
}}

Now analyze this question:
"{question}"
        """
        return self.llm_caller.generate(prompt)

    def decompose(self, question, analysis):
        prompt = f"""You are an expert assistant tasked with breaking down a complex question into foundational sub-questions. Each sub-question should focus on understanding one specific aspect of the original query or its components.

Original Question:
"{question}"

Original Question Analysis:
"{json.dumps(analysis, indent=2)}"

Decomposition Instructions:
1. Identify all key concepts or subjects mentioned in the original question.
2. Generate sub-questions that help explain or define each concept independently.
3. Create sub-questions that explore relationships between these concepts.
4. Ensure each sub-question contributes toward answering the original query.

Provide your response as a JSON object in this format:
{{
    "questions": [
    {{
        "question": "<sub-question>",
        "key_components": ["<key topic, concept, or keyword in the question>", ...]"
    }},
    ...
    ]
}}
        """
        return self.llm_caller.generate(prompt)

    def revise(self, question, analysis, questions):
        prompt = f"""You are an expert assistant tasked with breaking down a complex question into foundational sub-questions. Each sub-question should focus on understanding one specific aspect of the original question or its core components.

Original Question:
"{question}"

Original Question Analysis:
"{json.dumps(analysis, indent=2)}"    

Review the sub-questions listed below. Critically analyze them:
- Are they complete, covering all aspects of question?
- Are they clear and well-defined?
- Are there any redundant or overlapping sub-questions?

Provide a refined, improved list of sub-questions addressing these issues explicitly.

Original Sub-Questions:
"{json.dumps(questions, indent=2)}"

Provide your response as a JSON object in this format:
{{
    "questions": [
    {{
        "question": "<sub-question>",
        "key_components": ["<key topic, concept, or keyword in the question>", ...]"
    }},
    ...
    ]
}}
        """
        return self.llm_caller.generate(prompt)
    
    def get_titles(self, questions):
        prompt = f"""You are an expert assistant tasked with generating concise, Wikipedia-style article titles from a provided list of questions. Each title must reflect an existing Wikipedia page or closely align with a recognizable general concept or established field as commonly titled on Wikipedia.

List of questions:
{json.dumps(questions, indent=2)}

For each question:

1. Carefully identify the **main general topic or established field** covered by the question.
2. If multiple distinct concepts are involved, choose the **single most prominent or overarching concept** that aligns best with typical Wikipedia titles.
3. Generate a title that closely matches actual Wikipedia conventions—brief, precise, widely recognizable, and natural.
    - Avoid overly specific or complex phrasing.
    - Use nouns or concise noun phrases rather than questions or long descriptions.
    - Verify internally that the generated title aligns closely with actual Wikipedia articles.

Examples:
- **Question:** "How does regular exercise influence brain chemistry and function, which may affect mental health positively?"  
    **Title:** "Exercise physiology"

- **Question:** "What are the core components involved in photosynthesis, and how do they interact to convert solar energy into chemical energy?"  
    **Title:** "Photosynthesis"

Provide your response in the following structured JSON format:

```json
{{
    "titles": [
    {{
        "question": "<original_question>",
        "title": "<Wikipedia-style_title>"
    }},
    ...
    ]
}}
    """
        return self.llm_caller.generate(prompt)

    def get_queries(self, questions):
        prompt = f"""You are an expert assistant tasked with optimizing questions for execution as internet search queries. Each question should add a concise, keyword-optimized query suitable for search engines like Google.

Here is the list of questions:
{json.dumps(questions, indent=2)}

For each question:
1. Include the original question without any changes.
2. Extract the most important keywords and words from the question.
3. Optimize the query for search engines by focusing on concise and relevant keywords.
4. Include synonyms or related terms if they improve the likelihood of finding relevant information.

Provide your response as a JSON object in the following format:
{{
"queries": [
    {{
        "question": "<question>",
        "query": "<keyword_optimized_query>"
    }},
    ...
]
}}
        """
        return self.llm_caller.generate(prompt)
