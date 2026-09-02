from langchain.tools import tool
from agents.research_agent import researchApp
from agents.rag_agent import  ask_model






@tool
def rag_search(query: str) -> str:
    """
    Retrieve and answer questions using documents stored in the application's
    vector database.

    Use this tool when the user asks a question that should be answered from
    documents already indexed in the RAG knowledge base. The tool retrieves
    relevant document chunks and passes them through the RAG pipeline to
    generate a grounded response.

    This tool should NOT be used for finding new research papers, searching
    the web, or writing a full research document.

    Args:
        query: The user's question or information request to search for in the
            existing vector database.

    Returns:
        A grounded answer generated from the retrieved document context.
        The response may also contain source information or document references
        if they are provided by the underlying RAG pipeline.
    """
    return ask_model(query)


@tool
def research_topic(topic: str) -> str:
    """
    Research a topic by discovering and analyzing relevant external academic
    or research sources.

    Use this tool when information must be gathered beyond the application's
    existing RAG knowledge base. The research pipeline searches for relevant
    papers or sources, extracts useful information, and produces structured
    research material that can later be used by the writer pipeline.

    This tool is intended for information gathering and evidence collection.
    It should NOT be used to produce the final polished article, report, or
    manuscript.

    Args:
        topic: The research topic, question, or subject that should be
            investigated.

    Returns:
        Research findings related to the requested topic, including summarized
        information from relevant sources and source references or links when
        available from the underlying research pipeline.
    """
    return researchApp(topic)


#Leaving this tool for now will implement a more robust version later. The current implementation is a placeholder and may not fully meet the intended functionality.
@tool
def write_document(instructions: str) -> str:
    """
    Generate a structured written document using the provided instructions and
    research context.

    Use this tool when sufficient information has already been gathered and a
    polished output such as a report, research note, article, section, or draft
    needs to be created. The writer pipeline organizes the available information,
    follows the requested structure and style, and produces the final written
    response.

    This tool should primarily be used after relevant information has been
    retrieved through the RAG or research tools. It should NOT be used as the
    primary tool for discovering new sources.

    Args:
        instructions: Complete writing instructions including the topic,
            available research/context, desired structure, style, constraints,
            and any other requirements needed to generate the document.

    Returns:
        A structured and polished written document generated according to the
        supplied instructions and available research context.
    """
    return write_document(instructions)

