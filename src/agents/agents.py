from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()

# Model initialization - using flash-lite for higher quota and lower latency on the free tier
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
)

search_system_prompt = (
    "You are a search agent. Your job is to search the web for relevant, high-quality, "
    "and up-to-date information on the given topic and return comprehensive results."
)


# 1st agent : Searcher Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=search_system_prompt,
        name="search-agent",
    )


# 2nd agent : Reader Agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="You are a reader agent that can read the content of a URL and return the content.",
        name="reader-agent",
    )


# Writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed search report on the topic below.
    topic: {topic}
    research gathered: {research}
    structured the report as 
    - Introduction
    - Key Findings
    - Details
    - Conclusion
    - sources (list all the urls found in research)
    be detailed factual and professional
    """)
])        

writer_chain = writer_prompt | llm | StrOutputParser()


# Critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. be honest and specific"),
    ("human", """review the research report below.
    report: {report}
    respond in the exact format as follow
    - score : x/10
    - strength
    - areas to improve
    - one line verdict
    """)
])

critic_chain = critic_prompt | llm | StrOutputParser()
