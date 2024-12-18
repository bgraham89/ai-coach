import json
import random
from colorama import Fore, Back, Style

class Automator(object):

    def __init__(self):
        self._should_automate = True
        self.TEST_CASES_PATH = "./testing/examples.json"
        self.ASSIGNMENTS_TEMPLATE_PATH = "./config/assignments.json"
        self._inputs = []
        self._case = "case-2"
        self._specifics = {}
        super().__init__()

    def Input(self, prompt):
        if not self._should_automate:
            return input(prompt)
        
        if not self._inputs:
            self._CreateInputs()

        response = next(self._inputs)
        return self._CustomiseResponse(response)
    
    def _CreateInputs(self):
        with open(self.TEST_CASES_PATH, 'r') as file:
            responses = json.load(file)["responses"]

            if not self._case:
                keys = [key for key in responses.keys()]
                self._case = random.choice(keys)
            
        self._inputs = (response for response in responses[self._case])
    
    def _CustomiseResponse(self, response):
        if not self._specifics:
            self._CreateSpecifics()
        
        keys = [key for key in self._specifics.keys()]

        for key in keys:
            if f">{key}<" in response:
                response = response.replace(f">{key}<", self._specifics[f"{key}"])
        
        return response

    def _CreateSpecifics(self):

        with open(self.ASSIGNMENTS_TEMPLATE_PATH, 'r') as file:
            assignment_details = json.load(file)
            modules = assignment_details["titles"]
            self._specifics["module"] = random.choice(modules).lower()

            num_answers = len(assignment_details["answers"][self._specifics["module"]]) - 1
            self._specifics["answers"] = ", ".join(str(i+1) + ". " + str(random.choice(["true", "false"])) for i in range(num_answers))
        
        self._specifics["ukpsf"] = random.choice([a + str(b+1) for a in "AKV" for b in range(5)])
            



            



        
        

