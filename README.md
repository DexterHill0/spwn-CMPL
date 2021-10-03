# spwn-CMPL
Compile your SPWN files into a standalone executable!

<sup>Name by</sup> [<sup>@Deltara3</sup>](https://github.com/Deltara3)

### Notes
* The code was written to work across all platforms, but the container exectuable has only been compiled for windows, so it will need to be compiled for the other platforms.
<br>

## Installation
### Requirements
* `python >= 3.6`
* `regex >= 2021.8.28` ([regex](https://pypi.org/project/regex/))
Clone the repository:
```bash
mkdir spwn-CMPL
git clone https://github.com/DexterHill0/spwn-CMPL.git
cd spwn-CMPL
```
Run the setup:
```bash
python setup.py install
```

## Usage
```
> spwn-CMPL

  -h, --help                                Show this help message and exit
  --entry ENTRY, -e ENTRY                   Main SPWN file
  --out OUT, -o OUT                         Output file directory
  --name NAME, -n NAME                      Output file name
  --include INC [INC ...], -I INC [INC ...] List of extra files to include. (If a .spwn file is provided, it will *not* be checked for imports)
  --args PASS_THROUGH, -A PASS_THROUGH      String of arguments to pass to SPWN executable
  --verbose, -v                             Increased Logger verbosity
```
* `--include` any extra files needed for execution (text files, data files, etc.), or any imported file that cannot be found, can be passed to this argument so they are included in the executable.
* `--args`: The arguments that you want the SPWN exe to be called with. A list of arguments can be found [here](https://github.com/Spu7Nix/SPWN-language#flags)

<br>

## Execution
When run, the generated executable will execute the SPWN code within. For speed, it stores this code in a temporary directory. The generated executable can be executed with 3 flags:
```
no flags - runs the spwn code and keeps the temporary directory
```
or
```
--once / -o Remove all file after execution has finished
```
or
```
--clean / -c Removes any files that were created previously
```
<br>

## Building From Source
### Requirements
* `Rust`

Clone the repository:
```bash
mkdir spwn-CMPL
git clone https://github.com/DexterHill0/spwn-CMPL.git
cd spwn-CMPL
```
Open as a VSCode workspace:
```bash
code .
```
To build:
`F1` -> `Tasks: Run Task` -> `Cargo Build: Dev` / `Cargo Build: Release`
* `Dev` builds a development executable into the `target` folder.
* `Release` builds a development executable into the `target` folder, then moves it into the `containers` folder, and renames it.
