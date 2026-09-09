# Helper Development Guide

Use this guide to create and maintain helper modules for the `helper` CLI.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Quick Start](#quick-start)
- [\_\_init\_\_.py Template](#__init__py-template)
- [Required Module Variables](#required-module-variables)
- [Class and Method Conventions](#class-and-method-conventions)
- [Reserved Method and Argument Names](#reserved-method-and-argument-names)
- [Nesting Rules](#nesting-rules)
- [Install and Uninstall Scenarios](#install-and-uninstall-scenarios)
- [Scenario Syntax Reference](#scenario-syntax-reference)
- [Localization](#localization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Development Checklist](#development-checklist)

## Overview

Each helper is a Python module under `helpers/` that exposes methods as CLI commands.

Built-in modules:

- [`core`](./core/README.md) - manages helper core settings and updates.
- [`modules`](./modules/README.md) - manages helper modules and its updates.

## Directory Structure

```text
helpers
├───core [built-in]
├───modules [built-in]
└───helpername
    └───__init__.py
```

## Quick Start

You can quickly create a module using the built-in [`modules`](./modules/README.md) module:

```bash
modules create <module_name> --name ModuleName --author Author --version 1.0.0 --systems Linux,Windows,Darwin
```

After creation:

1. Implement module metadata and methods in `helpers/<module_name>/__init__.py`.
2. Ensure naming and restriction rules are followed.
3. Add optional `INSTALL.sc` and `UNINSTALL.sc` scenario files when needed.

## \_\_init\_\_.py Template

`__init__.py` is the main file of your helper module.

```python
from helpers import lang, mask, print_message, print_choices, print_choice, render_code, render_md, spinning_loader, SUCCESS, INFO, WARNING, ERROR, SUCCESS  # Basic helper imports.
from helpers.helpername.helper_additional_module import *  # Imports from additional helper modules.


# Module global settings
__module_disabled_methods__ = ['disabled_method']  # Methods that should not be available from CLI.
__module_name__ = 'HelperName'  # Helper name.
__module_author__ = 'AuthorName'  # Helper author.
__module_version__ = '0.1'  # Helper version.
__module_link__ = None  # Helper GitHub link.
__module_category__ = ['development', 'devops', 'k8s']  # Module categories.
__module_compatibility__ = ['all']  # Supported systems (for example: ['Linux', 'Windows', 'Darwin']).
__module_dependencies__ = [{}]  # Module dependencies (for example: [{'name': 'remote', 'link': 'https://github.com/Author/remote'}]).
__module_status__ = 'stable'  # Module status.
__methods_static_aliases__ = {  # Aliases for helper functions.
    'function_name': ['alias1', 'alias2']
}


class helpernameHelper:  # Helper class name format: <modulename>Helper
    def __init__(self, settings: dict):
        self.settings = settings

    def function_name(self, argument: str):
        return argument
```

## Required Module Variables

Each module must define these global variables:

```python
__module_disabled_methods__ = ['disabled_method']
__module_name__ = 'HelperName'
__module_author__ = 'AuthorName'
__module_version__ = '0.1'
__module_link__ = None
__module_category__ = ['development', 'devops', 'k8s']
__module_compatibility__ = ['all']
__module_dependencies__ = [{}]
__module_status__ = 'stable'
__methods_static_aliases__ = {
    'function_name': ['alias1', 'alias2']
}
```

## Class and Method Conventions

- The helper class must be named as `<pythonfile_name>Helper`.
- Use clear method names and include a short docstring with usage.
- Keep module methods focused and easy to discover from CLI help output.

Example:

```python
class helpernameHelper:
    """
    Module description.
    """
    def __init__(self, settings: dict):
        self.settings = settings

    def function_name(self, argument: str):
        """
        Returns the argument.
        Usage:
            helpername --argument argument
        """
        return argument
```

## Reserved Method and Argument Names

The following names are reserved and must not be used for custom helper methods or arguments.

### Reserved Methods

- `man` - prints module manual output.
- `version` - prints module version information.
- `requirements` - prints module requirements information.
- `help` - prints method or module help.
- `changes` - prints module changelog.

### Reserved Arguments

- `no_less` - prints full output without using built-in `less`.
- `not_pretty` - prints raw (non-pretty) output.

## Nesting Rules

Only one level of nested classes is supported under the root helper class.

Valid:

```python
class mainclassHelper:
    """
    Some main class.
    """
    def __init__(self, settings: dict):
        self.settings = settings

        # Subclasses
        self.subclass1 = self.subclass1(settings.get('mainclass:subclass1'))
        self.subclass2 = self.subclass2(settings.get('mainclass:subclass2'))

    class subclass1:
        """
        Some subclass 1.
        """
        def __init__(self, settings: dict):
            self.settings = settings

    class subclass2:
        """
        Some subclass 2.
        """
        def __init__(self, settings: dict):
            self.settings = settings
```

Invalid (nested subclass inside another subclass):

```python
class mainclassHelper:
    """
    Some main class.
    """
    def __init__(self, settings: dict):
        self.settings = settings

        # Subclasses
        self.subclass1 = self.subclass1(settings.get('mainclass:subclass1'))

    class subclass1:
        """
        Some subclass 1.
        """
        def __init__(self, settings: dict):
            self.settings = settings

            # Subclasses
            self.subclass11 = self.subclass11(settings.get('mainclass:subclass11'))

        class subclass11:
            """
            Some subclass 11.
            """
            def __init__(self, settings: dict):
                self.settings = settings
```

## Install and Uninstall Scenarios

You can configure pre/post install and uninstall hooks using `INSTALL.sc` and `UNINSTALL.sc`.

Structure:

```text
helpers
└───helpername
    ├───INSTALL.sc
    ├───UNINSTALL.sc
    └───__init__.py
```

### INSTALL.sc Example

```yaml
pre:
  scripts: [
    Linux|Darwin(./scripts/preinstall/1.sh),
    Windows(./scripts/preinstall/1.ps1)
  ]
  inline: []

post:
  scripts: []
  inline: []
```

### UNINSTALL.sc Example

```yaml
pre:
  scripts: [
    Linux|Darwin(./scripts/preuninstall/1.sh),
    Windows(./scripts/preuninstall/1.ps1)
  ]
  inline: [
    Linux|Darwin(/bin/bash 'rm -f /var/log/helper.log'),
    Windows(pwsh -Command "Remove-Item -Force C:\Windows\Logs\helper.log")
  ]

post:
  scripts: []
  inline: []
```

## Scenario Syntax Reference

Script syntax:

`PLATFORM(/path/to/script)`

Example:

`Linux|Darwin(./scripts/preuninstall/1.sh)`

Inline command syntax:

`PLATFORM(EXECUTABLE ADDITIONAL_KEYS INLINE_SCRIPT)`

Example:

`Linux|Darwin(/bin/bash 'rm -f /var/log/helper.log')`

## Localization

> NOTE! Localization is optional, you can still use docstring of class or method as source.

### Directory structure

```text
helpers
├───core [built-in]
├───modules [built-in]
└───helpername
    └───lang
        ├───ru_RU.lng
        └───en_US.lng
```

### Localization File Syntax

```yaml
metadata:
  author: Author
  version: Version
  lang: Lang Name

name_of_file_which_will_be_localized:
  name_of_helper.name_of_function_which_will_be_localized1: 
    description: "Usage documentation"  # Documentation string, which will be used with help argument
    items: "Some localization string"  # Used if outputs only one result from function
  name_of_helper.name_of_function_which_will_be_localized2:
    items:
      description: "Usage documentation" # Documentation string, which will be used with help argument
      # This additional ids used if outputs multiple results from function
      additional_id1: "Some localization string"
      additional_id2: "Some localization string"
```

### In Helper Usage

> Structure:

```text
helpers
└───mainclass
    ├───lang
    |   └───en_US.lng
    └───__init__.py
```

> en_US.lng

```yaml
metadata:
  author: SomeAuthor
  version: 1.0.0
  lang: English

__init__:
  mainclassHelper.single_result:
    description: |
      Usage:
        mainclass single_result
    items: "Hello World!"
  mainclassHelper.multiple_results:
    description: |
      Usage:
        mainclass multiple_results --true
    items:
        first: "First string"
        second: "Second string"
```

> \_\_init\_\_.py

```python
from helpers import lang, mask, print_message, print_choices, print_choice, render_code, render_md, spinning_loader, SUCCESS, INFO, WARNING, ERROR, SUCCESS  # Basic helper imports.
from helpers.helpername.helper_additional_module import *  # Imports from additional helper modules.

...

class mainclassHelper:
    def __init__(self, settings: dict):
        self.settings = settings

    def single_result(self):
        return lang.get()  # Returns "Hello World!" from en_US.yml
    
    def multiple_results(self, true: bool = False):
        return lang.get('first') if true else lang.get('second')  # Returns "First string" or "Second string" depends on `true` state. For example if you run `helper mainclass multiple_results --true` result will be "First string"
```


## Best Practices

- Keep helper methods small and task-specific.
- Use meaningful method names and aliases.
- Document method usage in docstrings.
- Limit side effects in install/uninstall hooks.
- Make localization only for returned data, not print_message values.
- Keep scenario scripts idempotent when possible.

## Troubleshooting

- **Module not visible from CLI**: check `__module_name__`, class name format, and module path under `helpers/`.
- **Method not available**: verify it is not listed in `__module_disabled_methods__` and does not use a reserved name.
- **Scenario not executing**: validate `INSTALL.sc` / `UNINSTALL.sc` syntax and platform selector values.
- **Wrong output format**: check whether `not_pretty` or `no_less` is being used.

## Development Checklist

- [ ] Module directory exists under `helpers/`.
- [ ] `__init__.py` contains all required module variables.
- [ ] Helper class follows `<modulename>Helper` naming.
- [ ] No reserved method or argument names are used.
- [ ] Nesting does not exceed one subclass level.
- [ ] Optional `INSTALL.sc` / `UNINSTALL.sc` files are valid.
- [ ] Method docstrings include clear usage examples.
