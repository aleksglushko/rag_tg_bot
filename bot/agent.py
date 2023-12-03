from llama_index import VectorStoreIndex, ServiceContext, SimpleDirectoryReader
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.agent import OpenAIAgent
from llama_index.node_parser import SimpleNodeParser
from llama_index.text_splitter import SentenceSplitter
from llama_index.llms import OpenAI

import os
import openai
import tiktoken


from config import openai_api_key
openai.api_key = openai_api_key

def init_data_agent(agent_prompt, model="gpt-3.5-turbo-16k"):
    llm = OpenAI(model=model)
    documents = SimpleDirectoryReader("data").load_data()

    text_splitter = SentenceSplitter(
        separator=" ",
        chunk_size=2048,
        chunk_overlap=100,
        paragraph_separator="\n\n\n",
        secondary_chunking_regex="[^,.;。]+[,.;。]?",
        tokenizer=tiktoken.encoding_for_model("gpt-3.5-turbo").encode,
    )

    node_parser = SimpleNodeParser.from_defaults(text_splitter=text_splitter)

    service_context = ServiceContext.from_defaults(node_parser=node_parser)

    index = VectorStoreIndex.from_documents(
        documents, service_context=service_context
    )

    individual_query_engine_tool = QueryEngineTool(
            query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name=f"vector_index",
                description=f"useful for when you want to answer queries about the FAQ",
            ),
        )

    agent = OpenAIAgent.from_tools([individual_query_engine_tool], 
                                   verbose=True, 
                                   system_prompt=agent_prompt, 
                                   llm=llm)
    return agent