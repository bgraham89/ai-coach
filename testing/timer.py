import time

class Timer:

    def __init__(self):
        self._time_created = time.time()
        self._should_print_with_time = True 

    def Print(self, string_to_print, should_print):
        if not should_print:
            return

        if not self._should_print_with_time:
            print(string_to_print)
            return
        
        time_passed = time.time() - self._time_created
        print(f"{string_to_print[:-1]} after {time_passed}.")