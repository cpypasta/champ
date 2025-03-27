import pickle, prompts, re
from strategies.planner import ResearchPlan, ResearchConcept
from tools.perplexity import PerplexityTool
from llm_caller import LLMCaller
from dataclasses import dataclass, field
from typing import List
from rich import print as rprint
from rich.markdown import Markdown
from rich.progress import Progress, TextColumn, BarColumn, ProgressColumn, Text, TimeElapsedColumn
from tools.article import ArticleCitation
from time import time
from datetime import timedelta

@dataclass
class TopicOverview:
    topic: str
    overview: str = None

@dataclass
class ResearchReport:
    plan: ResearchPlan
    topics: List[TopicOverview] = field(default_factory=list)
    citations: List[ArticleCitation] = field(default_factory=list)

    def markdown(self) -> str:
        combined_topics = "\n\n".join([
            f"### {topic.topic.upper()}\n{topic.overview}"
            for topic in self.topics
        ])
        self.citations = list({citation.url: citation for citation in self.citations}.values())
        references = [citation.reference() for citation in self.citations]
        references.sort()
        combined_references = "\n\n".join(references)
        
        return f"""
# {self.plan.subject}

**Research Question**: {self.plan.question}

## Key Topics
{combined_topics}

## References
{combined_references}
"""

class Researcher:
    def __init__(self, fast_llm: LLMCaller):
        self.fast_llm = fast_llm
        self.internet = PerplexityTool(fast_llm)

    def research(self, plan: ResearchPlan) -> ResearchReport:
        class PercentColumn(ProgressColumn):
            def render(self, task):
                if task.total:
                    completed = int(task.completed)
                    total = int(task.total)
                    percent = task.percentage
                    return Text(f"{completed}/{total} {percent:.0f}%", style="progress.percentage")
                else:
                    return Text("")
                
        class SmartBarColumn(BarColumn):
            def render(self, task):
                if task.total is None and (isinstance(task.completed, bool) and task.completed):
                    return Text("")
                return super().render(task)           

        def create_progress() -> Progress:
            return Progress(
            TextColumn("{task.description}"),
            TimeElapsedColumn(),         
            SmartBarColumn(bar_width=None),
            PercentColumn(),
            expand=False
        )

        def format_duration(delta: timedelta) -> str:
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}:{minutes:02d}:{seconds:02d}"        

        rprint("[dim]Research Started")
        rprint(f"[dim]Research Question: {plan.question}")
        start_time = time()
        key_topics = plan.key_topics
        
        report = ResearchReport(
            plan            
        )

        with create_progress() as progress:
            task = progress.add_task("Researching key topics", total=len(key_topics))
            topic_overviews = []
            for topic in key_topics:
                topic = re.sub(r"\:.*", "", topic).replace("**", "")
                search_query = prompts.key_topic_overview(topic)
                topic_overview = self.internet.search(search_query)
                if topic_overview:
                    topic_overview_content = topic_overview["content"]
                    topic_overview_content = topic_overview_content.replace("##", "####").replace("#######", "######")
                    topic_overviews.append(TopicOverview(topic, topic_overview_content))                
                    report.citations.extend(topic_overview["citations"])
                progress.update(task, advance=1)

            report.topics = topic_overviews

        stop_time = time()
        duration = format_duration(timedelta(seconds=stop_time - start_time))
        rprint(f"[dim]Research Complete {duration}")

        return report


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    with open("plan.pkl", "rb") as f:
        plan: ResearchPlan = pickle.load(f)    
        
    llm = LLMCaller(provider="gemini")
    solver = Researcher(llm)
    report = solver.research(plan)

    with open("report.md", "w") as f:
        f.write(report.markdown())