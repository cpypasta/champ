import prompts, re
from llm_caller import LLMCaller
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint
from strategies.atom_of_thought import AtomOfThought
from typing import List
from dataclasses import dataclass, field
from rich.progress import Progress, TextColumn, BarColumn, ProgressColumn, Text
from time import sleep

@dataclass
class ResearchConcept:
    subject: str
    concept: str
    question: str = None
    ideas: List[str] = field(default_factory=list)
    title: str = None

    def _extract_ideas(self, markdown: str) -> List[str]:
        return re.findall(r"IDEA:\s+(.+)", markdown)

    def create_question(self, llm: LLMCaller) -> "ResearchConcept":
        question = llm.generate(prompts.rephrase_concept(self.subject, self.concept))        
        self.question = question
        title = llm.generate(prompts.concept_title(self.concept))
        self.title = title
        return self
    
    def create_ideas(self, llm: LLMCaller) -> "ResearchConcept":
        brainstorm = llm.generate(prompts.brainstorm_approaches(self.question))
        top_ideas = llm.generate(prompts.pick_top_ideas(self.question, brainstorm))
        self.ideas = self._extract_ideas(top_ideas)
        return self
    
    def markdown(self) -> str:
        ideas = [
            f"  * {idea}"
            for idea in self.ideas
        ]
        ideas = "\n".join(ideas)

        return f"""### {self.title}        
* **Question**: {self.question}
* **Answer Strategies**: 
{ideas}
"""


class ResearchPlanner:
    def __init__(self, llm_caller: LLMCaller):
        self.llm = llm_caller
        self.atom = AtomOfThought(llm_caller, debug=False)

    def _extract_concepts(self, markdown: str) -> List[ResearchConcept]:
        concepts = []
        for line in markdown.splitlines():
            line = line.strip()
            if line:
                index = line.find(". ")
                if index != -1:
                    concept = line[index + 2:]
                    concepts.append(ResearchConcept(self.subject, concept))
        return concepts

    def _debug_concepts(self, concepts: List[ResearchConcept]):
        for concept in concepts:
            rprint(Panel(Markdown(concept.markdown()), title=concept.title, title_align="left"))

    def _extract_key_topics(self, markdown: str) -> List[str]:
        return re.findall(r"\*\s+(.+)", markdown)

    def plan(self, question: str) -> str:
        class PercentColumn(ProgressColumn):
            def render(self, task):
                if task.total:
                    completed = int(task.completed)
                    total = int(task.total)
                    percent = task.percentage
                    return Text(f"{completed}/{total} {percent:.0f}%", style="progress.percentage")
                else:
                    return Text("")

        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            PercentColumn(),
            expand=True
        )

        with progress:            
            rprint("Question", f"[blue bold]{question}")
            task = progress.add_task("", total=None)
            progress.update(task, description="Analyzing question", total=None)
            question_atom = self.atom.solve_problem(question, terminate_on_answer=False)["question"]
            # question_atom = question

            progress.update(task, description="Extracting key topics", total=None)
            key_topics_prompt = prompts.question_topics(question_atom)
            key_topics_response = self.llm.generate(key_topics_prompt)
            self.key_topics = self._extract_key_topics(key_topics_response)            
            
            progress.update(task, description="Extracting subject", total=None)
            self.subject = self.llm.generate(prompts.concept_title(question_atom))

            progress.update(task, description="Extracting concepts", total=None)
            concepts_prompt = prompts.question_concepts(question_atom)
            concepts_response = self.llm.generate(concepts_prompt)
            concepts = self._extract_concepts(concepts_response)
            concepts_size = len(concepts)

            progress.update(task, description="Analyzing concepts", total=concepts_size)
            for concept in concepts:
                concept.create_question(self.llm)
                progress.update(task, advance=1)
            progress.reset(task)

            progress.update(task, description="Brainstorming concepts", total=concepts_size)
            for concept in concepts:
                concept.create_ideas(self.llm)
                progress.update(task, advance=1)
            progress.reset(task)

            progress.remove_task(task)

            combined_topics = "\n".join([f"* {topic}" for topic in self.key_topics])
            combined_concepts = "\n".join([concept.markdown() for concept in concepts])
            outline = f"""# {self.subject}            

**Research Question**: {question}

**Expanded Question**: {question_atom}

## Key Topics
{combined_topics}

## Key Concepts
{combined_concepts}
"""
            rprint(Panel(Markdown(outline), title="Outline", title_align="left"))
            with open("outline.md", "w") as f:
                f.write(outline)


if __name__ == "__main__":
    # question = "Will AI ever replace human software programmers?"
    question = "How do the underlying theories of goal-setting and self-determination support the five factor theory for scrum team effectiveness?"

    llm = LLMCaller()
    planner = ResearchPlanner(llm)
    planner.plan(question)

    # s = "Given the current limitations of AI in understanding complex scenarios, ethical considerations, and creative problem-solving, and anticipating advancements in AI for code generation, automated debugging, and cross-language support, how can software programmers adapt their roles and practices to integrate AI tools into their workflow without being fully replaced, and what potential changes in the job market for software programmers could occur as a result of these AI advancements?"
    # terms = llm.generate(prompts.question_terms(s))
    # rprint(Markdown(terms))
    # print(planner._extract_key_terms(terms))