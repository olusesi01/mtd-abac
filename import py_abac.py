from py_abac.storage.json import JSONFileStorage

class PolicyManager:
    def __init__(self):
        self.storage = JSONFileStorage("policies.json")
        self.pdp = PDP(self.storage)
