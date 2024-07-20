from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from openai import OpenAI
import os
from dotenv import load_dotenv
import numpy as np

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

default_system = "Ты-консультант в компании Simble, ответь на вопрос клиента на основе документа с информацией. Не придумывай ничего от себя, отвечай максимально по документу. Не упоминай Документ с информацией для ответа клиенту. Клиент ничего не должен знать про Документ с информацией для ответа клиенту"

class Chunk:
    def __init__(self, path_to_base: str, sep: str = " ", ch_size: int = 1024):
        with open(path_to_base, 'r', encoding='utf-8') as file:
            document = file.read()

        splitter = CharacterTextSplitter(separator=sep, chunk_size=ch_size)
        self.source_chunks = [Document(page_content=chunk, metadata={}) for chunk in splitter.split_text(document)]
        self.embeddings = self._get_embeddings([chunk.page_content for chunk in self.source_chunks])

    def _get_embeddings(self, texts):
        response = client.embeddings.create(input=texts, model="text-embedding-ada-002")
        return [embedding.embedding for embedding in response.data]

    def similarity_search(self, query, k=4):
        query_embedding = self._get_embeddings([query])[0]
        scores = [np.dot(query_embedding, doc_embedding) for doc_embedding in self.embeddings]
        top_indices = np.argsort(scores)[-k:][::-1]
        return [self.source_chunks[i] for i in top_indices]

    def get_answer(self, system: str = default_system, query: str = None):
        docs = self.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ответь на вопрос клиента. Не упоминай документ с информацией для ответа клиенту в ответе. Документ с информацией для ответа клиенту: {message_content}\n\nВопрос клиента: \n{query}"}
        ]

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0
        )
        
        return completion.choices[0].message.content

    async def async_get_answer(self, system: str = default_system, query: str = None):
        docs = self.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ответь на вопрос клиента. Не упоминай документ с информацией для ответа клиенту в ответе. Документ с информацией для ответа клиенту: {message_content}\n\nВопрос клиента: \n{query}"}
        ]

        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0
        )
        
        return completion.choices[0].message.content