# Conource

Conource is a program that allows you to define your own custom commands (with arguments) for the CS:GO console.

## Prerequisites

- Python 3

## Installation

- Download the [latest release](https://github.com/blankdvth/Conource/releases/latest) (as a ZIP file)
- Extract the ZIP file to where you want the program to be installed
- Open a terminal in the extracted folder
- Run the program once (so that data files are created)

## Setup

- Open your Steam library
- Right click on CS:GO and click on `Properties`
- In the Launch Options field, enter `-netconport 16323` (this is the default port the program uses, you can change it
  in the config file)

## Configuration

The data folder is located in your config folder (on Windows, this
is `C:\Users\YOUR_USERNAME\AppData\Roaming\Conource`).
Open the configuration file (`config.json`). Below is an outline of what each option does, and how to configure your
aliases.

### Settings

- **`host`**: The host to bind to. This is almost always `127.0.0.1` or `localhost`.
- **`port`**: The port to bind to. This is the port you entered in the CS:GO launch options.
- **`check_delay`**: The delay between each full readthrough of the console. This is in seconds.
- **`fail_check_delay`**: How often the connection is retried when it fails. This is in seconds.
- **`console_prefix`**: The prefix that is expected to be before each command.
- **`block_semicolon`**: Whether to block semicolons in command arguments. This is HIGHLY RECOMMENDED, disabling it can
  leave you vulnerable to command injection.
- **`logging_level`**: The amount of logging shown. This can be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- **`logging_console`**: If enabled, logs of level `WARNING` and above will be shown in the console.
- **`commands`**: Dictionary of commands. See next section for more information.

### Commands

Commands are the main feature of the program, and are created via the `commands` section of the config file. All
commands are executed by an `echo` command in console, followed by your command prefix, command name, and arguments.

Each command is in the format of:

```json
"command_name": [
  "command1",
  "command2",
  "etc"
]
```

The `command_name` is the name that is used to invoke the command, it is case-sensitive. Each command has an array of
actual commands to run.
Placeholders can be used in these commands to insert arguments. They are in the format `${{NUM}}`, where `NUM` is the
position/index of the argument (starting from 0).
Here's an example that will send a message in chat, greeting the first argument:

```json
"hello": [
  "say Hello, ${{0}}!"
]
```

If the `console_prefix` is `cn_`, then the command can be invoked with `echo cn_hello World` in console (output would
be `Hello, World!`).

Keep in mind the program needs to be restarted for changes to take effect.

## Usage

All commands can be invoked by opening the CS:GO console (default key is `~`, needs to be enabled in settings), and
typing:
`echo <command prefix><command name> <arguments>}`, for example if the command prefix were `cn_`, the command
were `hello`
, and it took one argument: `echo cn_hello John`.

### Default Commands
There are a few default commands that perform various actions, they are checked before your commands so you cannot have
duplicate names. All default commands must be prefixed with the command prefix.

- **exit**: This exits the program.
- **help**: This shows a list of commands, and how many arguments they take.
- **reload**: This reloads the config file (not all changes can be applied via reload, such as logging changes. A restart may be needed)

## Common Issues

### CS adds spaces to my arguments

There are certain special characters that CS pads with spaces, `:` is one example. To get around this, you can add
double-quotes around the entire command, for example: `echo "cn_hello Person:John"`. Alternatively, if you're afraid
you'll forget, you can replace the one argument with 3 (one before, one colon, one after). `say Hello ${{0}}` becomes
`say Hello ${{0}}${{1}}${{2}}`.
