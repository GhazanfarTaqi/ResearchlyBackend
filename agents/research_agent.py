from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from tool.research_tool import get_research_data
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


tools = [get_research_data]

researh_agent = ChatMistralAI(model = "mistral-large-latest", temperature = 0.7)


class State():
    topic:str
    messages: Annotated[list,add_messages]
    papers:list[dict]
    report:str


def get_papers_node(state:State):
    topic = state['topic']
    papers = get_research_data.invoke({"query":topic})

    return {"papers":papers}


ResearchPrompt = ChatPromptTemplate.from_messages([
     (
        "system",
        """You are an academic research assistant.
        Synthesize research literature accurately and never invent
        citations, findings, or sources."""
    ),
    (
        "human",
        """
        Research Topic:
        {topic}

        Retrieved Research Papers:
        {research_papers}

        Analyze the supplied paper abstracts and produce a synthesized
        research summary.

        Your response must contain:

        # Research Summary

        ## Key Findings
        Group related findings across papers.

        ## Methods and Approaches
        Describe important methods mentioned in the abstracts.

        ## Areas of Agreement
        Explain where studies reach similar conclusions.

        ## Conflicting Findings
        Explain disagreements if they exist.

        ## Research Gaps
        Identify unanswered questions or limitations.

        ## Conclusion
        Give an overall synthesis of the research.

        ## Research Papers
        List every paper used with:
        - Title
        - Authors
        - Year
        - Original URL

        Rules:
        - Use only the information provided above.
        - Never fabricate findings or citations.
        - Never fabricate URLs.
        - Preserve URLs exactly.
        - Do not claim to have read full papers if only abstracts were provided.
        - Reference claims using [Paper Title].
        """
    )
])

def research_node(state:State):
    topic = state['topic']
    papers = state['papers']
    prompt = ResearchPrompt.invoke({
        "topic":topic,
        "research_papers":papers
    })
    response = researh_agent.invoke(prompt)

    messages = [prompt.to_messages()[-2], response]

    return {
        "messages":messages,
        "report":response.content
    }



graph = StateGraph(State)
graph.add_node("get_papers", get_papers_node)
graph.add_node("research", research_node)

graph.add_edge(START, "get_papers")
graph.add_edge("get_papers", "research")
graph.add_edge("research", END)

research_pipeline = graph.compile()

response = research_pipeline.invoke({
    "topic":"AI in healthcare"
})

print("RESEARCH REPORT \n")
print(response["report"])