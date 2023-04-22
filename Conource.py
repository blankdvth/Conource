import logging
from json import load, dump
from os import mkdir, environ
from os.path import isfile, isdir, expanduser
from telnetlib import Telnet
from time import sleep
from typing import Union
from re import compile
from shlex import split as ssplit
from sys import platform as sysplatform

VERSION = "0.0.1"
ARG_REGEX = compile(r"\${{(\d+)}}")

home = expanduser("~")
platform_locations = {"linux": ".config", "darwin": ".config"}
if "use_project_dir" in environ and environ["use_project_dir"] == "1":
    DATA_PATH = "data"
elif sysplatform.startswith("win"):
    DATA_PATH = environ["APPDATA"] + "\\Conource"
else:
    DATA_PATH = home + "/" + platform_locations[sysplatform] + "/Conource"


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        message = (
            record.getMessage()
            .replace('"', "'")
            .replace(";", "<SEMICOLON>")
            .split("\n")[0]
        )
        if config["logging_console"] and record.levelno >= logging.WARNING:
            tn.write(f'echo "[Conource] [{record.levelname}] {message}"\n'.encode())


def load_config() -> dict:
    if not isdir(DATA_PATH):
        mkdir(DATA_PATH)
    if not isfile(DATA_PATH + "/config.json"):
        with open(DATA_PATH + "/config.json", "w") as f:
            dump(
                {
                    "host": "127.0.0.1",
                    "port": 16323,
                    "check_delay": 0,
                    "fail_check_delay": 5,
                    "console_prefix": "cn_",
                    "block_semicolon": True,
                    "logging_level": "INFO",
                    "logging_console": True,
                    "commands": {},
                },
                f,
                indent=2,
            )
    with open(DATA_PATH + "/config.json", "r") as f:
        return load(f)

    # TODO: Implement automatic config updates


def replace_args(command: str, args: list) -> str:
    for i, arg in enumerate(args):
        command = command.replace("${{" + str(i) + "}}", arg)
    return command


def read():
    global tn
    try:
        return tn.read_until(b"\n").decode("utf-8")
    except EOFError:
        logging.error("Connection lost, reconnecting")
        tn.close()
        tn = None
        while tn is None:
            try:
                tn = Telnet(config["host"], config["port"])
                logging.info("Connected to server")
            except ConnectionRefusedError:
                logging.debug(
                    "Connection refused, retrying in {} seconds".format(
                        config["fail_check_delay"]
                    )
                )
                sleep(config["fail_check_delay"])
        return ""


def send(command: Union[str, list], args=None):
    if args is None:
        args = []
    if isinstance(command, str):
        tn.write(f"{replace_args(command, args)}\n".encode())
    elif isinstance(command, list):
        for c in command:
            tn.write(f"{replace_args(c, args)}\n".encode())


if __name__ == "__main__":
    config = load_config()
    logging.basicConfig(
        level=config["logging_level"],
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(DATA_PATH + "/conource.log"),
            ConsoleHandler(),
        ],
    )
    logging.addLevelName(
        logging.WARNING + 1, "INFO - IMPORTANT"
    )  # Will log to console as well
    setattr(logging, "INFOIMP", logging.WARNING + 1)
    setattr(
        logging,
        "infoimp",
        lambda message, *args, **kwargs: logging.log(
            logging.INFOIMP, message, *args, **kwargs
        ),
    )
    logging.info("Conource v{}".format(VERSION))
    logging.info(
        "Loaded commands: {}".format(
            ", ".join([config["console_prefix"] + i for i in config["commands"].keys()])
        )
    )
    tn = None
    while tn is None:
        try:
            tn = Telnet(config["host"], config["port"])
            logging.info("Connected to server")
        except ConnectionRefusedError:
            logging.debug(
                "Connection refused, retrying in {} seconds".format(
                    config["fail_check_delay"]
                )
            )
            sleep(config["fail_check_delay"])

    while True:
        try:
            line = read()
            while line != "":
                if line.startswith(config["console_prefix"]):
                    command_raw = line[len(config["console_prefix"]) :].strip()
                    command_name = command_raw.split(" ")[0]
                    if command_name == "exit":
                        logging.infoimp("Exiting")
                        exit(0)
                    elif command_name == "help":
                        avail_commands = {}
                        for command, commands in config["commands"].items():
                            avail_commands[command] = (
                                int(max(ARG_REGEX.findall("".join(commands)), key=int))
                                + 1
                            )
                        logging.infoimp(
                            "Available commands: {}".format(
                                ", ".join(
                                    f"{i} ({j})" for i, j in avail_commands.items()
                                )
                            )
                        )
                    elif command_name == "reload":
                        config = load_config()
                        logging.infoimp("Reloaded config")
                    elif config["block_semicolon"] and ";" in command_raw:
                        logging.warning(
                            "Did not execute '{}' because it contains a semicolon".format(
                                command_raw
                            )
                        )
                        line = read()
                        continue
                    elif command_name in config["commands"]:
                        command_args = ssplit(command_raw[len(command_name) :])
                        commands = config["commands"][command_name]
                        max_args = (
                            int(max(ARG_REGEX.findall("".join(commands)), key=int)) + 1
                        )
                        if len(command_args) != max_args:
                            logging.error(
                                "{} arguments for command '{}', got {}, expected {}".format(
                                    "Too many"
                                    if len(command_args) > max_args
                                    else "Not enough",
                                    command_name,
                                    len(command_args),
                                    max_args,
                                )
                            )
                            line = read()
                            continue
                        logging.info("Running command '{}'".format(command_raw))
                        send(commands, command_args)
                    else:
                        logging.warning(
                            "Command {}{} not found".format(
                                config["console_prefix"], command_name
                            )
                        )
                line = read()
        except (Exception,) as e:
            logging.exception(repr(e))
        sleep(config["check_delay"])
