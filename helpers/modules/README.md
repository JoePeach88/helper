# modules

Module to work with helper modules.

## Methods list

- [create](#create)
- [disable](#disable)
- [enable](#enable)
- [info](#info)
- [install](#install)
- [ls](#ls)
- [pack](#pack)
- [renderhash](#renderhash)
- [rendermd](#rendermd)
- [renderreq](#renderreq)
- [uninstall](#uninstall)
- [**update**](#update) [module]
- [changes](#changes)
- [check](#check)
- [install](#install)

## Installation

```bash
helper modules install modules --location None
```

## Credits

**Author: [JoePeach88](https://github.com/JoePeach88)**

**Version: 1.0.0**

**Supported platforms:**

```
all
```

## Methods

### create

```
Method creates empty module from template for development.
Usage:
modules create <module_name> --name ModuleName --author Author --version 1.0.0 --systems Linux,Windows,Darwin
```

### disable

```
Method disables module.
Usage:
modules disable --module <module_name>
```

### enable

```
Method enables module.
Usage:
modules enable --module <module_name>
```

### info

```
Method displays information about installed module.
Usage:
modules info --module <module_name>
```

### install

```
Method installs specified module from link or from path.
Usage:
modules install <module_name> --location <link or path>
```

### ls

```
Method displays all available modules.
Usage:
modules ls
```

### pack

```
Method prepare module and packs it to tar archive.
Usage:
1. To default pack location:
modules pack <module_name>
2. To specified pack location:
modules pack <module_name> --location <location>
3. To pack few modules:
modules pack <module1> <module2> --location <location>
```

### renderhash

```
Method renders hash for each module file.
Usage:
modules renderhash <module_name>
```

### rendermd

```
Module renders README.md.
Usage:
modules rendermd <module_name>
```

### renderreq

```
Module renders requirements.txt.
Usage:
modules renderreq <module_name>
```

### uninstall

```
Method uninstalls specified module.
Usage:
modules uninstall <module_name>
```

## update

```
Module to manipulate and check updates for modules.
```

### changes

```
Method prints changelog for module.
Usage:
1. With prompt to select available modules.
modules update changes
2. With specified module.
modules update changes --module <module_name>
```

### check

```
Method checks updates for modules or specified module.
Usage:
1. Without specified module name:
modules update check
2. With specified module name:
modules update check --module module_name
```

### install

```
Method updates modules or specified module.
Usage:
1. Without specified module name:
modules update install
2. With specified module name:
modules update install --module module_name
```
