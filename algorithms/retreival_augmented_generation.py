import os, pathlib

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings

class RetreivalAugmentedGeneration:
    
    def __init__(self):
        self.API_KEY_PATH = "./api.key"
        self.DEFAULT_CHUNK_SIZE = 200
        self.DEFAULT_CHUNK_OVERLAP = 100
        self.DEFAULT_QUERY = ""

    def StorePDFs(self, pdf_directory):
        files = os.listdir(pdf_directory)
        if not files:
            print(f"DEBUG: No files could be found in {pdf_directory}")
            return
        
        self._CreateTextSplitter()
        all_document_sections = self._SplitDocuments(files, pdf_directory)
        cleaned_document_sections = self._CleanSections(all_document_sections)
        self._CreateVectorStore(cleaned_document_sections)
        self._CreateRetriever()


    def _CreateTextSplitter(self, chunk_size=0, chunk_overlap=0):
        self._text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE, 
            chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
        )
    
    def _CreateVectorStore(self, all_document_sections):
        api_key = pathlib.Path(self.API_KEY_PATH).read_text()
        if not api_key:
            print(f"DEBUG: Could not find api key in {self.API_KEY_PATH}")
            self._vector_store = False
            return

        self._vector_store = SKLearnVectorStore.from_documents(
            documents = all_document_sections,
            embedding = OpenAIEmbeddings(api_key=api_key)
        )
    
    def _CreateRetriever(self):
        if not self._vector_store:
            print(f"DEBUG: Could not create retriever as there's no vector store.")
            self._retriever = False
            return
        
        self._retriever = self._vector_store.as_retriever(k=4)
    
    def _SplitDocuments(self, files, directory):
        all_document_sections = []
        for file in files:
            if file[-3:].lower() != "pdf":
                print(f"DEBUG: {file} not included.")
                continue

            path = directory + file
            loader = PyPDFLoader(path)
            document_sections = loader.load_and_split(self._text_splitter)
            all_document_sections.extend(document_sections)
        return all_document_sections
    
    def _CleanSections(self, all_document_sections, chunk_size=0, chunk_overlap=0):
        for section in all_document_sections:
            section.page_content = section.page_content.replace('\n', '')
            section.page_content = section.page_content.replace('-', '')

        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        is_useful_section = lambda x : len(x.page_content) >= chunk_size
        useful_sections = list(filter(is_useful_section, all_document_sections))

        return useful_sections
