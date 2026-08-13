from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages
from tool.scrap_tool import fetch_paper
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
load_dotenv()

writer_agent = ChatMistralAI(model = "mistral-large-latest", temperature = 0.7)
notes_agent = ChatMistralAI(model="codestral-latest")

class State(TypedDict):
    topic:str
    papers:list[dict]
    paper_chunks:list[dict]
    research_notes = list[dict]
    scraped_papers: list[dict]
    starter_manuscript: str


paper_analyzer_prompt = ChatPromptTemplate([
    ('system', """
    You are an academic research analysis agent.

    You will receive the content of ONE research paper.

    Your task is to extract and compress the information that would be useful
    for another AI agent writing a research-paper starter manuscript.
    """
    ),
    (
        'human',
    """

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
    """)
])
chunk_analyzer_prompt = ChatPromptTemplate([
    ("system", """
        You are an academic research extraction assistant.
        You are analyzing ONE CHUNK from a research paper.
    """)
    ("human", """
        You are an academic research extraction assistant.

        You are analyzing ONE CHUNK from a research paper.

        Research Topic:
        {topic}

        Paper Title:
        {paper_title}

        Chunk:
        {chunk}

        Your task is to extract and compress academically useful information
        from this chunk while preserving important evidence.

        Focus ONLY on information explicitly present in the provided chunk.

        Extract the following when available:

        1. Main Ideas
        - What important concepts or arguments are discussed?

        2. Research Problem
        - What problem or question is being investigated?

        3. Methodology
        - Experimental design
        - Dataset / population / samples
        - Materials
        - Variables
        - Models / algorithms
        - Data collection methods
        - Statistical or analytical methods

        4. Key Findings
        - Important findings or observations
        - Relationships between variables
        - Outcomes reported by the researchers

        5. Quantitative Evidence
        - Important numerical values
        - Percentages
        - Sample sizes
        - Performance metrics
        - Statistical results
        - Experimental measurements

        6. Claims / Conclusions
        - Important conclusions made by the authors

        7. Limitations
        - Limitations explicitly mentioned in this chunk

        8. Research Gaps / Future Work
        - Gaps or future research directions explicitly mentioned

        9. Relevance to Research Topic
        Explain briefly how this chunk is relevant to:
        "{topic}"

        Rules:

        - Do NOT invent information.
        - Do NOT use outside knowledge.
        - Do NOT assume information from other sections of the paper.
        - If a category is not discussed, write "Not present in this chunk."
        - Preserve important terminology used by the researchers.
        - Preserve important numbers and factual evidence.
        - Keep the output concise.
        - Do not write a general essay.
    """)
])

PAPER_SYNTHESIS_PROMPT = ChatPromptTemplate([
    ("system", """
        You are an academic research analyst.

        You will receive summaries extracted from multiple chunks belonging to
        ONE research paper.

        Your task is to combine these chunk summaries into one accurate,
        compact Research Note representing the paper.
    """)
    ("human", """

        Research Topic:
        {topic}

        Paper Metadata:
        {paper_metadata}

        Chunk Summaries:
        {chunk_summaries}

        Create a Research Note with the following structure:

        1. Paper Information
        - Title
        - Authors
        - Publication year
        - DOI
        - URL

        Use only metadata that was supplied.

        2. Research Problem
        Explain the main problem investigated by the paper.

        3. Research Objective
        Describe what the researchers attempted to investigate,
        determine, evaluate, compare, or develop.

        4. Background / Context
        Summarize only the background information that is useful for
        understanding the study.

        5. Methodology
        Summarize:
        - Research design
        - Dataset / population / samples
        - Materials
        - Important variables
        - Experimental conditions
        - Models / algorithms
        - Data collection
        - Analysis methods

        6. Key Findings
        Extract approximately 3-7 of the most important findings.

        7. Important Evidence
        Preserve important:
        - numerical results
        - measurements
        - statistics
        - sample sizes
        - performance metrics

        8. Conclusions
        Summarize the conclusions supported by the paper.

        9. Limitations
        Include only limitations supported by the chunk summaries.

        10. Research Gaps / Future Work

        Separate gaps into:

        EXPLICIT GAPS:
        Gaps or future work directly stated by the paper.

        POSSIBLE INFERRED GAPS:
        Only include these when they reasonably follow from the supplied evidence.
        Clearly label them as inferred.

        11. Relevance to User Topic

        Explain how this paper contributes to understanding:

        "{topic}"

        12. Potential Use in Manuscript

        Identify where this source could be useful:

        - Introduction
        - Literature Review
        - Methodology
        - Discussion
        - Research Gap

        Explain briefly why.

        IMPORTANT RULES:

        - Synthesize information rather than concatenating chunk summaries.
        - Remove duplicate information.
        - Resolve repeated findings into a single clear statement.
        - Do NOT invent information missing from the summaries.
        - Do NOT invent citations or bibliographic metadata.
        - Do NOT introduce outside knowledge.
        - Do NOT claim that something occurred unless supported by the supplied summaries.
        - Preserve important quantitative evidence.
        - Keep the Research Note substantially shorter than the original paper.
    """)
])

def scrapePapers(state:State):
    papers = state['papers']
    email = os.getenv("EMAIL")
    output_dir = './paper'
    scraped_papers = []
    for paper in papers:
        scrape = fetch_paper(paper['doi'], output_dir, email)
        paper['local_path'] = scrape["local_path"]
        paper['authors'] = scrape['authors']
        paper['url'] = scrape['pdf_url']
        scraped_papers.append(paper)
    
    return {"scraped_papers":scraped_papers}


def makeChunks(state:State):
    scraped_papers = state['scraped_papers']
    topic = state['topic']
    paper_chunks = []
    for paper in scraped_papers:
        loader = PyPDFLoader(paper['local_path'])
        doc = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(doc)

        # todo:connect vector store pipline here
        paper_chunks.append({
            "title":paper['title'],
            "authors":paper['authors'],
            "url":paper['url'],
            "year":paper['year'],
            "doi":paper['doi'], 
            "chunks":chunks})
    return {"paper_chunks":paper_chunks}
    

def makeNotes(state:State):
    chunks = state['paper_chunks']
    topic = state['topic']
    research_notes = []

    summarized_paper_chunks = []
    for paper in chunks:
        title = paper['title']
        chunks = paper['chunks']
        chunk_notes= []
        for chunk in chunks:
            chunk_prompt = chunk_analyzer_prompt({"paper_title":title, "chunk":chunk})
            response = notes_agent.invoke(chunk_prompt)
            chunk_notes.append(response.content)
        
        summarized_paper_chunks.append({"title":title, "doi":paper['doi'],"summarized_chunks":chunk_notes})
    
    for paper in summarized_paper_chunks:
        synthesis_prompt = PAPER_SYNTHESIS_PROMPT({
            "topic":topic,
            "paper_metadata":{
                "title":paper['title'],
                "doi":paper["doi"],
                "year":paper["year"],
                "authors":paper['authors'],
                "url":paper['url'],
            },
            "chunk_summaries":paper["summarized_chunks"]
        })
        response = notes_agent.invoke(synthesis_prompt)
        research_notes.append({
                "title":paper['title'],
                "doi":paper["doi"],
                "year":paper["year"],
                "authors":paper['authors'],
                "url":paper['url'],
                "notes":response.content
            })
        
    return {"research_notes":research_notes}




def writerNode():
    pass






