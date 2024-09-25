import logging
import traceback
from typing import Any, Callable

import paramiko
from git import Repo


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

    def _ssh_session(func: Callable):
        def wrapper(self, *args, **kwargs) -> None:
            try:
                with paramiko.SSHClient() as ssh:
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_filepath)
                    kwargs.update({"ssh": ssh})
                    func(self, *args, **kwargs)
            except Exception as error:
                logger.error(str(error))
        return wrapper

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

    @_ssh_session
    def restart_app(self, ssh: paramiko.SSHClient):
        ssh.exec_command(f"cd {self.remote_repository_path}; "
                         f"{self.restart_command}")
        logger.info("Restarting app...")

    @_ssh_session
    def perform_push(self, restart: bool, ssh: paramiko.SSHClient):
        local_project_repo = Repo(self.local_repository_path)
        changed_files = [item.a_path for item in local_project_repo.index.diff(None)]
        logger.info(f"Changed files ({len(changed_files)}) --> {changed_files}")
        self.drop_changes()
        with ssh.open_sftp() as sftp:
            for local_file_path in changed_files:
                full_local_file_path = self.local_repository_path + local_file_path
                full_remote_file_path = self.remote_repository_path + local_file_path
                sftp.put(full_local_file_path, full_remote_file_path)
            logger.info(f"Files pulled successfully!")
        if restart:
            self._restart_app(ssh)

    @_ssh_session
    def drop_changes(self, ssh: paramiko.SSHClient):
        stdin, stdout, stderr = ssh.exec_command(f"cd {self.remote_repository_path}; git stash -u && git stash drop")
        logger.info(f"SERVER RESPONSE:\n{''.join(stdout.readlines())}")
        logger.info(f"Сhanges were successfully rolled back!")

    @_ssh_session
    def switch_branch(self, branch: str, restart: bool, ssh: paramiko.SSHClient):
        if branch == "master":
            raise Exception("Do not touch master branch!")
        stdin, stdout, stderr = ssh.exec_command(f"cd {self.remote_repository_path}; git switch master; "
                                                 f"git branch -D {branch}; "
                                                 f"git switch -c {branch} --track origin/{branch}")
        logger.info(f"SERVER RESPONSE:\n{''.join(stdout.readlines())}")
        logger.info(f"Branch successfully re-switched")
        if restart:
            self._restart_app(ssh)


class CommandHandler:

    COMMAND_HELP    = ("help",)
    COMMAND_EXIT    = ("exit",)
    COMMAND_CONFIG  = ("cfg", "config")
    COMMAND_HISTORY = ("h", "history")
    COMMAND_LAST    = ("l", "last")
    COMMAND_PUSH    = ("p", "push")
    COMMAND_DROP    = ("d", "drop")
    COMMAND_RESTART = ("r", "restart")
    COMMAND_SWITCH  = ("s", "switch")

    def __init__(self):
        self.manager = RemoteManager()
        self.manager.read_config_file()
        self.command_history: list = []
        self.title_command_map: dict = {}
        self.call_command_map: dict = {}
        self.do_last_command: bool = False
        self.__build_command_map()

    def __build_command_map(self):
        command_names = [item for item in CommandHandler.__dict__.items() if item[0].startswith("COMMAND")]
        for item in command_names:
            for command in item[1]:
                self.title_command_map[command] = item[0].lower()

        command_funcs = [item for item in CommandHandler.__dict__.items() if item[0].startswith("execute_")]
        for item in command_funcs:
            self.call_command_map[item[0].replace("execute_", "")] = item[1]

    def _handle_command_input(self) -> tuple[str, dict[str, Any]]:
        if self.do_last_command:
            self.do_last_command = False
            command = self.command_history[-1]
        else:
            command = input("--> ")
            if self.title_command_map.get(command):
                self.command_history.append(self.title_command_map.get(command).replace("command_", ""))
            else:
                self.command_history.append(command)
        options = {}
        spl_command = command.split(' ')
        command = spl_command[0]
        spl_options = spl_command[1:]
        for index, option in enumerate(spl_options):
            if option.startswith("-") or option.startswith("--"):
                options[option.strip('-')] = option.strip('-')
            else:
                options['param'] = option
        return command, options

    def start(self):
        while True:
            try:
                command, options = self._handle_command_input()
                command_name = self.title_command_map.get(command)
                if not command_name:
                    logger.info("No such command (type {help} to see all commands)")
                    continue
                self.call_command_map.get(command_name)(self, options)
            except Exception as error:
                if str(error) == "exit":
                    break
                logger.error(traceback.format_exc())

    def execute_command_help(self, options: dict[str, Any]):
        logger.info("Available commands: \n"
                    "{p} | {push}      -->  push modified files to remote repository \n"
                    "                       options: {-nr | --no-restart} \n"
                    "{d} | {drop}      -->  drop changes \n"
                    "{r} | {restart}   -->  restart the app \n"
                    "{s} | {switch}    -->  switch branch by deleting it and track again \n"
                    "                       param: {branch_name} \n"
                    "                       options: {-r | --restart} \n"
                    "                       switch branch with restart: {switch LKM-669 -r} \n"
                    "{cfg} | {config}  -->  config: \n"
                    "                       options: {-s | --set} \n"
                    "                       set full new config: {config -s | --set} \n"
                    "                       see config options: {config} \n"
                    "{l} | {last}      -->  execute last command \n"
                    "{h} | {history}   -->  show command history \n"
                    "{help}            -->  show commands info \n"
                    "{exit}            -->  exit program \n")

    def execute_command_exit(self, options: dict[str, Any]):
        raise Exception("exit")

    def execute_command_config(self, options: dict[str, Any]):
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
                self.manager.set_config(config)
        else:
            for attribute, value in self.manager.__dict__.items():
                logger.info(f"{attribute + ' = ' + str(value)}")

    def execute_command_history(self, options: dict[str, Any]):
        for command in self.command_history:
            logger.info(f"{command}")

    def execute_command_last(self, options: dict[str, Any]):
        self.do_last_command = True
        self.command_history.pop(-1)

    def execute_command_push(self, options: dict[str, Any]):
        restart = True
        if options.get("nr") or options.get("no-restart"):
            restart = False
        self.manager.perform_push(restart)

    def execute_command_drop(self, options: dict[str, Any]):
        self.manager.drop_changes()

    def execute_command_restart(self, options: dict[str, Any]):
        self.manager.restart_app()

    def execute_command_switch(self, options: dict[str, Any]):
        restart = False
        if "r" in options or "restart" in options:
            restart = True
        self.manager.switch_branch(branch=options["param"], restart=restart)


if __name__ == '__main__':
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=[console_out],
                        format="[%(levelname)s]: %(message)s",
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    command_handler = CommandHandler()
    command_handler.start()
