from strategies.planner import ResearchPlanner
from strategies.researcher import Researcher
from llm_caller import LLMCaller
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    question = "How do the underlying theories of goal-setting and self-determination support the five factor theory for scrum team effectiveness?"
    fast_llm = LLMCaller(provider="gemini")
    planner = ResearchPlanner(fast_llm)
    plan = planner.plan(question)
    researcher = Researcher(fast_llm)
    report = researcher.research(plan)
    markdown = report.markdown()
    
    with open("report.md", "w") as f:
        f.write(markdown)