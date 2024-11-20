import json
from colorama import Fore, Back, Style

class GenerativeQueryReformulation:
    
    def __init__(self):
        self._attempt_number = 1
        self._current_query = ""

    def GetPromptTemplate(self, template_path, for_creation=True):
        with open(template_path, 'r') as file:
            script = json.load(file)

        return "".join(script["templates"]["Query generation" if for_creation else "Documents evaluation"])
    
    def GetInjectionVariables(self, template_path, for_creation=True):
        with open(template_path, 'r') as file:
            script = json.load(file)
        
        return script["injection_variables"]["Query generation" if for_creation else "Documents evaluation"]
    
    def MakeQuery(self, generator, current_slot, memory):
        if self._current_query:
            injections = {
                "Previous query" : self._current_query
            }
            self._current_query = generator.invoke(injections)
            return self._current_query
        
        if current_slot == "Key questions":
            self._current_query = f"Key questions for UKPSF criterion {memory['UKPSF expectation']}"

        if current_slot == "Learning activities":
            self._current_query = f"Learning activities to answer {memory['Key questions']}"

        if current_slot == "Proof of mastery":
            self._current_query = f"Practise {memory['Learning activities']}"
        
        if current_slot == "Supporting roles":
            self._current_query = f"Supporting roles for {memory['UKPSF expectation']}"

        return self._current_query
    
    def ApproveDocuments(self, evaluator, documents):
        injections = {
            "Query" : self._current_query,
            "Documents" : documents
        }
        evaluation = evaluator.invoke(injections)
        print(Fore.CYAN + "Document Content Evaluation: " + evaluation)
        return evaluation.lower()[:2] != "no"
