class SSHManager:
    _instance = None
    _ssh_client = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SSHManager()
        return cls._instance
    
    @property
    def ssh_client(self):
        return self._ssh_client
    
    @ssh_client.setter
    def ssh_client(self, client):
        self._ssh_client = client
    
    def execute_command(self, command):
        """执行SSH命令并返回结果"""
        if not self._ssh_client:
            raise Exception("SSH连接未建立")
        
        stdin, stdout, stderr = self._ssh_client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()
    
    def close(self):
        """关闭SSH连接"""
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None 