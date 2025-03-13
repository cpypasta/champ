from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field

@dataclass
class Context:
    source: str
    content: str

    def __str__(self):
        return f"*Source: {self.source}*\n\n{self.content}"

@dataclass
class Question:
    question: str
    title: str = None
    query: str = None
    context: List[Context] = field(default_factory=list)
    answer: str = None

    def add_context(self, context: str):
        new_context = self.context + [context]
        return Question(
            self.question, 
            title=self.title, 
            query=self.query, 
            context=new_context, 
            answer=self.answer
        )
    
    def get_context(self) -> str:
        if self.context and len(self.context) > 0:
            context = '\n\n'.join([str(c) for c in self.context])
            return context
        return ""

    def __str__(self):
        output = f"# Question: {self.question}\n\n"
        if self.context and len(self.context) > 0:
            output += f"## Context\n{self.get_context()}\n\n"
        if self.answer:
            output += f"## Answer\n{self.answer}\n\n"
        return output


class ResearchTool(ABC):
    @abstractmethod
    def research(questions: List[Question]) -> List[Question]:
        pass


if __name__ == "__main__":
    q = Question("boo")
    q = q.add_context("one")
    print(q.context)
    print(q)