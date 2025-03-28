import config.prompts as prompts, re
from dataclasses import dataclass
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint
from tools.llm_caller import LLMCaller
from typing import List, Optional

@dataclass
class Observation:
    thought: str
    action: str
    observation: Optional[str] = None

    def markup(self) -> str:
        obs = f"* **Thought**: {self.thought}\n* **Action**: {self.action}"
        if self.observation:
            obs += f"\n* **Observation**: \n```\n{self.observation}\n```"

        return obs

class React:
    def __init__(self, llm_caller: LLMCaller, max_depth: int = 4):
        self.llm = llm_caller
        self.max_depth = max_depth

    def solve_problem(self, problem: str) -> str:
        """Solve a problem using the ReAct framework.

        This framework follows the `Thought`, `Action`, `Observation` iterative process. The loop stops when an answer is found or the maximum depth is reached. You can think of this as combining chain-of-thought and function calling.

        Args:
            problem (str): The problem to solve.

        Returns:
            str: The answer to the problem.        
        """
        observations = []
        answer = None
        D = 0

        while D < self.max_depth:
            # get next action
            new_action_prompt = prompts.next_action(problem, observations)
            rprint(Panel(Markdown(new_action_prompt), title="Next Action Prompt", title_align="left"))
            action_response = self.llm.generate(new_action_prompt)
            rprint(Panel(Markdown(action_response), title="Next Action", title_align="left"))
            answer_match = re.search(r"ANSWER:\s(.*)", action_response, re.DOTALL)
            
            if answer_match:
                # if we have an answer, then we are done asking for new actions
                answer = answer_match.group(1).strip()
                break

            thought_match = re.search(r"Thought[\*\s]*:\s(.*)", action_response)
            action_match = re.search(r"Action[\*\s]*:\s(.*)", action_response)
            if thought_match and action_match:
                thought = thought_match.group(1).strip()
                action = action_match.group(1).strip()
                obs = Observation(thought, action)

                # take action and get observation
                observation_prompt = prompts.take_action(observations, obs)
                rprint(Panel(Markdown(observation_prompt), title="Action Prompt", title_align="left"))
                observation_response = self.llm.chat(observation_prompt)
                observation_response = observation_response.replace("```", "")
                rprint(Panel(Markdown(observation_response), title="Observation", title_align="left"))
                observation_match = re.search(r"Observation[\*\s]*:[\s`]*(.*)`{0,3}", observation_response, re.DOTALL)
                if observation_match:
                    obs.observation = observation_match.group(1).strip()                    
                else:
                    obs.observation = observation_response

                observations.append(obs)

            
            D += 1

        return answer


if __name__ == "__main__":
    from tools.math import multiply_numbers
    from tools.perplexity import search_internet

    # question = "What is 2 + 2 * 7?"
    question = "What are the best use-cases for microservices? Be sure to consider my team consists mainly of inexperienced developers."
    react = React(LLMCaller(tools=[multiply_numbers, search_internet]))
    rprint(f"[green bold]{question}")
    answer = react.solve_problem(question)
    rprint(f"[green bold]{answer}")