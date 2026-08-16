from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from tool.scrap_tool import fetch_paper
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from rich import print
import os
load_dotenv()

writer_agent = ChatMistralAI(model = "mistral-large-latest", temperature = 0.7)
notes_agent = ChatMistralAI(model="codestral-latest")

class State(TypedDict):
    topic:str
    papers:list[dict]
    paper_chunks:list[dict]
    research_notes: list[dict]
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
    """),
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
    """),
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
STARTER_MANUSCRIPT_PROMPT = ChatPromptTemplate([
    ("system", """
        You are an academic research writing assistant.
        Your task is to create a STARTER RESEARCH MANUSCRIPT for the user.
        This is NOT intended to be presented as a finished research paper.
        It should serve as a structured, research-backed boilerplate that the
        user can edit, expand, verify, and complete using their own research.
    """),
    ("human", """
        Research Topic:
        {topic}

        Synthesized Research Context:
        {research_context}

        Reference Information:
        {references}

        ==================================================
        PRIMARY OBJECTIVE
        ==================================================

        Create a useful starting manuscript that:

        - establishes the research background
        - synthesizes existing literature
        - identifies potential research gaps
        - suggests possible research questions and objectives
        - gives the user a strong paper structure
        - clearly indicates where their own experimental or analytical work is required

        ==================================================
        SOURCE RULES
        ==================================================

        Use ONLY information supplied in the Research Context.

        Never invent:

        - papers
        - authors
        - citations
        - URLs
        - DOIs
        - numerical results
        - experiments
        - datasets
        - methodology
        - sample sizes
        - findings

        If the user's own research information is required, insert a placeholder.

        Use labels such as:

        [USER INPUT REQUIRED]

        [SUGGESTED — EDIT AS NEEDED]

        [ADD YOUR RESULTS HERE]

        [ADD EXPERIMENTAL DETAILS]

        [VERIFY AGAINST ORIGINAL SOURCE]

        ==================================================
        OUTPUT
        ==================================================

        # Proposed Title

        Provide one recommended academic title.

        Also provide 2 alternative titles.

        ---

        # Abstract Template

        Provide a starter abstract containing:

        Background:
        Write 2-3 sentences supported by the literature.

        Problem:
        Describe the research problem.

        Objective:
        [SUGGESTED — EDIT ACCORDING TO YOUR STUDY]

        Methodology:
        [USER INPUT REQUIRED: Describe your methodology.]

        Results:
        [USER INPUT REQUIRED: Add your results.]

        Conclusion:
        [USER INPUT REQUIRED: Add conclusions based on your actual findings.]

        ---

        # 1. Introduction

        Write a strong starter introduction.

        Structure it from:

        Broad research area
                ↓
        Existing knowledge
                ↓
        Important findings from literature
                ↓
        Unresolved issue / research gap
                ↓
        Potential purpose of the present study

        Do not claim that the user has conducted work that has not been supplied.

        End with:

        "The present study therefore aims to [USER INPUT REQUIRED]."

        ---

        # 2. Literature Review

        Organize the literature THEMATICALLY.

        Create meaningful subsections such as:

        ## 2.1 [Theme]

        ## 2.2 [Theme]

        ## 2.3 [Theme]

        For each theme:

        - synthesize multiple sources
        - explain major findings
        - describe agreements
        - describe disagreements when relevant
        - connect the literature to the research topic

        Avoid paper-by-paper summaries.

        ---

        # 3. Research Gap

        Present:

        ## Supported Gaps

        Only gaps reasonably supported by the supplied literature.

        ## Possible Research Opportunities

        Present inferred directions separately.

        Never present an inference as an established research gap.

        ---

        # 4. Suggested Research Problem

        Create a suggested research problem statement connecting:

        Existing knowledge
        → limitation/gap
        → why further research may be needed

        Label it:

        [SUGGESTED — EDIT ACCORDING TO YOUR ACTUAL STUDY]

        ---

        # 5. Suggested Research Objectives

        ## Main Objective

        Provide one suggested main objective.

        ## Specific Objectives

        Provide approximately 3-5 possible specific objectives.

        Clearly label all objectives as suggestions.

        ---

        # 6. Suggested Research Questions

        Provide relevant research questions derived from the literature.

        RQ1:
        RQ2:
        RQ3:

        ---

        # 7. Hypotheses

        Only suggest hypotheses if appropriate for the type of research.

        Otherwise state that hypotheses may not be necessary.

        ---

        # 8. Methodology Template

        Do NOT fabricate a methodology.

        Create editable subsections:

        ## 8.1 Research Design

        [USER INPUT REQUIRED]

        ## 8.2 Study Population / Dataset / Materials

        [USER INPUT REQUIRED]

        ## 8.3 Variables

        [USER INPUT REQUIRED]

        ## 8.4 Data Collection

        [USER INPUT REQUIRED]

        ## 8.5 Experimental Procedure

        [USER INPUT REQUIRED]

        ## 8.6 Data Analysis

        [USER INPUT REQUIRED]

        You may mention methodologies used by existing studies as possible
        approaches, but clearly label them as methodological inspiration.

        ---

        # 9. Results Template

        Never create results.

        Provide placeholders for:

        ## 9.1 Main Results

        [ADD YOUR RESULTS]

        ## 9.2 Tables / Figures

        [ADD APPROPRIATE TABLES OR FIGURES]

        ## 9.3 Statistical / Analytical Findings

        [ADD YOUR ANALYSIS]

        ---

        # 10. Discussion Template

        Provide a framework that the user can complete after obtaining results.

        Include prompts for:

        - interpretation of findings
        - comparison with previous studies
        - similarities with previous research
        - contradictory findings
        - possible explanations
        - theoretical implications
        - practical implications

        Use placeholders where user results are required.

        ---

        # 11. Limitations

        Include:

        Known limitations from existing literature, where relevant.

        Then:

        [USER INPUT REQUIRED: Describe limitations of your own study.]

        ---

        # 12. Future Research

        Suggest future research directions based on the synthesized literature.

        Clearly label inferred directions as suggestions.

        ---

        # 13. Conclusion Template

        Write only the literature-supported portion of the conclusion.

        Leave placeholders for:

        [INSERT MAIN STUDY FINDINGS]

        [INSERT IMPLICATIONS]

        [INSERT FINAL CONCLUSION]

        ---

        # 14. References Used

        List ONLY references provided in the research context.

        Include available:

        - Authors
        - Title
        - Year
        - DOI
        - URL

        Never create missing information.

        ==================================================
        WRITING STYLE
        ==================================================

        Use:

        - professional academic English
        - clear scientific language
        - coherent paragraphs
        - thematic synthesis
        - concise writing

        Avoid:

        - unnecessary verbosity
        - fake citations
        - unsupported statements
        - repeated summaries
        - pretending the manuscript is complete

        The manuscript should give the researcher a strong starting point while
        making it obvious what they must complete themselves.
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
        paper['publisher_url'] = scrape['publisher_url']
        scraped_papers.append(paper)
    
    return {"scraped_papers":scraped_papers}


def makeChunks(state:State):
    scraped_papers = state['scraped_papers']
    papers = state['papers']
    topic = state['topic']
    paper_chunks = []
    # print(state)
    for paper in scraped_papers:
        if paper['local_path']:
            path = paper['local_path'].replace('\\', "/")          
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
        else:
            # https://doi.org/10.14801/jkiit.2024.22.11.167)
            abstract = paper['abstract']
            paper_chunks.append({
                "title":paper['title'],
                "authors":paper['authors'],
                "url":paper['url'],
                "year":paper['year'],
                "doi":paper['doi'], 
                "chunks":[abstract]})

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
            chunk_prompt = chunk_analyzer_prompt.invoke({"topic":topic, "paper_title":title, "chunk":chunk})
            response = notes_agent.invoke(chunk_prompt)
            chunk_notes.append(response.content)
        
        summarized_paper_chunks.append({
            "title":title, 
            "doi":paper['doi'],
            "summarized_chunks":chunk_notes, 
            "year":paper['year'],  
            "authors":paper['authors'],
            "url":paper['url']
            })
    
    for paper in summarized_paper_chunks:
        synthesis_prompt = PAPER_SYNTHESIS_PROMPT.invoke({
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
    
    print("research_notes", research_notes)
    return {"research_notes":research_notes}

def makeStaterTempelate(state:State):
    print(f"State In MakeStaterTemplate {list(state.keys())}")
    research_context = state['research_notes']
    topic = state['topic']
    references = state['papers']

    stater_template_prompt = STARTER_MANUSCRIPT_PROMPT.invoke({
        "topic":topic,
        "research_context":research_context,
        "references":references
    })

    response = notes_agent.invoke(stater_template_prompt)

    return {"starter_manuscript":response.content}



graph = StateGraph(State)

graph.add_node("scrapePapers", scrapePapers)
graph.add_node("makeChunks", makeChunks)
graph.add_node("makeNotes", makeNotes)
graph.add_node("makeStaterTempelate",makeStaterTempelate)

graph.add_edge(START, "scrapePapers")
graph.add_edge("scrapePapers", "makeChunks")
graph.add_edge("makeChunks", "makeNotes")
graph.add_edge("makeNotes", "makeStaterTempelate")
graph.add_edge("makeStaterTempelate", END)


writerApp = graph.compile()









