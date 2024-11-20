import json
from colorama import Fore, Back, Style

class DialogueStateTracking:

    def __init__(self):
        self._current_frame = ""
        self._current_slot = ""
        self._frames = []
        self._slots = {}
        self._progress = {}

    def AddFramesModel(self, model_path):
        with open(model_path, 'r') as file:
            specification = json.load(file)

        self._model = specification["model"]
        self._frames.extend(specification["frames"])
        self._slots.update(specification["slots"])
        self._progress.update({ slot : False for frame, slots in specification["slots"].items() for slot in slots})

    def GetPromptTemplate(self, template_path, for_intepreter=False):
        with open(template_path, 'r') as file:
            script = json.load(file)

        self._current_frame, self._current_slot = self.GetCurrentFrame(for_intepreter)
        for_intepreter and print(Fore.YELLOW + f"\nCurrent Frame: {self._current_frame} (Slot: {self._current_slot[9:]})") # Remove "Intepret "
        return "".join(script["templates"][self._current_slot])

    def GetInjectionVariables(self, template_path):
        with open(template_path, 'r') as file:
            script = json.load(file)
        
        return script["injection_variables"][self._current_slot]
    
    def GetCurrentSlot(self, frame, should_clean=False):
        for slot in self._slots[frame]:
            if not self._progress[slot]:
                return self._CleanSlot(slot) if should_clean else slot
        return ""
    
    def GetCurrentFrame(self, for_interpreter=False, should_clean=False):
        for frame in self._frames:
            if slot := self.GetCurrentSlot(frame, should_clean):
                return frame, "Intepret " + slot if for_interpreter else slot
        print("DEBUG: Could not deduce current frame and slot")
        return "", ""
    
    def GetCurrentProgress(self):
        return self._progress
    
    def AddPromptInjections(self, conversation, documents, paths):
        input_variables = self.GetInjectionVariables(paths["prompt_templates"]) 
        injections = {}

        for variable in input_variables:
            if variable == "conversation":
                injections["conversation"] = conversation
                continue
            if variable == "documents":
                injections["documents"] = documents
                continue
            if variable == "assignments":
                injections["assignments"] = self._GetAssignmentTitles(paths["assignments"])
                continue
            if variable == "rubrik":
                injections["rubrik"] = self._GetAssignmentRubrik(paths["assignments"])
                continue

            # injection from previous slot
            injections[variable] = self._progress[variable]

        return injections
    
    def ShouldUseRAG(self, template_path):
        return "documents" in self.GetInjectionVariables(template_path)

    def GetNewConversation(self):
        return ["The conversation start's now."]
    
    def ApproveDocuments(self, documents):
        return True
    
    def FillSlot(self, intepretation, paths):
        if "no" == intepretation.lower()[:2]:
            return False
        
        current_frame, current_slot = self.GetCurrentFrame()
        self._progress[current_slot] = self._CleanIntepretation(intepretation, paths)
        return True
    
    def _GetAssignmentTitles(self, template_path):
        with open(template_path, 'r') as file:
            assignment_info = json.load(file)
        
        return "/n".join(assignment_info["titles"])
    
    def _GetAssignmentRubrik(self, template_path):
        with open(template_path, 'r') as file:
            assignment_info = json.load(file)
        
        assignment_choice = self._progress["Assignment choice"].lower()
        rubrik = assignment_info["answers"][self._RemovePunctuation(assignment_choice)]
        return "/n".join(rubrik)
    
    def _CleanSlot(self, slot):
        if len(slot) > 9 and slot[:8] == "Intepret":
            slot = slot[9:]
        return slot
    
    def _CleanIntepretation(self, interpretation, paths):
        current_frame, current_slot = self.GetCurrentFrame()
        return interpretation if current_slot != "Assessment" else self._GetQuestionInsight(interpretation, paths["assignments"])
    
    def _GetQuestionInsight(self, intepretation, path):
        choice = int("".join(char for char in intepretation if char.isnumeric()) or 2) - 1
        with open(path, 'r') as file:
            assignment_info = json.load(file)
        
        assignment_choice = self._progress["Assignment choice"].lower()
        insight = assignment_info["explanations"][self._RemovePunctuation(assignment_choice)][choice]
        print(Fore.CYAN + f"Chosen question: {choice + 1}")
        print(Fore.CYAN + f"Question purpose: {insight}")
        return insight
    
    def _RemovePunctuation(self, text):
        return "".join([c for c in text if c.isalnum() or c.isspace()])