import logging
from json import load, dump
from os import mkdir, environ
from os.path import isfile, isdir, expanduser
from telnetlib import Telnet
from time import sleep
from typing import Union
from shlex import split as ssplit
from sys import platform as sysplatform


def load_config() -> dict:
    home = expanduser("~")
    platform_locations = {"linux": ".config", "darwin": ".config"}
    if "use_project_dir" in environ and environ["use_project_dir"] == "1":
        DATA_PATH = "data"
    elif sysplatform.startswith("win"):
        DATA_PATH = environ["APPDATA"] + "\\Conource"
    else:
        DATA_PATH = home + "/" + platform_locations[sysplatform] + "/Conource"

    if not isdir(DATA_PATH):
        mkdir(DATA_PATH)
    if not isfile(DATA_PATH + "/config.json"):
        with open(DATA_PATH + "/config.json", "w") as f:
            dump(
                {
                    "host": "127.0.0.1",
                    "port": 16323,
                    "check_delay": 5,
                    "console_prefix": "cn_",
                    "password": None,
                    "logging_level": "INFO",
                    "commands": {},
                },
                f,
                indent=2,
            )
    with open(DATA_PATH + "/config.json", "r") as f:
        return load(f)


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
                        config["check_delay"]
                    )
                )
                sleep(config["check_delay"])
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
        handlers=[logging.StreamHandler(), logging.FileHandler("data/conource.log")],
    )
    tn = None
    while tn is None:
        try:
            tn = Telnet(config["host"], config["port"])
            logging.info("Connected to server")
        except ConnectionRefusedError:
            logging.debug(
                "Connection refused, retrying in {} seconds".format(
                    config["check_delay"]
                )
            )
            sleep(config["check_delay"])

    while True:
        line = read()
        while line != "":
            if line.startswith(config["console_prefix"]):
                command_raw = line[len(config["console_prefix"]) :].strip()
                command_name = command_raw.split(" ")[0]
                if command_name in config["commands"]:
                    command_args = ssplit(command_raw[len(command_name) :])
                    commands = config["commands"][command_name]
                    logging.info("Running command '{}'".format(command_raw))
                    send(commands, command_args)
                else:
                    logging.warning(
                        "Command {}{} not found".format(
                            config["console_prefix"], command_name
                        )
                    )
            line = read()
        sleep(5)
