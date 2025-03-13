from typing import List
from strategies.tree_of_thought import TreeNode

def _format_reasonsing_steps(reasoning: List[str]) -> str:
    """Combines reasoning steps into a single string for sending in the prompt."""
    return "\n".join([f"{i+1}. Step {i+1}: {step.strip()}" for i, step in enumerate(reasoning)])  

def generate_title(text: str) -> str:
    """Generate title for captures key components text"""
    prompt = f"""You are an expert at taking some text and generating a title that consisely and accurately captures the text.

Text: {text}

Title: 
""" 
    return prompt


def generate_approaches_for_question(question: str, max_branches: int) -> str:
    """Generates differents approaches to answering a given question"""
    prompt = f"""
## Question: 
{question}

## Expected Output Format:
* APPROACH: [brief description of the approach 1]
* APPROACH: [brief description of the approach 2]
* ...
* APPROACH: [brief description of the approach {max_branches}]


## Approaches:
Generate {max_branches} different initial approaches to answer this question. 
Each approach should be distinct and explore a different angle or methodology.

* APPROACH:
"""       
    return prompt     


def next_steps(node: TreeNode, max_branches: int) -> str:
    question = node.get_original_question()
    steps = node.get_steps_markdown()    
    if len(node.get_steps()) > 0:
        steps_tried = f"\n## Steps Tried So Far\n{steps}\n"
    else:
        steps_tried  = "\n## Steps Tried So Far\nNone\n"

    prompt = f"""You are an expert at looking at a problem, steps tried so far, and recommending what possible next steps to try to solve the problem. Each step should be a logical continuation of previous steps and explore different possibilities. Make sure to explore new thoughts and not just rewording previous steps.
## Problem
{question}
{steps_tried}
## Next Steps
Generate a maxium of {max_branches} next steps.
Provide your response as a JSON object in this format:
{{
    "next_steps": [
        "<step 1>",
        "<step 2>",
        ...
        "<step {max_branches}>"
    ]
}}
"""
    return prompt

def answer_step(node: TreeNode) -> str:
    question = node.get_original_question()
    steps = node.get_steps_markdown()
    if len(node.get_steps()) > 0:
        steps_tried = f"\n## Steps Tried So Far\n{steps}\n"
    else:
        steps_tried  = "\n## Steps Tried So Far\nNone\n"
            
    prompt = f"""You are an expert at looking at a problem, steps tried so far, and the latest step and providing an answer to the original problem.
## Problem    
{question}
{steps_tried}
## Current Step
{node.step.thought}

## Answer
Based on these steps, provide a final answer to the problem. 

If you cannot reach a definitive answer yet, respond with the following JSON:
{{
    "answer": None
}}

If you have a final answer, Provide your response as a JSON object in this format:
{{
    "answer": "<final_answer>"
}}
"""
    return prompt

def evaluate_step(node: TreeNode) -> str:
    question = node.get_original_question()
    steps = node.get_steps_markdown()
    if len(node.get_steps()) > 0:
        steps_tried = f"\n## Steps Tried So Far\n{steps}\n"
    else:
        steps_tried  = "\n## Steps Tried So Far\nNone\n"
    prompt = f"""You are an expert at looking at a problem, reasoning steps tried so far, and a proposed answer to the problem. You are also an expert at evaluating the answer and deciding how good it is.
## Problem
{question}
{steps_tried}
## Proposed Answer
{node.step.answer}

## Answer
Based on these steps, provide a final answer to the problem. 

## Confidence
Evaluate the confidence in this answer by responding to the following three questions:

1. Is the reasoning logically sound? (YES/NO)
2. Does the solution fully address the problem? (YES/NO)
3. Does the solution contain any errors or inconsistencies? (YES/NO)

Return your response as a JSON object in this format:
{{
    "logic": "<YES/NO>",
    "completeness": "<YES/NO>",
    "errors": "<YES/NO>"
}}
"""
    return prompt        


def generate_appoaches_for_question_given_reasoning(question: str, reasoning: List[str], max_branches: int) -> str:
    current_reasoning = _format_reasonsing_steps(reasoning)
            
    prompt = f"""
## Question: 
{question}

## Current Reasoning:
{current_reasoning}

## Expected Output Format:
* STEP: [description of the next reasoning step 1]
* STEP: [description of the next reasoning step 2]
* ...
* STEP: [description of the next reasoning step {max_branches}]

## Next Steps:
Generate {max_branches} different possible next steps in the reasoning process. 
Each step should be a logical continuation but explore different possibilities.

* STEP: 
"""
    return prompt


def answer_question(question: str, reasoning: List[str]) -> str:
    current_reasoning = _format_reasonsing_steps(reasoning)            
    prompt = f"""
## Question: 
{question}

## Reasoning Path:
{current_reasoning}

## Answer
Based on this reasoning path, provide a final answer to the question. 
If you cannot reach a definitive answer yet, respond with "INCOMPLETE".

Format your response as:
ANSWER: [your final answer]
"""       
    return prompt


def answer_confidence(question: str, reasoning: List[str], answer: str) -> str:
    reasoning_steps = _format_reasonsing_steps(reasoning)
    prompt = f"""
## Question: 
{question}

## Reasoning Path:
{reasoning_steps}

## Proposed Answer:
{answer}

## Confidence
Evaluate the confidence in this answer by responding to the following three questions:

1. Is the reasoning logically sound? (YES/NO/PARTIALLY)
2. Does the solution fully address the problem? (YES/NO/PARTIALLY)
3. Does the solution contain any errors or inconsistencies? (YES/NO/MAYBE)

Format your response as:
* LOGIC: [YES/NO/PARTIALLY]
* COMPLETENESS: [YES/NO/PARTIALLY]
* ERRORS: [YES/NO/MAYBE]
* EXPLANATION: [brief explanation of your evaluation]
"""
    return prompt


def compare_answers(question: str, answers: List[str]) -> str:
    answers_formatted = [
        f"### Answer {i+1}: {answer['solution'].strip()}"
        for i, answer in enumerate(answers)
    ]
    answeres_combined = "\n".join(answers_formatted)

    prompt = f"""
## Question: 
{question}

## Answers:
{answeres_combined}

## Best Answer
Evaluate these solutions based on correctness, completeness, and logical soundness.
Which solution is best? Why?

Format your response as:
* BEST SOLUTION: [number of the best solution]
* EXPLANATION: [explanation of why this solution is best]
"""    
    return prompt