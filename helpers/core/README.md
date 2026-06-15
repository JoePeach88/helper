# core

Module to work with helper core.

## Methods list

- [**config**](#config) [module]
- [get](#get)
- [ls](#ls)
- [set](#set)
- [**update**](#update) [module]
- [check](#check)
- [install](#install)

## Installation

```bash
helper modules install core --location None
```

## Credits

**Author: [JoePeach88](https://github.com/JoePeach88)**

**Version: 1.0.0**

**Supported platforms:**

```
all
```

## Methods

## config

```
Module to manipulate helper config parameters.
```

### get

```
Method retrieves config data.
Usage:
core config get <section> <option>
```

### ls

```
Method displays all config data.
Usage:
core config ls
```

### set

```
Method sets config data.
Usage:
1. Simple value set:
core config set <section> <option> <value>
2. Value set based on current system:
core config set <section> <option> <value> --system-based
```

## update

```
Module updates helper core.
```

### check

```
Method checks updates for helper core.
Usage:
core update check
```

### install

```
Method updates helper core.
Usage:
core update install
```
