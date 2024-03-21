from dotenv import load_dotenv

load_dotenv()

import openai
from openai import OpenAI

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import Vector

from langchain_openai.embeddings import OpenAIEmbeddings
import chainlit as cl


@cl.on_chat_start
async  def factory():
    embeddings_model = OpenAIEmbeddings()
    open_ai_client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),  # this is also the default, it can be omitted
    )
    search_client = SearchClient(endpoint=os.getenv('AZURE_AI_SEARCH_ENDPOINT'),
                                 credential=AzureKeyCredential(os.getenv('AZURE_AI_SEARCH')), index_name="systems")
    cl.user_session.set("search_client" ,search_client)
    cl.user_session.set("embeddings_model" ,embeddings_model)
    cl.user_session.set("open_ai_client" ,open_ai_client)

@cl.on_message
async  def main(message):


    coversation_history = cl.user_session.get("coversation_history"," ")
    coversation_history = coversation_history + str(message.content)

    search_client = cl.user_session.get("search_client")
    embeddings_model = cl.user_session.get("embeddings_model")
    open_ai_client = cl.user_session.get("open_ai_client")
    vector = Vector(value=embeddings_model.embed_query(coversation_history), k=3, fields="embedding")
    result = search_client.search(search_text=None, vectors=[vector], select=["content"])
    input_text = ' '
    for rs in result:
        input_text = input_text + rs['content']
    response = open_ai_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"Answer the query based on given input text in brief less than 100 words.Please respond back with citations. Input{input_text}. Question: {query}",
        prompt=f"Context information is below.\n"
               f"---------------------------------------\n"
               f"{input_text}\n"
               f" Given strictly the context information and not the prior knowledge ,"
               f" Answer the query precisely  and friendly.If the query doesnot match the context information please respond with appropriate message saying he context is not available \n"
               f"Query : {coversation_history} \n"
               f"Answer : ",
        max_tokens=250,
        temperature=1
    )
    coversation_history = coversation_history + response.choices[0].text
    cl.user_session.set("coversation_history",coversation_history)

    print(response.choices[0].text)
    response_msg = cl.Message(content="")
    for token in response.choices[0].text:
        await  response_msg.stream_token(token)
