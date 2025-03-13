from llm_caller import LLMCaller
from tqdm import tqdm

class AnswerConsolidator:
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller

    def answer_sub_question(self, question: str, context: str):
        prompt = f"""You are an expert who can answer a question using content from an article.

Using ONLY the provided article content below, answer the following question accurately and thoroughly:

Question:
\"""{question}\"""

Article Content:
\"""
{context}
\""

Answer (accurate and thorough):
"""
        return self.llm_caller.generate(prompt, json_format=False)

    def verify_article(self, query: str, article_title: str) -> str: # TODO: removed verification step in research, need to add it back
        prompt = f"""You are an expert assistant who can determine if an article title is closely related to a query. The title is a result of searching for an article based on a user query. Your job is to determine if the article title is a good match for the user query.

You should respond ONLY with True or False (no quotes).

User Query:
{query}

Aritcl Title:
{article_title}

The article title is closely related to the user query (True or False):  
"""
        return self.llm_caller.generate(prompt, json_format=False)

    def generate_report(self, sub_question_answers):
        sub_question_response = ""
        for i, a in tqdm(enumerate(sub_question_answers), desc="generating report"):
            sub_question_response += f"# {i+1}. Question: {a['question']}\n"
            sub_question_response += f"## Answer\n\n{a['answer']}\n"
        return sub_question_response

    def consolidate_answers(self, main_question, sub_question_response):
        prompt = f"""You are tasked with synthesizing several answers to sub-questions into a comprehensive answer to an original question. Follow these instructions carefully:

### Original Question:
"{main_question}"

### Sub-questions and Answers:
And the following summaries derived from Wikipedia articles:
{sub_question_response}

---

### Instructions for Synthesis:
- Provide a clear, coherent, and comprehensive final answer to the **original question** above.
- Explicitly reference relevant points from the provided answers.
- Synthesize information step-by-step, logically connecting ideas.
- Keep your final answer accurate and thorough.

### Final Synthesized Answer: 
"""
        return self.llm_caller.generate(prompt, json_format=False)

