import logging
from typing import Any, Callable, Union

import paramiko
from git import Repo

console_out = logging.StreamHandler()
logging.basicConfig(handlers=[console_out],
                    format='[%(levelname)s]: %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class RemoteManager:

    def __init__(self,
                 hostname: str = "",
                 username: str = "",
                 key_filepath: str = "",
                 local_repository_path: str = "",
                 remote_repository_path: str = "",
                 app_restart_command: str = "",
                 celery_restart_command: str = "",
                 is_restart_app: Union[bool, str] = False
                 ):
        self.hostname = hostname
        self.username = username
        self.key_filepath = key_filepath
        self.local_repository_path = local_repository_path
        self.remote_repository_path = remote_repository_path
        self.app_restart_command = app_restart_command
        self.celery_restart_command = celery_restart_command
        self.is_restart_app = eval(is_restart_app) if isinstance(is_restart_app, str) \
                                                   else is_restart_app

    def set_config(self, config: dict[str, Any]):
        self.__init__(**config)
        with open("config", "a+") as file:
            file.seek(0)
            file.truncate()
            for setting, value in config.items():
                file.writelines(f"{setting}={value}\n")

    def read_config_file(self):
        config = {}
        with open("config", "a+") as file:
            file.seek(0)
            settings = file.readlines()
            for setting in settings:
                name, value = setting.split("=")
                config[name] = value.strip()
        self.__init__(**config)

    def _ssh_connection(func: Callable):
        def wrapper(self, *args, **kwargs) -> None:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_filepath)
                func(self, ssh, *args, **kwargs)
                ssh.close()
            except Exception as error:
                logger.error(str(error))
        return wrapper

    @_ssh_connection
    def perform_replacement(self, ssh: paramiko.SSHClient):
        local_project_repo = Repo(self.local_repository_path)
        changed_files = [item.a_path for item in local_project_repo.index.diff(None)]
        logger.info(f"Changed files --> {changed_files}")
        sftp = ssh.open_sftp()
        for local_file_path in changed_files:
            full_local_file_path = self.local_repository_path + local_file_path
            full_remote_file_path = self.remote_repository_path + local_file_path
            sftp.put(full_local_file_path, full_remote_file_path)
        logging.info(f"Files replaced successfully!")
        if self.is_restart_app:
            logger.info("Restarting server...")
            ssh.exec_command(f"{self.app_restart_command}; {self.celery_restart_command}")
        sftp.close()

    @_ssh_connection
    def undo_replacement(self, ssh: paramiko.SSHClient):
        stdin, stdout, stderr = ssh.exec_command(f"cd {self.remote_repository_path}; git stash -u && git stash drop")
        logging.info(stdout.readlines())
        logging.info(f"Сhanges were successfully rolled back!")


manager = RemoteManager()
manager.read_config_file()

while True:
    try:
        command = input("--> ")
        options = None
        if '--' in command:
            _c = command.split('--')
            options = _c[-1].split(' ')
            command = _c[0]

        if command.startswith("help"):
            logger.info("Available commands: \n"
                        "{replace} --> perform replacement modified files to remote repository \n"
                        "{undo}    --> undo replacement changes \n"
                        "{config}  --> set-up new config, options: \n"
                        "              --hostname\n"
                        "              --username\n"
                        "              --key_filepath\n"
                        "              --local_repository_path\n"
                        "              --remote_repository_path\n"
                        "              --app_restart_command\n"
                        "              --celery_restart_command\n"
                        "              --is_restart_app\n"
                        "              set option: {config --hostname 0.0.0.0}\n"
                        "              show option value: {config --hostname}\n"
                        "              to set full new config write {config}")

        elif command.startswith("config"):
            config = {}
            if options:
                if len(options) > 1:
                    setattr(manager, options[0], options[1])
                # elif options[0] == 'all':
                #     for attr in ...:
                #         ...
                else:
                    logger.info(f"{options[0]} = {manager.__getattribute__(options[0])}")
            else:
                config["hostname"] = input("hostname: ")
                config["username"] = input("username: ")
                config["key_filepath"] = input("key_filepath: ")
                config["local_repository_path"] = input("local_repository_path: ")
                config["remote_repository_path"] = input("remote_repository_path: ")
                config["app_restart_command"] = input("app_restart_command: ")
                config["celery_restart_command"] = input("celery_restart_command: ")
                config["is_restart_app"] = input("is_restart_app: ")
                manager.set_config(config)

        elif command.startswith("replace") or command == "r":
            manager.perform_replacement()

        elif command.startswith("undo") or command == "u":
            manager.undo_replacement()

        elif command.startswith("exit"):
            break

        else:
            logger.info("No such command (type {help} to see all commands)")

    except Exception as error:
        logger.error(str(error))
