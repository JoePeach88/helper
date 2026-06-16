#!/usr/bin/env python
import sys
sys.dont_write_bytecode = True


import env
env.DEBUG = False
env.EMOJI_ENABLED = False


import base64
from pipreqs import pipreqs
from pathlib import Path
from helpers import list_helpers
from libs.messages import print_message
from env import __product_name__, __version__, __version_name__
from helpers.modules import modulesHelper
from helpers.core.utils import collect_requirements, detect_builtin, detect_core
from datetime import datetime


pip_ignore_win = ['getch']
pip_ignore_unix = []


def exit_code_check(system: str = 'Windows'):
    if system == 'Windows':
        return "\tif (-not $?) {$exit_code = $?}\n"
    else:
        return "\tif [ $? -ne 0 ]; then\n\t\texit_code=$?\n\tfi\n"


def windows_installer(structure: list, requirements: list):
    commands = [
        'do {\n',
        '\t$response = Read-Host "Do you want to continue? (y/n)"\n',
        '} until ($response -match \'^(y|n)$\')\n',
        'if ($response -eq \'y\') {\n',
        '\tif (($location = Read-Host "Specify install location (default: ./)") -eq \'\') { $location = "./" }',
        '\t$exit_code = $true\n',
        '\tWrite-Host "Preparing structure..."\n'
    ]
    installer_path = Path('./setup.ps1')

    def append_item(item: Path, requirements: bool = False):
        if item.is_dir():
            commands.append(f'\tNew-Item -ItemType Directory -Path "$location/{item.as_posix()}" -Force | Out-Null  2>> install.log\n')
            commands.append(exit_code_check())
            for child in sorted(item.iterdir()):
                append_item(child)
        else:
            if requirements:
                new_req_content = []
                with open(item, 'r', encoding='utf-8') as req_file:
                    for req_line in req_file.readlines():
                        for ignore_package in pip_ignore_win:
                            if ignore_package not in req_line:
                                new_req_content.append(req_line)
                    b64 = base64.b64encode('\n'.join(new_req_content).encode("utf-8")).decode("utf-8")
            else:
                with open(item, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
            commands.append(f"\t[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(\"{b64}\")) | Out-File -FilePath $location/{item.as_posix()} 2>> install.log\n\n")
            commands.append(exit_code_check())

    for entry in structure:
        append_item(Path(entry), Path(entry) in requirements)

    commands.extend([
        '\tWrite-Host "Structure prepared."\n', 
        '\tWrite-Host "Installing dependencies..."\n'
    ])
    for requirement in requirements:
        commands.append(f"\tpip install -r $location/{requirement.as_posix()}\n")
        commands.append(exit_code_check())
    commands.extend([
        "\tif (-not $exit_code) {\n",
        "\t\tWrite-Host \"Something went wrong during installation. Abort.\nLast exit code: $exit_code\"\n",
        "\t} else {\n",
        f"\t\tWrite-Host '{__product_name__} CLI v.{__version__} ({__version_name__}) (build date: {datetime.now()}) successfully installed!'\n",
        f"\t\tRemove-Item -Force ./{installer_path.as_posix()}\n",
        '\t\t$oldPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")\n',
        '\t\t$installPath = Convert-Path $location\n',
        '\t\tif (($env:Path -split \';\') -contains $installPath) {\n',
        '\t\t\t$newPath = "$oldPath;$installPath"\n',
        '\t\t\t[System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")\n\t\t}\n',
        "\t\tWrite-Host \"\nUsage:\n",
        "\thelper version - to view information about helper cli version and it installed modules.\n",
        "\thelper debug - to view cli debug information.\n",
        "\thelper modules ls - to view all available modules.\n",
        "\thelper <module_name> man - to view manual for helper module.\n",
        "\thelper <module_name> help - to view help information for module, show all available methods and its aliases.\"\n\t}\n",
        "}\n"
    ])
    with open(installer_path, 'w' if installer_path.exists() else 'x', newline="\n", encoding='utf-8') as installer_file:
        installer_file.writelines(commands)


def unix_installer(structure: list, requirements: list):
    commands = [
        '#!/bin/bash\n',
        'exit_code=0\n'
        f'read -r -p "Do you want to install {__product_name__} CLI? (y/n): " response\n',
        'if [[ "$response" =~ ^[Yy] ]]; then\n',
        'read -p "Specify install location (default: ./): " location\n',
        'if [[ -z "$location" ]]; then\n',
        '\tlocation=\'./\'\n',
        'fi\n',
        'echo "Preparing structure..."\n'
    ]
    installer_path = Path('./setup.sh')

    def append_item(item: Path, requirements: bool = False):
        if item.is_dir():
            commands.append(f"\tmkdir -p $location/{item.as_posix()} 2>> install.log\n")
            commands.append(exit_code_check('Unix'))
            for child in sorted(item.iterdir()):
                append_item(child)
        else:
            if requirements:
                new_req_content = []
                with open(item, 'r', encoding='utf-8') as req_file:
                    for req_line in req_file.readlines():
                        for ignore_package in pip_ignore_unix:
                            if ignore_package not in req_line:
                                new_req_content.append(req_line)
                    b64 = base64.b64encode('\n'.join(new_req_content).encode("utf-8")).decode("utf-8")
            else:
                with open(item, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
            commands.append(f"""\tbase64 --decode << 'EOF' > $location/{item.as_posix()}
{b64}
EOF
2>> install.log
""")
            commands.append(exit_code_check('Unix'))

    for entry in structure:
        append_item(Path(entry), Path(entry) in requirements)

    commands.extend(['\techo "Structure prepared."\n', '\techo "Installing dependencies..."\n'])
    for requirement in requirements:
        commands.append(f"\tpip install -r $location/{requirement.as_posix()} --break-system-packages")
        if pip_ignore_unix:
            commands.append(f" --exclude {' '.join(pip_ignore_unix)} 2>> install.log\n")
        else:
            commands.append(' 2>> install.log\n')
        commands.append(exit_code_check('Unix'))
    commands.extend([
        "\tif [ $exit_code -ne 0 ]; then\n",
        "\t\techo \"Something went wrong during installation. Abort.\nLast exit code: ${exit_code}\"\n",
        "\telse\n",
        f"\t\techo '{__product_name__} CLI v.{__version__} ({__version_name__}) (build date: {datetime.now()}) successfully installed!'\n",
        f"\t\trm -f ./{installer_path.as_posix()}\n",
        "\t\tinstall_location=$(realpath $location)\n",
        "\t\techo $PATH | grep -q \"${install_location}\" && echo \"export PATH=\\\"\$PATH:${install_location}\\\"\" >> ~/.bashrc && source ~/.bashrc\n",
        "\t\tchmod +x $location/helper\n",
        "\t\techo \"Usage:\n",
        "\thelper version - to view information about helper cli version and it installed modules.\n",
        "\thelper debug - to view cli debug information.\n",
        "\thelper modules ls - to view all available modules.\n",
        "\thelper <module_name> man - to view manual for helper module.\n",
        "\thelper <module_name> help - to view help information for module, show all available methods and its aliases.\"\n",
        "\tfi\n",
        "fi\n"
    ])
    with open(installer_path, 'w' if installer_path.exists() else 'x', newline="\n", encoding='utf-8') as installer_file:
        installer_file.writelines(commands)


def make_installer(structure: list, requirements: list, system: str = 'Unix'):
    if system == 'Unix':
        unix_installer(structure, requirements)
    elif system == 'Windows':
        windows_installer(structure, requirements)


if __name__ == '__main__':
    modules_helper = modulesHelper({})
    pipreqs_args = {'--encoding': 'utf-8', '--ignore': '.venv', '<path>': '.', '--force': True, '--savepath': None, '--print': None, 
                    '--pypi-server': None, '--proxy': None, '--use-local': None, '--diff': None, '--clean': None, '--mode': None}
    pipreqs_obj = pipreqs
    pipreqs_obj.logging.disable()
    print_message(f"Starting pipreqs with arguments {pipreqs_args}...", debug=True)
    pipreqs_obj.init(pipreqs_args)
    reqs_lines = []
    with open(Path('./requirements.txt'), 'r', encoding='utf-8') as reqs_file:
        reqs_lines = reqs_file.readlines()
    with open(Path('./requirements.txt'), 'w', newline="\n", encoding='utf-8') as reqs_file:
        reqs_file.writelines(reqs_lines)
    
    print_message('Listing core files...', debug=True)
    core_files = detect_core()
    print_message('Listing builtin modules files...', debug=True)
    builtin_helpers = detect_builtin()
    for builtin_helper in builtin_helpers:
        if builtin_helper.is_dir():
            print_message('Rendering hash, md and requirements for builtin modules...', debug=True)
            modules_helper.renderhash(module=builtin_helper.name)
            modules_helper.rendermd(module=builtin_helper.name)
            modules_helper.renderreq(module=builtin_helper.name)
    final_structure_files = core_files + builtin_helpers
    print_message('Listing requirements.txt files...', debug=True)
    requirements  = collect_requirements(final_structure_files)
    systems = ['Unix', 'Windows']
    for system in systems:
        print_message(f"Making installer for system '{system}'...", debug=True)
        make_installer(final_structure_files, requirements, system)
    print_message('Done.', 'SUCCESS', debug=True)
