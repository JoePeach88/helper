# modules

None

## Methods list

- [create](#create)
- [disable](#disable)
- [enable](#enable)
- [info](#info)
- [install](#install)
- [**language**](#language) [module]
- [translate](#translate)
- [ls](#ls)
- [pack](#pack)
- [push](#push)
- [renderhash](#renderhash)
- [rendermd](#rendermd)
- [renderreq](#renderreq)
- [rendertemplate](#rendertemplate)
- [rendertests](#rendertests)
- [**test**](#test) [module]
- [start](#start)
- [viewreport](#viewreport)
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

**Version: 1.3.0**

**Supported platforms:**

```
all
```

## Methods

### create

**Method creates empty module from template for development.**
```
Usage:
modules create <module_name> --name ModuleName --author Author --version 1.0.0 --systems Linux,Windows,Darwin
```

### disable

**Method disables module.**
```
Usage:
modules disable --module <module_name>
```

### enable

**Method enables module.**
```
Usage:
modules enable --module <module_name>
```

### info

**Method displays information about installed module.**
```
Usage:
modules info --module <module_name>
```

### install

**Method installs specified module from link or from path.**
```
Usage:
modules install <module_name> --location <link or path>
```

## language

**Module to work with language files.**

### translate

**Method translates en_US localization to different languages.**
> NOTE: After translation, you need to manually check translate correctness.
```
Usage:
1. Default usage:modules language translate <module_name> --language <language_code>
2. With custom provider:
modules language translate <module_name> --language <language_code> --provider <provider_name>
```
Available providers:
* `yandex`
* `google` [default]
* `mymemory`
* `microsoft`
* `chatgpt`

### ls

**Method displays all available modules.**
```
Usage:
modules ls
```

### pack

**Method prepare module and packs it to tar archive.**
```
Usage:
1. To default pack location:
modules pack <module_name>
2. To specified pack location:
modules pack <module_name> --location <location>
3. To pack few modules:
modules pack <module1> <module2> --location <location>
```

### push

**Method pushes module source code to it`s repo.**
>NOTE: Before using this method, configure your GitHub account to use SSH keys.
```
Usage:
modules push <module_name>
```

### renderhash

**Method renders hash for each module file.**
```
Usage:
modules renderhash <module_name>
```

### rendermd

**Method renders README.md.**
```
Usage:
modules rendermd <module_name>
```

### renderreq

**Method renders requirements.txt.**
```
Usage:
modules renderreq <module_name>
```

### rendertemplate

**Method renders template from templates path.**
```
Usage:
modules rendertemplate <template> <file> <args>
```

### rendertests

**Method renders tests from template for specified module.**
```
Usage:
modules rendertests <module>
```

## test

**Module to work with module`s tests.**

### start

**Method runs tests for specified module.**
```
Usage:
1. Only test, without reports:
modules test start <module>
2. Test with reports rendering:
module test start <module> --report
```

### viewreport

**Method to view tests results.**
```
Usage:
1. View summary report:
modules test viewreport <module>
2. View specified report:
modules test viewreport <module> --report <report>
```

### uninstall

**Method uninstalls specified module.**
```
Usage:
modules uninstall <module_name>
```

## update

**Module to manipulate and check updates for modules.**

### changes

**Method prints changelog for module.**
```
Usage:
1. With prompt to select available modules.
modules update changes
2. With specified module.
modules update changes --module <module_name>
```

### check

**Method checks updates for modules or specified module.**
```
Usage:
1. Without specified module name:
modules update check
2. With specified module name:
modules update check --module module_name
```

### install

**Method updates modules or specified module.**
```
Usage:
1. Without specified module name:
modules update install
2. With specified module name:
modules update install --module module_name
```
