import json
from colorama import Fore, Back, Style
from testing.timer import Timer

class DialogueStateTracking(Timer):

    def __init__(self):
        super().__init__()
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

    def GetPromptTemplate(self, template_path, for_comprehension=False, is_cot=False, cot_index=0, is_cot_final_stage=False):
        with open(template_path, 'r') as file:
            script = json.load(file)

        self._current_frame, self._current_slot = self.GetCurrentFrame(for_comprehension)
        
        if not is_cot:
            for_comprehension and self.Print(Fore.YELLOW + f"\nCurrent Frame: {self._current_frame} (Slot: {self._current_slot[11:]})") # Remove "Comprehend "
            return "".join(script["templates"][self._current_slot])

        if not is_cot_final_stage:
            templates = script["templates"][self._current_slot]
            if cot_index >= len(templates):
                return ""
            return "".join(templates[cot_index])
        
        return "".join(script["reasoning"][self._current_slot])

        
        
        

    def GetInjectionVariables(self, template_path):
        with open(template_path, 'r') as file:
            script = json.load(file)
        
        return script["injection_variables"][self._current_slot]
    
    def GetCurrentSlot(self, frame, should_clean=False):
        for slot in self._slots[frame]:
            if not self._progress[slot]:
                return self._CleanSlot(slot) if should_clean else slot
        return ""
    
    def GetCurrentFrame(self, for_comprehension=False, should_clean=False):
        for frame in self._frames:
            if slot := self.GetCurrentSlot(frame, should_clean):
                return frame, "Comprehend " + slot if for_comprehension else slot
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
    
    def ShouldUseChainOfThought(self, template_path):
        with open(template_path, 'r') as file:
            script = json.load(file)

        self._current_frame, self._current_slot = self.GetCurrentFrame(True)
        should_use_cof = script["has_chain_of_thought"][self._current_slot] == "True"
        should_use_cof and self.Print(Fore.CYAN + f"Using Chain Of Thought")
        return should_use_cof

    def GetNewConversation(self):
        return ["The conversation start's now."]
    
    def ApproveDocuments(self, documents):
        return True
    
    def FillSlot(self, comprehension, paths):
        if "no" == comprehension.lower()[:2]:
            return False
        
        current_frame, current_slot = self.GetCurrentFrame()
        self._progress[current_slot] = self._CleanComprehension(comprehension, paths)
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
        if len(slot) > 11 and slot[:10] == "Comprehend":
            slot = slot[10:]
        return slot
    
    def _CleanComprehension(self, comprehension, paths):
        current_frame, current_slot = self.GetCurrentFrame()
        return comprehension if current_slot != "Assessment" else self._GetQuestionInsight(comprehension, paths["assignments"])
    
    def _GetQuestionInsight(self, comprehension, path):
        choice = int("".join(char for char in comprehension if char.isnumeric())) - 1
        with open(path, 'r') as file:
            assignment_info = json.load(file)
        
        assignment_choice = self._progress["Assignment choice"].lower()
        insight = assignment_info["explanations"][self._RemovePunctuation(assignment_choice)][choice % 4]
        self.Print(Fore.RED + f"Insight: {insight}")
        return insight
    
    def _RemovePunctuation(self, text):
        return "".join([c for c in text if c.isalnum() or c.isspace()])