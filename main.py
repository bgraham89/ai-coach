from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from algorithms.retreival_augmented_generation import RetreivalAugmentedGeneration
from algorithms.dialogue_state_tracking import DialogueStateTracking
from algorithms.generative_query_reformulation import GenerativeQueryReformulation
from testing.timer import Timer

import sys
from colorama import Fore, Back, Style

class Application(Timer):

    def __init__(self):
        super().__init__()
        self.TRAINING_MATERIAL_PATH = "./training_materials/"
        self.DIALOGUE_STATES_PATH = "./config/dialogue_states.json"
        self.PROMPT_TEMPLATE_PATH = "./config/prompt_template.json"
        self.ASSIGNMNETS_TEMPLATE_PATH = "./config/assignments.json"
        self.PRETRAINED_MODEL = "llama3.1"
        self._CreateDialogueStateTracker()
        self._CreateGenerativeQueryReformulator()
        self._CreatePretrainedModel()

    def __call__(self, initial_query=""):
        initial_query = sys.argv[1] if len(sys.argv) > 1 else "Hi"
        self.Coach(initial_query)

    def Coach(self, user_query):
        self._conversation = self._dst.GetNewConversation()
        while user_query:
            self._conversation.append(f"Higher Education Staff: {user_query} ")
            self._IntepretUserQuery()
            ai_response = self._RespondToUserQuery()
            self._conversation.append(f"Coach: {ai_response} ")
            user_query = input(Fore.BLUE + "\n")
        print(Fore.WHITE + "Goodbye!")

    def _CreateDialogueStateTracker(self, should_print=False):
        self._dst = DialogueStateTracking()
        self._dst.AddFramesModel(self.DIALOGUE_STATES_PATH)
        self.Print("Dialogue State Tracker Created.", should_print)

    def _CreateGenerativeQueryReformulator(self, should_print=False):
        self._gqr = GenerativeQueryReformulation()
        self.Print("Generative Query Reformulator Created.", should_print)

    def _CreateRAG(self, should_print=False):
        self._rag = RetreivalAugmentedGeneration()
        self._rag.StorePDFs(self.TRAINING_MATERIAL_PATH)
        self._retriever = self._rag._retriever
        self.Print("Vector Database Created.", should_print)
    
    def _CreatePromptTemplate(self, should_print=False, for_intepreter=False):
        self._prompt_template = PromptTemplate(
            template = self._dst.GetPromptTemplate(self.PROMPT_TEMPLATE_PATH, for_intepreter),
            input_variables = self._dst.GetInjectionVariables(self.PROMPT_TEMPLATE_PATH)
        )
        self.Print("Prompt Template Created.", should_print)
    
    def _CreatePretrainedModel(self, should_print=False):
        self._pretrained_model = ChatOllama(
            model = self.PRETRAINED_MODEL,
            temperature = 0
        )
        self.Print("Pretrained Model Created.", should_print)
    
    def _CreateResponder(self, should_print=False, for_intepretation=False):
        self._CreatePromptTemplate(should_print, for_intepretation)
        self._responder = self._prompt_template | self._pretrained_model | StrOutputParser()
        if not for_intepretation:
            self.Print("AI Coach Created.", should_print)

    def _GetPaths(self):
        paths = {
            "training_material" : self.TRAINING_MATERIAL_PATH,
            "prompt_templates" : self.PROMPT_TEMPLATE_PATH,
            "assignments" : self.ASSIGNMNETS_TEMPLATE_PATH
        }
        return paths
    
    def _GetDocumentText(self):
        if not self._dst.ShouldUseRAG(self.PROMPT_TEMPLATE_PATH):
            return ""

        if not hasattr(self, "_rag"):
            print(Fore.RED + "Creating RAG database - this may take a couple of minutes")
            self._CreateRAG()

        for _ in range(3):
            query = self._MakeQuery()
            documents = self._retriever.invoke(query)
            text = "\\n".join([doc.page_content for doc in documents])
            evaluator = self._CreateQueryEvaluator()
            if self._gqr.ApproveDocuments(evaluator, documents):
                break
            print(Fore.LIGHTRED_EX + f"Discarded RAG query: {query}.")
        else:
            print(Fore.MAGENTA + f"RAG could not extract anything useful.")
            return "A document containing nothing useful"
        print(Fore.YELLOW + f"RAG query: {query}.")
        print(Fore.MAGENTA + f"RAG extract: {text}.")
        return text
    
    def _GenerateResponse(self, prompt_injections):
        response = self._responder.invoke(prompt_injections)
        return response
    
    def _IntepretUserQuery(self):
        self._CreateResponder(for_intepretation=True)
        user_query = self._conversation[-1][24:]
        print(Fore.WHITE + f"User: '{user_query}'")
        documents = self._GetDocumentText()
        prompt_injections = self._dst.AddPromptInjections(self._conversation, documents, self._GetPaths())
        response = self._GenerateResponse(prompt_injections)
        if self._dst.FillSlot(response):
            self._conversation = self._dst.GetNewConversation() + self._conversation[-1:]
        print(Fore.GREEN + f"(Slot intepreted?: {response})")

    def _RespondToUserQuery(self):
        self._CreateResponder(for_intepretation=False)
        documents = self._GetDocumentText()
        prompt_injections = self._dst.AddPromptInjections(self._conversation, documents, self._GetPaths())
        response = self._GenerateResponse(prompt_injections)
        print(Fore.WHITE + f"Coach: '{response}'")
        return response
    
    def _MakeQuery(self):
        generator = self._CreateQueryGenerator()
        frame, slot = self._dst.GetCurrentFrame(should_clean=True)
        progress = self._dst.GetCurrentProgress()
        query = self._gqr.MakeQuery(generator, slot, progress)
        return query
    
    def _CreateQueryGenerator(self):
        prompt_template = PromptTemplate(
            template = self._gqr.GetPromptTemplate(self.PROMPT_TEMPLATE_PATH),
            input_variables = self._gqr.GetInjectionVariables(self.PROMPT_TEMPLATE_PATH)
        )
        return prompt_template | self._pretrained_model | StrOutputParser()
    
    def _CreateQueryEvaluator(self):
        prompt_template = PromptTemplate(
            template = self._gqr.GetPromptTemplate(self.PROMPT_TEMPLATE_PATH, for_creation=False),
            input_variables = self._gqr.GetInjectionVariables(self.PROMPT_TEMPLATE_PATH, for_creation=False)
        )
        return prompt_template | self._pretrained_model | StrOutputParser()




    
application = Application()
initial_query = sys.argv[1] if len(sys.argv) > 1 else ""
answer = application(initial_query)