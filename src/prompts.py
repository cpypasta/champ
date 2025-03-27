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

# Planning

def question_concepts(question: str) -> str:
    return f"""Extract the key concepts from the following research question. Break down the question into its fundamental components, such as the subject, the process or action, the affected entities, and the outcomes or impacts. List these concepts and provide a brief explanation of why each is central to understanding and answering the question.

## Example
### Question
How does the replacement of human labor with technology, particularly in manufacturing, retail, transportation and logistics, healthcare, customer service and support, finance, hospitality, and other sectors most affected by automation, impact employment rates, income distribution, social inequality, and the skills and education needs of the workforce?

### Concepts
* **Automation**: This is the core technology driving the changes in labor. It’s central because the entire question revolves around its implementation and effects across various sectors.
* **Replacement of Human Labor**: This is the specific process being examined. Understanding how and why human jobs are being replaced is essential to addressing the question’s focus on technological substitution.
* **Sectors Affected (e.g., manufacturing, retail, transportation)**: These are the key areas where automation is applied. Their inclusion is critical because the question specifies them as the primary domains of impact, and each sector may experience unique effects.
* **Employment Rates**: This is a direct outcome of labor replacement. It’s central because the question seeks to understand how automation influences job availability across the workforce.
* **Income Distribution**: This concept addresses how automation might alter economic equity. It’s vital for exploring whether technological changes concentrate wealth or redistribute it.
* **Social Inequality**: This outcome examines whether automation widens or narrows societal gaps. It’s key to assessing the broader human and ethical implications of the technology.
* **Skills and Education Needs**: This reflects the workforce’s adaptation to automation. It’s essential for understanding how job requirements shift and what training is needed to mitigate negative impacts.

## Assistant
### Question
{question}

### Concepts
"""

def rephrase_concept(subject: str, concept: str) -> str:
    return f"""Rephrase the provided key concept into a research question. The new question should be concise and suitable for brainstorming approaches to explore that concept. The subject of the concept will be provided to ensure the context is clear.

The research question you provide should be in plain text with no special formatting. I want to work with your response and it is easier for me if it just the research question in plain text.

Guidance:
1. If the concept is a person, place, or thing (i.e., a noun), consider asking about its definition, role, or impact.  
   - *Example:* For "AI," ask, "What is AI, and how does it shape modern technology?"
2. If the concept involves a relationship between two or more things, consider phrasing the question in terms of correlation or association.  
   - *Example:* For "AI and Employment," ask, "What is the relationship between AI adoption and employment trends?"
3. If the concept implies one thing causing another, consider phrasing the question in terms of causation or influence.  
   - *Example:* For "AI causing job displacement," ask, "To what extent does AI cause job displacement in traditional industries?"
4. If the concept is an outcome or impact, consider asking how or why it occurs.  
   - *Example:* For "Economic Implications of AI," ask, "How does AI adoption impact economic productivity and inequality?"
5. If the concept is a process or method, consider asking how it works or what its effects are.  
   - *Example:* For "Automation in Healthcare," ask, "How does automation in healthcare affect efficiency and patient outcomes?"
6. If the concept is a theory or model, consider asking how it explains or applies to a specific situation.  
   - *Example:* For "Skill-Biased Technical Change," ask, "How does skill-biased technical change explain workforce skill shifts?"

## Subject
{subject}

## Concept
{concept}

## Research Question
"""

def brainstorm_approaches(question: str) -> str:
    return f"""You are an expert at identifying high-level approaches to answering a research question.

Your task is to think strategically about various ways to tackle the question, focusing on broad strategies, methodologies, and frameworks rather than specific solutions. Consider perspectives from different disciplines, including both conventional and unconventional ideas, and incorporate a mix of qualitative and quantitative methods. Also, reflect on short-term and long-term implications.

Here are some broad approaches to research that you should consider (though you can also create your own approaches):
1. **Systems Thinking**
  * **What it is**: This approach looks at the interconnectedness of components within a system, focusing on relationships, feedback loops, and the bigger picture.
  * **Why it's useful**: It's great for complex questions where multiple factors interact—like climate change or urban planning—because it encourages a holistic view.
2. **Reductionism**
  * **What it is**: This involves breaking down a complex research question into smaller, manageable parts.
  * **Why it's useful**: It simplifies the process by allowing focused investigation of individual pieces before putting them back together.
3. **Interdisciplinary Approaches**
  * **What it is**: This combines methods and insights from different fields to tackle a question from multiple angles.
  * **Why it's useful**: Many modern challenges—like public health or sustainability—benefit from diverse perspectives.
4. **Iterative Refinement**
  * **What it is**: This is about refining a research question or approach through repeated cycles of feedback and adjustment.
  * **Why it's useful**: Research often evolves, and this flexibility allows for continuous improvement.
5. **Comparative Analysis**
  * **What it is**: This examines a question by comparing different cases, scenarios, or examples to find patterns or lessons.
  * **Why it's useful**: It's helpful for understanding what works or fails in different contexts—like comparing policies across cities.
6. **Data-Driven Approaches**
  * **What it is**: This relies on empirical data, statistics, or modeling to guide the research process.
  * **Why it's useful**: It ensures the research is grounded in evidence, which is key for testing ideas or making recommendations.

For each approach, provide:
- **Definition**: A brief description of what the approach entails.
- **Explanation**: Why this approach is valuable for researching and answering the question.

Present your ideas as a list of bullet points in the following format:
* **<approach name>**
  * **Definition**: <definition>
  * **Explanation**: <explanation>

## Example
### Question
How can traffic congestion be reduced in large cities?

### Brainstorm
* Systems Thinking Approach
  * Definition: Analyzing how transportation, urban planning, economic activities, and social behaviors interconnect within the city to create comprehensive strategies that reduce traffic congestion.
  * Explanation: This approach is valuable because it uncovers how different elements contribute to congestion, enabling a holistic understanding that can guide comprehensive research and solutions.
* Data-Driven Approach
  * Definition: Collecting and analyzing extensive data on traffic patterns, commuter behaviors, and infrastructure use to pinpoint effective ways to reduce traffic congestion.
  * Explanation: This approach provides empirical evidence to identify congestion causes and test hypotheses, making it essential for grounding the research in measurable insights.
* Behavioral Economics Approach
  * Definition: Studying how people's transportation choices are influenced by behavior, decision-making, and incentives to design interventions that reduce traffic congestion.
Explanation: Understanding the psychological and economic drivers of congestion can reveal opportunities to influence commuter habits, offering a unique angle for both short-term and long-term research.
  * Explanation: Understanding the psychological and economic drivers of congestion can reveal opportunities to influence commuter habits, offering a unique angle for both short-term and long-term research.
* Policy and Governance Approach
  * Definition: Investigating how government policies, regulations, and urban planning can be shaped to manage and reduce traffic congestion effectively.
  * Explanation: This approach is critical for researching how structural and legal mechanisms can address congestion, providing a lens into scalable, enforceable strategies.
* Technological Innovation Approach
  * Definition: Exploring how new technologies, like smart traffic systems and autonomous vehicles, can be used to develop solutions that reduce traffic congestion.
  * Explanation: This approach allows research into cutting-edge solutions, assessing their feasibility and impact over time, which is key for forward-looking planning.

## Assistant
### Question
{question}

### Brainstorm
"""

def pick_top_ideas(question: str, ideas: str) -> str:
    return f"""You are an expert at analyzing brainstorming ideas about different way to approach answering a research question. Your job is review the ideas and pick the top 5 (if there are enough ideas).

Please return each idea in the format `IDEA: <idea>` so I can easily identify and extract the idea. Please do **NOT** include any explanation for the idea, just the research approach idea itself.

Here is some criteria to consider when making your decision on the top ideas:
1. Pick ideas that are directly relevant to answering the question.
2. Pick ideas that allow you to explore the question from a different angle.
3. Pick ideas that are clear and specific.
4. Pick ideas that a large language model (LLM) like you could answer (e.g., avoid ideas like conducting a new survey or interviews).

## Example
### Question
How can traffic congestion be reduced in large cities?

### Ideas
* Systems Thinking Approach
  * Definition: Analyzing how transportation, urban planning, economic activities, and social behaviors interconnect within the city to create comprehensive strategies that reduce traffic congestion.
  * Explanation: This approach is valuable because it uncovers how different elements contribute to congestion, enabling a holistic understanding that can guide comprehensive research and solutions.
* Data-Driven Approach
  * Definition: Collecting and analyzing extensive data on traffic patterns, commuter behaviors, and infrastructure use to pinpoint effective ways to reduce traffic congestion.
  * Explanation: This approach provides empirical evidence to identify congestion causes and test hypotheses, making it essential for grounding the research in measurable insights.
* Behavioral Economics Approach
  * Definition: Studying how people's transportation choices are influenced by behavior, decision-making, and incentives to design interventions that reduce traffic congestion.
Explanation: Understanding the psychological and economic drivers of congestion can reveal opportunities to influence commuter habits, offering a unique angle for both short-term and long-term research.
  * Explanation: Understanding the psychological and economic drivers of congestion can reveal opportunities to influence commuter habits, offering a unique angle for both short-term and long-term research.
* Policy and Governance Approach
  * Definition: Investigating how government policies, regulations, and urban planning can be shaped to manage and reduce traffic congestion effectively.
  * Explanation: This approach is critical for researching how structural and legal mechanisms can address congestion, providing a lens into scalable, enforceable strategies.
* Technological Innovation Approach
  * Definition: Exploring how new technologies, like smart traffic systems and autonomous vehicles, can be used to develop solutions that reduce traffic congestion.
  * Explanation: This approach allows research into cutting-edge solutions, assessing their feasibility and impact over time, which is key for forward-looking planning.

### Top Ideas
* IDEA: Analyzing how transportation, urban planning, economic activities, and social behaviors interconnect within the city to create comprehensive strategies that reduce traffic congestion.
* IDEA: Collecting and analyzing extensive data on traffic patterns, commuter behaviors, and infrastructure use to pinpoint effective ways to reduce traffic congestion.
* IDEA: Studying how people's transportation choices are influenced by behavior, decision-making, and incentives to design interventions that reduce traffic congestion.
* IDEA: Investigating how government policies, regulations, and urban planning can be shaped to manage and reduce traffic congestion effectively.
* IDEA: Exploring how new technologies, like smart traffic systems and autonomous vehicles, can be used to develop solutions that reduce traffic congestion.

## Assistant
### Question
{question}

### Ideas
{ideas}

### Top Ideas
"""

def concept_title(concept: str) -> str:
    return f"""You are an expert at creating a title for a given concept. This concept will be displayed to the user as a heading, and we want it to be consise and capture the essense of the concept.

Create a title you would likely see in a research paper or article, since that is the context this will be used.

Please return the title with no quotes or any special format. I just want the title to be simple plain text. Do **NOT** put the word "title" in the title.

## Example
### Concept
How does goal setting influence Scrum team effectiveness according to self-determination theory?

### Title
Impact of Goal Setting on Scrum Team Effectiveness

## Assistant
### Concept
{concept}

### Title
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
    return f"""You are an expert at analyzing a question and extracting critical and important key topics that should be defined and understood in order to answer the question.

You should **NOT** pick insubstational topics, but pick topics that are critical and important for the specific question. The purpose of doing this analysis is to prepare a research plan.

## Example
### Question
Given that AI transforms job markets by creating new job types and modifying existing ones while also affecting economic growth and inflation, what new ethical issues arise due to these changes in employment, and what ethical concerns are associated with the social effects of AI, such as changes in social interactions and relationships?

### Key Topics
* Artificial Intelligence (AI)
* Job Market
* Economic Growth
* Inflation
* Ethical Issues
* Social Effects

## Assistant
### Question
{question}

### Key Topics
"""

# SOLVER
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

Please format the response in a way that is concise, clear, and easily readable. Include only the important only.
"""