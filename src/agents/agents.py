from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()

# Model initialization
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)


# 1st agent : Searcher Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_message=system_prompt,
        name="search-agent",
        description="Search agent that can search the web and return the results",
        input_parser=StrOutputParser(),
        output_parser=StrOutputParser(),
    )

# 2nd agent : Reader Agent

def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_message="""You are a reader agent that can read the content of a URL and return the content.""",
        name="reader-agent",
        description="Reader agent that can read the content of a URL and return the content",
        input_parser=StrOutputParser(),
        output_parser=StrOutputParser(),
    )

# Writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insights reports."),
    ("human", """Write a detailed search report on  the topic below.
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

# critic chain

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
