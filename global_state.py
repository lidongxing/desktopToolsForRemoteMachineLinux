class GlobalState:
    _instance = None
    _task_type = None
    _upload_id = 0
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GlobalState()
        return cls._instance
    
    @property
    def task_type(self):
        return self._task_type
    
    @task_type.setter
    def task_type(self, value):
        self._task_type = value
        
    @property
    def upload_id(self):
        return self._upload_id
    
    @upload_id.setter
    def upload_id(self, value):
        self._upload_id = value 