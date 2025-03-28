from typing import List
from strategies.tree_of_thought import TreeNode
from strategies.react import Observation

# TREE-OF-THOUGHT

def get_answers_markdown(answers: List[TreeNode]) -> str:
    result = []
    for i, answer in enumerate(answers):
        answer_markdown = f"### Answer {i+1}:\n{answer}"
        result.append(answer_markdown)
    return "\n".join(result)

def generate_title(text: str) -> str:
    """Generate title for captures key components text"""
    prompt = f"""You are an expert at taking some text and generating a title that consisely and accurately captures the text.

Text: {text}

Title: 
""" 
    return prompt

def three_experts(question: str) -> str:
    prompt = f"""Imagine three different experts are answering this question.
All experts will write down 1 step of their thinking,
then share it with the group.
Then all experts will go on to the next step, etc.
If any expert realises they're wrong at any point then they leave.
The experts continue to discuss until an answer is found.
Be sure to provide the final answer with "ANSWER:" so it can be extracted later.

**REMEMBER TO CONTINUE THE EXPERT CONVERSATION UNTIL AN ANSWER IS FOUND!**

## Example 1
### Question
Bob is in the living room.
He walks to the kitchen, carrying a cup.
He puts a ball in the cup and carries the cup to the bedroom.
He turns the cup upside down, then walks to the garden.
He puts the cup down in the garden, then walks to the garage.
Where is the ball?

### Experts
* Expert 1: The ball is in the living room.
* Expert 2: The ball is in the kitchen.
* Expert 3: The ball is in the bedroom.
* Expert 1: Bob carries the cup to the bedroom, so the ball must be in the cup.
* Expert 2: Oh, I see my mistake. Yes, the ball is in the cup.
* Expert 3: Agreed, the ball is in the cup in the bedroom.
* Expert 1: Next, Bob turns the cup upside down in the bedroom.
* Expert 2: After that, Bob walks to the garden and puts the cup down.
* Expert 3: Therefore, the ball must have fallen out of the cup when Bob turned it upside down in the bedroom. So, the ball is in the bedroom, not in the cup anymore.
* Expert 1: Oh, you're right. I made a mistake. The ball is in the bedroom, not in the cup.
* Expert 2: Agreed, the ball is in the bedroom.
* Expert 3: Bob then walks to the garage, so the ball remains in the bedroom. It is not in the garden or the garage.
* Expert 1: Absolutely, the ball is still in the bedroom.
* Expert 2: Yes, the ball hasn't moved from the bedroom.
* Expert 3: Therefore, the ball is in the bedroom, not in the garden or the garage.
All three experts agree that the ball is in the bedroom.

### Answer
ANSWER: The ball is in the bedroom.

## Assistant
### Question
{question}

### Experts
"""
    return prompt

def next_steps(node: TreeNode, max_branches: int) -> str:
    question = node.question
    steps = node.get_steps_markdown()    
    steps_tried = f"\n## Reasoning Steps\n{steps}\n"

    prompt = f"""You are an expert at looking at a problem, understanding the reasoning steps, and recommending what possible next steps to try to solve the problem. Each step should be a logical continuation of previous steps and explore different possibilities. Make sure to explore new thoughts instead of just rewording previous steps.
## Problem
{question}
{steps_tried}
## Next Steps
Generate a maximum of {max_branches} next steps.
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
    question = node.question
    steps = node.get_steps_markdown()
    steps_tried = f"\n## Reasoning Steps\n{steps}\n"
            
    prompt = f"""You are an expert at looking at a problem, following the reasoning steps, and attempting to provide an answer to the problem if one can be found. Please use the tools provided if you need external information to help answer the question.
## Problem    
{question}
{steps_tried}
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
    question = node.question
    steps = node.get_steps_markdown()
    steps_tried = f"\n## Reasoning Steps\n{steps}\n"
    prompt = f"""You are an expert at looking at a problem, understanding reasoning steps, and a proposed answer to the problem. You are also an expert at evaluating the answer and deciding how good it is.
## Problem
{question}
{steps_tried}
## Proposed Answer
{node.step.answer}

## Confidence
Evaluate the confidence in this answer by responding to the following three questions:

1. Is the reasoning logically sound? (YES/NO)
2. Does the solution fully address the problem? (YES/NO)
3. Is the answer clear and easy to understand? (YES/NO)

Return your response as a JSON object in this format:
{{
    "logic": "<YES/NO>",
    "completeness": "<YES/NO>",
    "clarity": "<YES/NO>"
}}
"""
    return prompt        

def compare_answers(answers: List[TreeNode]) -> str:
    question = answers[0].question
    answers_markdown = get_answers_markdown(answers)
    prompt = f"""
## Problem: 
{question}

## Answers:
{answers_markdown}

## Best Answer
Evaluate these answers based on correctness, completeness, and logical soundness.
Which solution is best? Why?

Format your response as a JSON object in this format:
{{
    "best_answer": <best_answer: int>
}}
"""    
    return prompt

# ATOM-OF-THOUGHT

def decompose_question(question: str) -> str:
    prompt = f"""You are an expert at breaking down a complex question into simpler subquestions.

Please decompose this question into 3-5 simpler subquestions that would help answer the original question.
For each subquestion, indicate if it depends on the answer to any other subquestion.

Use the following definition of dependency: A subquestion is dependent on another if it requires information *not* directly present in the original question, but derived from the answer to another subquestion.

Be consistent when you format the "Subquestion:" and "Dependencies:" since this information will be extracted later.

## Example 1
### Question
How far is it from New York to Los Angeles?

### Subquestions
* Subquestion 1
  * Subquestion: Where is New York located?
  * Dependencies: None
* Subquestion 2
  * Subquestion: Where is Los Angeles located?
  * Dependencies: None
* Subquestion 3
  * Subquestion: What is the distance between New York and Los Angeles?
  * Dependencies: Subquestion 1, Subquestion 2

## Assistant
### Question
{question}

### Subquestions
"""
    return prompt

def answer_subquestion(question: str, subquestion: str) -> str:
    prompt = f"""You are an expert at answering subquestions. You will be given a subquestion and the original question from which it was dervied. Your job is to provide an answer for the subquestion considering the context of the original question.

## Original Question
{question}

## Subquestion
{subquestion}
"""
    return prompt

def answer_question(question: str) -> str:
    return f"""You are an expert at answering questions.

## Question
{question}
"""

def restate_question_given_answers(question: str, independent_answers: List[str], dependent_questions: List[str]) -> str:
    independent_answers = "\n\n".join(independent_answers)
    dependent_questions = "\n".join([
        f"* **Subquestion**: {question}"
        for question in dependent_questions
    ])
    prompt = f"""You are simplifying a complex question by integrating answers to some of its independent subquestions while ensuring the remaining unresolved dependent subquestions are still addressed in the reformulated question.

Your task is to reformulate the original question into a new question that:
1. Incorporates the answers to the independent subquestions as known facts or conditions.
2. Continues to require answers to the dependent subquestions to fully resolve the question.

The reformulated question you provide should be in plain text with no special formatting. I want to work with your response and it is easier for me if reformulated question is provided in plain text.

Ensure the new reformulated question is clear, coherent, and logically flows from the provided answers while keeping the remaining dependencies intact.

## Example
### Original Question
What is the population of the capital of France?

### Independent Subquestions
* **Subquestion**: What is the capital of France?
* **Answer**: Paris

### Dependent Subquestions
* **Subquestion**: What is the population of the capital?
  
### Reformulated Question
What is the population of Paris?

## Assistant
### Original Question
{question}

### Independent Subquestions
{independent_answers}

### Dependent Subquestions
{dependent_questions}

### Reformulated Question
"""
    return prompt

def evaluate_solution(problem: str, solution: str) -> str:
    prompt = f"""You are an expert and looking at a problem and solution and deciding if the solution is a good answer.

**Ensure you respond only with "Yes" or "No" since this answer will be parsed from your response.**

## Problem
{problem}

## Solution
{solution}

## Evalutation
Is this solution valid, logical, and clear for the given problem? Respond simply with "Yes" or "No".
"""
    return prompt

# ReAct

def combine_observations(observations: List[Observation]) -> str:
    if len(observations) == 0:
        return "None"

    return "\n".join([o.markup() for o in observations])

def next_action(question: str, observations: List[Observation]) -> str:
    observations = combine_observations(observations)
    prompt = f"""You are an AI assistant that solves problems by reasoning and taking actions.

You will be provided a question, thoughts, actions, and observations.

Your job is to either answer the question using previous observations or create a new thought and action that will lead to an answer. Sometimes you will have enough information from previous observations, and other times you will not. In the situations where you do have enough information you can simply provide the answer to the question. For the situations where you need more information you will provide a new `Thought` and what `Action` to take to answer that thought. The user will then take that action and provide you, the assistant, with the outcome or `Observation` from that action. This enables a back-n-forth conversation that should allow you, the assistant, and the user to provide a great answer!

If you do provide an answer, ensure to format it as `ANSWER: <answer>` since this information will be extracted later.
If are **not** providing an answer, you should create only **one** new `Thought` and `Action`. Always return both `Thought` and `Action`, not just the action.

## Example 1
### Question
What is 5 + 3 + 11?

### Observations
* **Thought**: I should add 5 and 3.
* **Action**: Add 5 and 3.
* **Observation**: 
```
5 + 3 = 8
```
* **Thought**: I should now add 8 and 11.
* **Action**: Add 8 and 11.
* **Observation**: 
```
8 + 11 = 19
```

### Assistant
ANSWER: The answer for 5 + 3 + 11 is 19.

## Example 2
### Question
What is the current weather in Chicago?

### Observations
* **Thought**: I assume this is the city of Chicago in Illinois. If I had a zip code for Chicago, I could more easily lookup the weather.
* **Action**: Find the zip code for Chicago, IL.
* **Observation**: 
```
The zip code for Chicago, IL is 60601.
```

### Assistant
* **Thought**: Now that I have the zip code, I can now lookup the weather.
* **Action**: Lookup the weather for the zip code 60601.

## Assistant
### Question
{question}

### Observations
{observations}

### Assistant
"""
    return prompt

def take_action(observations: List[str], observation: Observation) -> str:
    if observations:
        observations = combine_observations(observations)
    else:
        observations = ""

    return f"""You are an AI assistant that performs an action and provides an observation. The observation is the outcome of taking the action.

Only return the `Observation`. Do **NOT** suggest any new actions.

{observations}
{observation.markup()}
"""

# PLANNER

def question_concepts(question: str) -> str:
    return f"""
# Deep Conceptual Analysis for Research Questions

Analyze the following research question by identifying its underlying conceptual frameworks, mechanisms, and relationships. Your goal is to extract the deeper scientific or theoretical elements that would be essential for a comprehensive investigation.

Instead of restating obvious components of the question, focus on:

1. Core biological/chemical/physical mechanisms that underlie the phenomenon
2. Key variables and their interactions (both explicit and implicit)
3. Theoretical frameworks relevant to the question
4. Methodological considerations that would be crucial
5. Contextual factors that might influence findings

For each concept:
- Explain why it's fundamental to addressing the question (not just "because it's mentioned")
- Describe specific aspects that would need investigation
- Connect it to broader scientific principles or theories

## Example
### Research Question
How does the replacement of human labor with technology, particularly in manufacturing, retail, transportation and logistics, healthcare, customer service and support, finance, hospitality, and other sectors most affected by automation, impact employment rates, income distribution, social inequality, and the skills and education needs of the workforce?

### Deep Conceptual Analysis
* **Creative destruction process**: The economic mechanism through which technological innovation simultaneously eliminates existing jobs while creating new ones. Investigation would need to examine historical patterns and ratios of job creation-to-destruction across various technological transitions, and how the AI/automation wave might differ from previous industrial revolutions.

* **Productivity-compensation decoupling**: The growing gap between productivity gains from technology and corresponding wage growth. This phenomenon challenges traditional economic theories assuming productivity gains naturally translate to higher wages, suggesting investigation into how automation-driven productivity affects different wage tiers.

* **Task-based labor market framework**: This theoretical model distinguishes between routine and non-routine tasks, explaining why certain roles are more automation-susceptible than others. Analysis would need to examine specific task compositions across sectors and how emerging technologies shift the boundaries of what's considered routine.

* **Network effects in labor displacement**: How automation in interconnected industries creates cascade effects that amplify beyond direct replacement. Research would need to map complex interdependencies between sectors and model second/third-order employment impacts.

* **Skill polarization dynamics**: The tendency of automation to hollow out middle-skill jobs while preserving high and low-skill work. Investigation would measure distribution changes across skill categories and analyze whether this creates "missing rungs" in career advancement ladders.

## Your Task
Provide a deep conceptual analysis for the following research question:

{question}
"""

def rephrase_concept(subject: str, concept: str) -> str:
    return f"""
# Formulating Precise Research Questions from Concepts

Transform the provided concept into a focused, actionable research question that captures its full scope and complexity. Your question should encompass all key variables, relationships, and investigative aspects described in the concept.

The research question should:
1. Be concise (ideally 20-30 words) but comprehensive
2. Include specific variables or factors mentioned in the concept
3. Reflect the precise mechanism or relationship being investigated
4. Be suitable for empirical investigation or systematic review
5. Avoid vague terms in favor of specific, measurable elements

The question should be presented in plain text with no special formatting to facilitate further use.

## Guidelines by Concept Type:
- For **mechanisms/processes**: Frame questions that address "how" the process works, specifying inputs and outputs
- For **relationships**: Specify the exact nature of the relationship (correlation, impact, mediation) and include all relevant variables
- For **contextual factors**: Include both the primary factor and its moderating conditions
- For **methodological considerations**: Frame as comparative questions that contrast approaches or conditions

## Example
### Subject
Automation and Employment

### Concept
**Task-based labor market framework**: This theoretical model distinguishes between routine and non-routine tasks, explaining why certain roles are more automation-susceptible than others. Analysis would need to examine specific task compositions across sectors and how emerging technologies shift the boundaries of what's considered routine.

### Generated Research Question
How does the cognitive-manual and routine-nonroutine task composition of occupations predict their vulnerability to automation across different industry sectors?

## Your Task
### Subject
{subject}

### Concept
{concept}

### Research Question
"""

def brainstorm_approaches(question: str) -> str:
    return f"""
# Research Approach Brainstorming for LLM Implementation

You are tasked with identifying high-level approaches to answer a research question using only capabilities available to large language models. Your task is to think strategically about various ways to tackle the question, focusing on strategies that can be implemented through text analysis, knowledge synthesis, and reasoning.

Consider approaches that leverage:
- Existing knowledge within your training data
- Logical reasoning and inference
- Conceptual frameworks and models
- Comparative analysis of existing information
- Thought experiments and hypothetical scenarios

For each approach, provide your response in this format:
* **APPROACH:** [Name of the approach]
  * **DEFINITION:** [Brief description of what the approach entails (1-2 sentences)]
  * **EXPLANATION:** [Why this approach is valuable for researching this question (2-3 sentences)]
  * **IMPLEMENTATION:** [How you would execute this approach as an LLM]
  * **LIMITATIONS:** [Challenges you might face with this approach]

Consider these LLM-appropriate research approaches (though you may suggest others):
1. **Knowledge Synthesis**: Integrating information from various domains to form comprehensive perspectives
2. **Concept Mapping**: Identifying and organizing key concepts and their relationships
3. **Analogical Reasoning**: Drawing comparisons to similar domains or problems
4. **Theoretical Analysis**: Applying established theoretical frameworks to understand the question
5. **Multi-perspective Analysis**: Examining the question from different disciplinary or philosophical viewpoints
6. **Historical Pattern Recognition**: Identifying relevant historical precedents or trends

Generate 4-6 approaches that would be most relevant to the research question.

## Research Question
{question}

## Approaches
"""

def pick_top_strategies(question: str, ideas: str) -> str:
    return f"""
# Evaluate and Select Optimal Research Approaches

## Research Approaches
{ideas}

## Instructions
Based on the research approaches you've generated, identify the 2-3 most effective approaches for answering this research question. Present them in order of priority (most important first).

Format your response as follows:

## Most Effective Approaches (In Priority Order)

* **APPROACH 1:** [Name of highest priority approach]
  * **DEFINITION:** [Brief description of what this approach entails (1-2 sentences)]
  * **RATIONALE:** [Why this approach is particularly effective for this question]
  * **INTEGRATION:** [How this approach would complement or build upon other selected approaches]

* **APPROACH 2:** [Name of second priority approach]
  * **DEFINITION:** [Brief description of what this approach entails (1-2 sentences)]
  * **RATIONALE:** [Why this approach is particularly effective for this question]
  * **INTEGRATION:** [How this approach would complement or build upon other selected approaches]

* **APPROACH 3:** [Name of third priority approach] (if applicable)
  * **DEFINITION:** [Brief description of what this approach entails (1-2 sentences)]
  * **RATIONALE:** [Why this approach is particularly effective for this question]
  * **INTEGRATION:** [How this approach would complement or build upon other selected approaches]

## Research Question
{question}
"""

def concept_title(concept: str) -> str:
    return f"""
# Creating Research Paper Section Headings

Convert the provided research question into a concise, clear heading suitable for a section within a research paper or article. Your heading should capture the essential focus while being appropriately brief for a section title.

## Guidelines for Effective Section Headings:
1. Be concise (typically 3-7 words)
2. Focus on the core concept or relationship
3. Use clear, direct phrasing without unnecessary articles or conjunctions
4. Maintain scholarly tone while being more concise than paper titles
5. Use parallel structure for consistency with other headings
6. Consider standard section heading formats in academic papers (e.g., "Zinc Absorption Mechanisms" rather than "The Effects of Zinc on Absorption Mechanisms")
7. Create a heading you would likely see within a research paper or article

## Examples:

### Research Question:
How does the cognitive-manual and routine-nonroutine task composition of occupations predict their vulnerability to automation across different industry sectors?

### Section Heading:
Task Composition and Automation Vulnerability

### Research Question: 
To what extent does early childhood nutrition affect cognitive development and academic performance in elementary school children from different socioeconomic backgrounds?

### Section Heading:
Nutritional Impacts Across Socioeconomic Groups

## Your Task:

### Research Question:
{concept}

### Section Heading:
"""

def decompose_question_components(question: str) -> str:
    return f"""To fully address the research question, identify the key subquestions or components that need to be explored. Consider different angles, perspectives, or themes that might be relevant. Aim to break the question into 3-5 distinct parts that, when answered, will provide a comprehensive response.

## Example
### Question
How can renewable energy adoption be increased in urban areas?

### Subquestions
1. What are the current barriers to renewable energy adoption in cities?
2. How do economic factors influence urban renewable energy use?
3. What role does government policy play in encouraging adoption?
4. How can technology make renewable energy more accessible in urban settings?
5. What social or cultural attitudes affect public acceptance of renewables?

## Assistant
### Question
{question}

### Subquestions
"""

def question_topics(question: str) -> str:
    """Finds the key topics that should be defined in order to understand the question."""
    return f"""
You are an expert at analyzing research questions and identifying the fundamental topics that must be understood before attempting to answer them.

When presented with a research question, extract 1-5 core scientific concepts that:
- Form the conceptual foundation of the question
- Would make answering impossible if misunderstood
- Require clear definition before meaningful research can begin

Always include the primary subject of the research as a foundational topic.

IMPORTANT: Do NOT simply restate parts of the question as topics. For example, for a question about "medical benefits of zinc," you should NOT list "medical benefits" as a separate topic since it's merely restating part of the question.

Instead, identify underlying scientific disciplines, mechanisms, or frameworks needed to understand the question. Focus on knowledge domains rather than descriptive phrases from the question.

For each identified concept:
- Explain why it's foundational to the question
- Note what specific aspects of this concept are most relevant to the question

Format your response exactly as follows:

* **TOPIC 1**: [Name of first key concept]
RELEVANCE: [Why this concept is foundational to the question]

* **TOPIC 2**: [Name of second key concept]
RELEVANCE: [Why this concept is foundational to the question]

Your goal is not to create a research plan but to identify the conceptual prerequisites that anyone would need to grasp before attempting to answer this specific question.

## Research Question
{question}

## Foundational Topics
"""

# RESEARCHER
# Provide the names in the format "Lastname, FirstInitial. MiddleInitial."
def article_citation(url: str, meta_tags: List[str], content: str) -> str:
    meta_tags_combined = "\n".join([f"* {tag}" for tag in meta_tags]) 
    return f"""You are an expert at reading the text (extracted from HTML) from an online article and extracting information.

# Context
## URL:
{url}

## Meta Tags:
{meta_tags_combined}

## Content:
{content}
</article>

# Instructions
Please return the information in the format requested so that it is easy to extract the information.

Please provide the published date in the format "YYYY-MM-DD". If only year and month is found, just include the year (ignore month).

Please a semi-colon to separate authors if there are more than one.
If the resource was written by a group or organization, use the name of the group/organization as the author.

If you cannot find author information or published date use the value "None".

**PLEASE RESPOND IN THE EXACT FORMAT REQUESTED!**

Create a response in the following format:
* AUTHORS: <authors>
* PUBLISHED_DATE: <published_date>

Example Response:
* AUTHORS: Deanna Debara
* PUBLISHED_DATE: 2022-06-22

# Assistant
"""

def valid_authors(authors: List[str]) -> str:
    names = [f"* NAME: {name}" for name in authors]
    names = "\n".join(names)
    return f"""Which of the following values look like a human name?

Please return each name with the syntax: `NAME: <name>`

# Possible Human Names
{names}

# Valid Human Names
"""

def key_topic_overview(key_topic: str) -> str:
    return f"""Provide a high-level overview of the following topic:

"{key_topic}"

Please format the response in a way that is concise, clear, and easily readable. Include only the important information.
"""

def key_concept_overview(key_concept: str, strategy: str) -> str:
    return f"""You are an expert at answering research questions using the requested strategy.

Special Instructions:
Please do not include any unnecessary introductions or endings.

Research question:
"{key_concept}"

Research Strategy:
"{strategy}"
"""

def consolidate_concept_overviews(key_concept: str, answers: List[str]) -> str:
    answers_combined = [
        f"## Candidate {i+1}\n\n```markdown\n\n{answer}\n```" 
        for i, answer in enumerate(answers)
    ]
    answers_combined = '\n\n'.join(answers_combined)

    return f"""Please evaluate the following candidate responses to the question and create a comprehensive answer that combines the best points from each while eliminating redundancies:

# Question
"{key_concept}" 

# Candidates
{answers_combined}

# Instructions
Based on the candidate responses above, please create a single cohesive answer that:
1. Combines unique insights from all responses
2. Organizes the answer in a way that makes the content clear
3. Uses markdown formatting for readability

Please do not include any unnecessary introductions or endings.
"""