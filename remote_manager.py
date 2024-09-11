import logging
from typing import Any, Callable

import paramiko
from git import Repo

console_out = logging.StreamHandler()
logging.basicConfig(handlers=[console_out],
                    format="[%(levelname)s]: %(message)s",
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
                 ):
        self.hostname = hostname
        self.username = username
        self.key_filepath = key_filepath
        self.local_repository_path = local_repository_path
        self.remote_repository_path = remote_repository_path
        self.restart_command = f"{app_restart_command}; {celery_restart_command}"

    def _ssh_connection(func: Callable):
        def wrapper(self, *args, **kwargs) -> None:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_filepath)
                kwargs.update({"ssh": ssh})
                func(self, *args, **kwargs)
                ssh.close()
            except Exception as error:
                logger.error(str(error))
        return wrapper

    @_ssh_connection
    def restart_app(self, ssh: paramiko.SSHClient):
        ssh.exec_command(self.restart_command)
        logger.info("Restarting app...")

    def _restart_app(self, ssh: paramiko.SSHClient):
        ssh.exec_command(self.restart_command)
        logger.info("Restarting app...")

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

    @_ssh_connection
    def perform_pull(self, ssh: paramiko.SSHClient):
        local_project_repo = Repo(self.local_repository_path)
        changed_files = [item.a_path for item in local_project_repo.index.diff(None)]
        logger.info(f"Changed files ({len(changed_files)}) --> {changed_files}")
        sftp = ssh.open_sftp()
        for local_file_path in changed_files:
            full_local_file_path = self.local_repository_path + local_file_path
            full_remote_file_path = self.remote_repository_path + local_file_path
            sftp.put(full_local_file_path, full_remote_file_path)
        logging.info(f"Files pulled successfully!")
        sftp.close()
        self._restart_app(ssh)

    @_ssh_connection
    def undo_pull(self, ssh: paramiko.SSHClient):
        stdin, stdout, stderr = ssh.exec_command(f"cd {self.remote_repository_path}; git stash -u && git stash drop")
        logging.info(f"SERVER RESPONSE:\n{''.join(stdout.readlines())}")
        logging.info(f"Сhanges were successfully rolled back!")

    @_ssh_connection
    def switch_branch(self, branch: str, restart: bool, ssh: paramiko.SSHClient):
        if branch == "master":
            raise Exception("Do not touch master branch!")
        stdin, stdout, stderr = ssh.exec_command(f"cd {self.remote_repository_path}; git switch master; "
                                                 f"git fetch --all; "
                                                 f"git branch -D {branch}; "
                                                 f"git switch -c {branch} --track origin/{branch}")
        logging.info(f"SERVER RESPONSE:\n{''.join(stdout.readlines())}")
        logging.info(f"Branch successfully re-switched")
        if restart:
            self._restart_app(ssh)


manager = RemoteManager()
manager.read_config_file()

while True:
    try:
        command = input("--> ")
        options = {}
        spl_command = command.split(' ')
        command = spl_command[0]
        spl_options = spl_command[1:]
        for index, option in enumerate(spl_options):
            if option.startswith("-") or option.startswith("--"):
                options[option.strip('-')] = option.strip('-')
            else:
                options['param'] = option

        # print(options)

        if command == "help":
            logger.info("Available commands: \n"
                        "{p} | {pull}     --> pull modified files to remote repository \n"
                        "{u} | {undo}     --> undo pull changes \n"
                        "{r} | {restart}  --> restart the app \n"
                        "{s} | {switch}   --> switch branch by deleting it and track again \n"
                        "                     param: {branch_name} \n"
                        "                     options: {-r | --restart} \n"
                        "                 switch branch with restart: {switch LKM-669 -r} \n"
                        "{config}         --> config: \n"
                        "                     options: {-s | --set} \n"
                        "                 set full new config: {config -s | --set} \n"
                        "                 see config options: {config} \n")

        elif command == "config":
            config = {}
            if options:
                if options.get('set'):
                    config["hostname"] = input("hostname: ")
                    config["username"] = input("username: ")
                    config["key_filepath"] = input("key_filepath: ")
                    config["local_repository_path"] = input("local_repository_path: ")
                    config["remote_repository_path"] = input("remote_repository_path: ")
                    config["app_restart_command"] = input("app_restart_command: ")
                    config["celery_restart_command"] = input("celery_restart_command: ")
                    config["is_restart_app"] = input("is_restart_app: ")
                    manager.set_config(config)
                    continue
            else:
                for attribute, value in manager.__dict__.items():
                    logger.info(f"{attribute + ' = ' + str(value)}")

        elif command == "pull" or command == "p":
            manager.perform_pull()

        elif command == "undo" or command == "u":
            manager.undo_pull()

        elif command == "switch" or command == "s":
            restart = False
            if "r" in options or "restart" in options:
                restart = True
            manager.switch_branch(branch=options["param"], restart=restart)

        elif command == "restart" or command == "r":
            manager.restart_app()

        elif command == "exit":
            break

        else:
            logger.info("No such command (type {help} to see all commands)")

    except Exception as error:
        logger.error(str(error))
