import openai
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import chainlit as cl

from azure.search.documents.models import Vector
from dotenv import load_dotenv

from langchain.embeddings import OpenAIEmbeddings
load_dotenv()


openai.api_key = os.getenv('OPENAI_API_KEY')

def openai_complete_response(context,query):
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        # prompt=f"Answer the query based on given input text in brief less than 100 words.Please respond back with citations. Input{input_text}. Question: {query}",
        prompt=f"""Context  is below."
                context : {context}"
                Given strictly the context information and not the prior knowledge ,
                Answer the below query briefly .If the query doesnot match the context information please respond with appropriate message saying he context is not available "
                query : {query} \n"
               Answer : """,
        max_tokens=100,
        temperature=0
    )
    return response

@cl.on_chat_start
async  def factory():
    embeddings_model = OpenAIEmbeddings()
    search_client = SearchClient(endpoint=os.getenv('AZURE_AI_SEARCH_ENDPOINT'),
                                 credential=AzureKeyCredential(os.getenv('AZURE_AI_SEARCH')), index_name="systems")
    cl.user_session.set('embeddings_model',embeddings_model)
    cl.user_session.set('search_client',search_client)


@cl.on_message
async  def main(message):
    embeddings_model =   cl.user_session.get('embeddings_model' )
    search_client =  cl.user_session.get('search_client')

 
    query = message.content
    vector = Vector(value=embeddings_model.embed_query( query), k =2 , fields="embedding")
    result = search_client.search(search_text=None, vectors=[vector] ,select=["content"])
    input_text = '  '
    for rs in result:
        input_text =input_text + rs['content']


    response =   await cl.make_async(openai_complete_response)(input_text,query)
    print('HERE----------------------------------\n')
    print(response['choices'][0]['text'])
    response_msg = cl.Message(content="")
    for token in response['choices'][0]['text'] :
        await  response_msg.stream_token(token)