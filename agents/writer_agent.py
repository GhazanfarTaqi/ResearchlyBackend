from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages
from tool.scrap_tool import scrapeURL
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

writer_agent = ChatMistralAI(model = "mistral-large-latest", temperature = 0.7)

class State(TypedDict):
    topic:str
    papers:list[dict]
    research_notes = list[dict]
    scraped_papers: list[dict]
    starter_manuscript: str


paper_analyzer_prompt = """
    You are an academic research analysis agent.

    You will receive the content of ONE research paper.

    Your task is to extract and compress the information that would be useful
    for another AI agent writing a research-paper starter manuscript.

    Research topic:

    {topic}

    Paper:

    {paper}

    Extract ONLY information supported by the supplied paper.

    Return the following structure:

    Title:
    Authors:
    Publication Year:
    URL / DOI:

    Research Problem:
    Briefly describe the problem investigated by the paper.

    Research Objective:
    State the objective of the study.

    Methodology:
    Summarize the methodology, including:
    - research design
    - dataset/sample/material
    - important variables
    - experimental approach
    - analysis methods

    Only include details explicitly available in the paper.

    Key Findings:
    Provide 3-6 important findings.

    Important Evidence:
    Extract useful numerical or factual observations when available.

    Limitations:
    List limitations mentioned by the authors.
    If none are provided, write "Not identified from provided content."

    Research Gap:
    Identify gaps explicitly discussed or reasonably evident from the paper.
    Clearly mark inferred gaps as "Possible inferred gap."

    Relevance to User Topic:
    Explain how this paper helps answer or frame:

    {topic}

    Potential Citation Use:
    Explain where this paper may be useful:
    - Introduction
    - Literature Review
    - Methodology
    - Discussion
    - Research Gap

    Rules:

    - Do not invent information.
    - Do not invent statistics.
    - Do not invent methodology.
    - Do not invent authors.
    - Do not invent citations.
    - Do not claim anything not supported by the provided paper.
    - Keep the analysis concise.
    """

def scrapePapers(state:State):
    papers = state['papers']



