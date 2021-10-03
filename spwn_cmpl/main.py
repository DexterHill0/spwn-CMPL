import argparse
import platform
import shutil
import sys
import os
#it's like re but better
import regex
import tempfile
from pathlib import Path

from .logger import Logger 

class Platforms:
	Unknown = -1
	Windows = 0
	Darwin = 1
	Linux = 2

def get_platform():
	try:
		return vars(Platforms)[platform.system()]
	except KeyError:
		return Platforms.Unknown

#the location of the module + containers directory
CONTAINER_FOLDER = Path(os.path.dirname(os.path.realpath(__file__))) / "containers"

#the extension for the current OS
class Extensions:
	EXECUTABLE = { Platforms.Windows: ".exe", Platforms.Darwin: "", Platforms.Linux: "." }[get_platform()]

parser = argparse.ArgumentParser(description="--SPWN-CMPL-- | Compile SPWN files into a standalone EXE.")

parser.add_argument("--entry", "-e", help="Main SPWN file", 
                    dest="entry", action="store", type=Path, required=True)

parser.add_argument("--out", "-o", help="Output file directory",
                    dest="out", action="store", type=Path, required=False)
parser.add_argument("--name", "-n", help="Output file name",
                    dest="name", action="store", type=str, required=False)

parser.add_argument("--include", "-I", help="List of extra files to include. (If a .spwn file is provided, it will *not* be checked for imports)",
                    dest="inc", nargs="+", type=Path, default=[], required=False)

parser.add_argument("--args", "-A", help="String of arguments to pass to SPWN executable",
                    dest="pass_through", action="store", type=str, required=False)

parser.add_argument("--verbose", "-v", help="Increased Logger verbosity",
                    dest="verbose", action="store_true", required=False)

class Paths:
	
	def __init__(self) -> None:
		self = vars(self).update(self.get_paths())
	
	def get_paths(self):
		Logger.info("Getting paths")

		Logger.debug(f"Platform: [{platform.system()}](LIGHTBLUE_EX|)")

		command = "{} spwn".format("where" if get_platform() == Platforms.Windows else "which")

		#get location of spwn executable
		with os.popen(command) as h:
			SPWN = Path(h.read().strip())
		SPWN_LIBS = SPWN.parents[0] / "libraries"

		WRAPPER_EXE = Path(platform.system().lower())

		Logger.debug(
			f"Paths:\n	spwn.exe: [{SPWN}](YELLOW|),\n	spwn_libs: [{SPWN_LIBS}](YELLOW|),\n	container_exe: [{WRAPPER_EXE}](YELLOW|)")

		return {"SPWN": SPWN, "WRAPPER_EXE": WRAPPER_EXE, "LIBS": SPWN_LIBS}


class LibrarySearcher():

	#finished reg: https://regex101.com/r/EBaNtd/1
	#carves out import statments in the spwn code
	IMPORT_REG = r"^(?:(?!import).)*([\"'])(?:(?=(\\?))\2.)+?\1.*(*SKIP)(*FAIL)$|import (\"|')?(?P<relative>(\.(\\|\/)|(.*\/)+?))?(?P<filename>[^\"\\\s]+)(\"|')?"
	
	def __init__(self) -> None:
		self.import_regex = regex.compile(LibrarySearcher.IMPORT_REG, flags=regex.MULTILINE)

		self.found = []

	def recurse_libs(self, entry):
		if not entry.exists():
			Logger.error(f"{{RED|}} Couldn't find entry/library file: [{entry}](YELLOW|)")
			raise FileNotFoundError(entry)

		with open(entry, "r") as h:

			for line in h.readlines():
				match = self.import_regex.search(line)

				if match is None:
					continue
				
				#start at base folder of script
				path = entry.parents[0]

				if match["relative"] or "spwn" in match["filename"].lower():
					#ignore the gamescene library since it's always included no matter what
					if match["filename"] == "gamescene":
						continue

					path = path / (match["relative"] if match["relative"]
					               is not None else "") / match["filename"]
				else:
					path = path / "libaries" / match["filename"] / "lib.spwn"

				self.found.append(path)

				self.recurse_libs(path)

		return self.found


class Compiler():
	
	def __init__(self, args) -> None:
		Logger.set_level(
			Logger.DEBUG if args.verbose else Logger.INFO, 
		)

		self.pargs = args
		self.paths = Paths()

		self.search = LibrarySearcher()
	
	def compile(self):
		Logger.info("Recursively searching files for libraries")

		#get all the libraries used in the SPWN file
		libs = self.search.recurse_libs(self.pargs.entry)

		Logger.info(
			f"Found [{len(libs)} imported](LIGHTGREEN_EX|) files, [{len(self.pargs.inc)} extra](LIGHTGREEN_EX|) files")

		#add the extra files
		libs.extend(self.pargs.inc)
		#add the main file too
		libs.append(self.pargs.entry)

		Logger.debug(f"Files: {libs}")

		out = Path(self.pargs.out if self.pargs.out else "./bin")
		out.mkdir(parents=True, exist_ok=True)

		file_name = out / (self.pargs.name if self.pargs.name else self.paths.WRAPPER_EXE.with_suffix(Extensions.EXECUTABLE))

		# create copy of executable
		shutil.copy(CONTAINER_FOLDER / self.paths.WRAPPER_EXE, file_name)

		Logger.info("Creating executable")

		#open the copied executable in append binary mode
		with open(file_name, "ab") as h:
			#get size in bytes of spwn exe
			spwn_size = self.paths.SPWN.stat().st_size

			Logger.debug(f"Size of SPWN exe: [{spwn_size} bytes](LIGHTBLUE_EX|)")

			#copy the actual spwn exe data to the container exe
			h1 = open(self.paths.SPWN, "rb")
			h.write(h1.read())
			h1.close()

			temp_dir = Path(tempfile.mkdtemp())

			#create directory 1 level down
			os.mkdir(temp_dir / "data")
			temp_dir = temp_dir / "data"

			#copy spwn library files to temp folder
			shutil.copytree(self.paths.LIBS, temp_dir / "libraries")
			Logger.debug(
				f"Copied STD libraries to temp folder: [{temp_dir}](YELLOW|)")

			for lib in libs:
				try:
					#will gradually make the directory structure if it doesnt already exist
					#so shutil.copy doesnt complain
					os.makedirs((temp_dir / lib).parents[0])
				except FileExistsError:
					pass
				shutil.copy(lib, temp_dir / lib)

			os.chdir(temp_dir)

			Logger.debug("Copied program files to temp folder")

			zipf = Path(shutil.make_archive("../out", "zip", root_dir="./", base_dir=None))
			zip_size = zipf.stat().st_size
			Logger.debug(
				f"Created zip file of all required SPWN files, size: [{zip_size} bytes](LIGHTBLUE_EX|)")

			#write zip file data
			h1 = open(zipf, "rb")
			h.write(h1.read())
			h1.close()

			#write command line args for spwn exe
			h.write(b"\x00")
			arg = f"b {self.pargs.entry} {self.pargs.pass_through}"
			h.write(arg.encode())

			#add the sizes of each file so the executable can extract the data
			h.write(b"\x00")
			h.write(f"{zip_size}".encode())

			h.write(b"\x00")
			h.write(f"{spwn_size}".encode())

			Logger.debug(
				f"Written exe data: [{os.fstat(h.fileno()).st_size} bytes](LIGHTBLUE_EX|)")

		Logger.info(f"Finished creating executable! ([{file_name}](YELLOW|))")
			
		#cd home to leave directory - means we can remove the temporary directory
		os.chdir(os.path.expanduser("~"))

		Logger.debug("Removing temporary directory")
		#delete temporary directory
		shutil.rmtree(temp_dir / "../")

def main():
	args = parser.parse_args()

	c = Compiler(args)
	c.compile()

if __name__ == "__main__":
	main()
