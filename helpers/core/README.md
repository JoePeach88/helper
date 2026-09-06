# core

None

## Methods list

- [**config**](#config) [module]
- [get](#get)
- [ls](#ls)
- [rm](#rm)
- [set](#set)
- [**logging**](#logging) [module]
- [flush](#flush)
- [ls](#ls)
- [rm](#rm)
- [view](#view)
- [selfcheck](#selfcheck)
- [**update**](#update) [module]
- [check](#check)
- [install](#install)

## Installation

```bash
helper modules install core --location None
```

## Credits

**Author: [JoePeach88](https://github.com/JoePeach88)**

**Version: 1.3.0**

**Supported platforms:**

```
all
```

## Methods

## config

**Module to manipulate helper config parameters.**

### get

**Method retrieves config data.**
```
Usage:
core config get <section> <option>
```

### ls

**Method displays all config data.**
```
Usage:
core config ls
```

### rm

**Method removes specified section or option.**
```
Usage:
core config rm <section> <option>
```

### set

**Method sets config data.**
```
Usage:
1. Simple value set:
core config set <section> <option> <value>
2. Value set based on current system:
core config set <section> <option> <value> --system-based
```

## logging

**Module to manipulate with logs.**

### flush

**Method removes all log files.**
```
Usage:
core logging flush
```

### ls

**Method displays logs.**
```
Usage:
core logging ls
```

### rm

**Method removes log file.**
```
Usage:
core logging rm <log_file>
```

### view

**Method displays log content.**
```
Usage:
core logging view <log>
```

### selfcheck

**Method checks that all required parameters set for correct work.**
```
Usage:
core selfcheck
```

## update

**Module updates helper core.**

### check

**Method checks updates for helper core.**
```
Usage:
core update check
```

### install

**Method updates helper core.**
```
Usage:
core update install
```
