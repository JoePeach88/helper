# helper CLI

The CLI which interpretates python modules as CLI commands.

Usage:
```
helper <module> <module_method> <module_args>
```

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Builtin modules](#builtin-modules)
- [Docs](#docs)

## Requirements

* **Python >= 3.7**
* **Installed requirements from [requirements.txt](https://github.com/JoePeach88/helper/blob/1.x.x/requirements.txt)**

## Installation

1. Install Python >= 3.7
    * from [official website](https://www.python.org/downloads/) for Windows
    * for other systems install Python using your package manager (`brew`/`apt`/`yum` and etc.)

### Automatic installation

2. Download and run setup script according to your system platform:

**\* For Windows:**

```pwsh
./setup.ps1
```

**\* For Unix:**

```bash
./setup.sh
```

### Manual installation

2. Clone source repository with helper code:

```bash
git clone https://github.com/JoePeach88/helper && git switch <specify version branch>
```

3. After Python installation, install requirement packages for `helper` using command:

```bash
python3 -m pip install -r ./requirements.txt
```

4. Add path of `helper` to your PATH environment variable

#### Additional installation steps

5. Make yours GitHub API token via [Fine-grained personal access tokens](https://github.com/settings/personal-access-tokens) and add yours SSH key via [settings](https://github.com/settings/keys)

6. Configure `helper` via `core` module, like this:

```bash
helper core config set core:remote gh_api_token <your token here>
```

7. After that you can check updates for modules, like this:

```bash
helper modules update check
```

or like this:

```bash
helper modules update install
```

## Builtin modules

* [core](https://github.com/JoePeach88/helper/blob/1.x.x/helpers/core/README.md) - Module to work with helper core settings.
* [modules](https://github.com/JoePeach88/helper/blob/1.x.x/helpers/modules/README.md) - Module to work with helper installed modules.

## Docs

* [Module Development Guide](./HELPERS.md)
