from dotenv import load_dotenv
import chainlit as cl
load_dotenv()

import openai
from openai import OpenAI
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from azure.search.documents.models import Vector

from langchain_openai import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings()

open_ai_client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),  # this is also the default, it can be omitted
)


def openai_complete_response(context, query):
    print(context)
    response = open_ai_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"Answer the query based on given input text in brief less than 100 words.Please respond back with citations. Input{input_text}. Question: {query}",
        prompt=f"Context information is below.\n"
               f"---------------------------------------\n"
               f"{context}\n"
               f" Given  the context information and not the prior knowledge ,"
               f" Answer the query briefly and friendly.If the query doesnot match the context information please respond with appropriate message saying he context is not available \n"
               f"Query : {query} \n"
               f"Answer : ",
        max_tokens=100,
        temperature=0
    )

    return response


@cl.on_chat_start
async def factory():
    embeddings_model = OpenAIEmbeddings()
    search_client = SearchClient(endpoint=os.getenv('AZURE_AI_SEARCH_ENDPOINT'),
                                 credential=AzureKeyCredential(os.getenv('AZURE_AI_SEARCH')), index_name="systems")

    cl.user_session.set('embeddings_model', embeddings_model)
    cl.user_session.set('search_client', search_client)


@cl.on_message
async def main(message):
    embeddings_model = cl.user_session.get('embeddings_model')
    search_client = cl.user_session.get('search_client')

    query = str(message)
    vector = Vector(value=embeddings_model.embed_query(query), k=3, fields="embedding")
    result = search_client.search(search_text=None, vectors=[vector], select=["content"])
    input_text = '  '
    for rs in result:
        input_text = input_text + rs['content']

    response = await cl.make_async(openai_complete_response)(input_text, query)
    print('HERE----------------------------------\n')
    print(response.choices[0]. text )
    response_msg = cl.Message(content="")
    for token in response.choices[0]. text:
        await  response_msg.stream_token(token)