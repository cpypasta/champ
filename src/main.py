import json
from tqdm import tqdm
from llm_caller import LLMCaller
from question_decomposition import QuestionDecomposer
from answer_consolidation import AnswerConsolidator
from tools.research_tool import Question
from researcher import Researcher, Tool
from dotenv import load_dotenv

load_dotenv()

def process_user_question(user_question: str):
    print(user_question)
    print()

    # Instantiate dependencies
    llm_caller = LLMCaller()
    decomposer = QuestionDecomposer(llm_caller)
    consolidator = AnswerConsolidator(llm_caller)

    # Analyze the question
    analysis = decomposer.analyze(user_question)
    print("Question Analysis:")
    print(json.dumps(analysis, indent=2))
    print()

    # Decompose the question into sub-questions and revise them
    sub_questions_data = decomposer.decompose(user_question, analysis)
    for _ in tqdm(range(2), desc="revising sub-questions"):
        sub_questions_data = decomposer.revise(user_question, analysis, sub_questions_data["questions"])
    sub_questions = [q["question"] for q in sub_questions_data["questions"]]

    # Generate Wikipedia-style titles for each sub-question
    titles = decomposer.get_titles(sub_questions)["titles"]
    titles = [t["title"] for t in titles]

    # Research
    question_titles = zip(sub_questions, titles)
    questions_to_research = [Question(q[0], title=q[1]) for q in question_titles] # TODO: create questions directly from decomposition step
    researcher = Researcher(llm_caller)
    questions_with_context = researcher.research(questions_to_research, [Tool.WIKIPEDIA, Tool.PERPLEXITY])

    # Save questions with context
    with open("../tmp/context.md", "w") as f:
        debug_questions = "---\n".join([str(q) for q in questions_with_context])
        f.write(debug_questions)
        print("Context saved")

    # Answer each sub-question
    sub_question_answers = []
    for question in tqdm(questions_with_context, desc="answering sub-questions"):
        answer = consolidator.answer_sub_question(question.question, question.get_context())
        q_a = {"question": question.question, "answer": answer}
        sub_question_answers.append(q_a)

    # Generate a report of sub-questions and answers
    sub_question_response = consolidator.generate_report(sub_question_answers)

    # Save the report to a markdown file
    with open("../tmp/sub_questions.md", mode="w") as f:
        f.write(sub_question_response)

    # Consolidate the sub-question answers into a final answer
    final_answer = consolidator.consolidate_answers(user_question, sub_question_response)

    # Save the final answer to a markdown file
    with open("../tmp/final_answer.md", "w") as f:
        f.write(final_answer)
    
    return final_answer


if __name__ == "__main__":
    # user_question = "is chain of thought with a LLM (large-language-model) just a matter of prompting an LLM more than once?"
    # user_question = "how can a person use Lakoff's conceptual metaphor theory and probabilistic context-free grammars (PCFGs) to better understand user intent?"
    # user_question = "how do the underlying theories of goal-setting and self-determination support the five factor theory for scrum team effectiveness?"
    user_question = "i have a large 3 stall garage. i need help figuring out a plan on how to clean and organize it. have any tips?"

    process_user_question(user_question)

