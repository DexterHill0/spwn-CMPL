import logging as _logging
import regex
from colorama import Fore, Back, Style, init

#init colorama
init(autoreset=True, convert=True)


#so overcomplicated lmao
GLOBAL_REG = regex.compile(r"{(?P<FORE>([A-Z_]+)?)\|(?P<BACK>([A-Z_]+)?)}")
SINGLE_REG = regex.compile(
	r"\[(?P<TEXT>([a-zA-Z0-9_ :\\.()]+)?)\]\((?P<FORE>([A-Z_]+)?)\|(?P<BACK>([A-Z_]+)?)\)")

F_COL = {**vars(Fore), "": ""}
B_COL = {**vars(Back), "": ""}

# adds colours to strings:
# - "{FOREGROUND|BACKGROUND}" / "{FOREGROUND|}" / "{|BACKGROUND}"
#    - assigns a global colour to the string (meaning it affects the entire string)
# 
# - "[text](FOREGROUND|BACKGROUND)" / "[text](FOREGROUND|)" / "[text](|BACKGROUND)"
#    - assigns a colour to just the text within the square brackets
#    - the global colour (if set) will continue after the text within the brackets
#
def format_colour(string):
	#default colours if there are no global definitions
	prev_global = [Fore.WHITE, ""]

	for col in GLOBAL_REG.finditer(string):
		fore, back = F_COL[col.group("FORE")], B_COL[col.group("BACK")]
		
		string = string.replace(col[0], f"{fore}{back}")

		# add the latest global colour so it can be replaced if single text is coloured
		prev_global = [fore, back]

	for col in SINGLE_REG.finditer(string):
		fore, back, text = F_COL[col.group(
			"FORE")], B_COL[col.group("BACK")], col.group("TEXT")

		string = string.replace(
			col[0], f"{fore}{back}{text}{prev_global[0]}{prev_global[1]}")

	# styles apply only to that string
	string += Style.RESET_ALL

	return string

class Logger():
	INFO = _logging.INFO
	DEBUG = _logging.DEBUG

	def set_level(level=_logging.INFO):
		_logging.basicConfig(
			level=level,
			format="%(message)s"
		)

	def info(message):
		_logging.info(f"{Fore.CYAN}INFO:{Style.RESET_ALL} {format_colour(message)}")

	def warn(message):
		_logging.warn(
			f"{Fore.YELLOW}WARN:{Style.RESET_ALL} {format_colour(message)}")

	def error(message):
		_logging.error(f"{Fore.RED}ERROR:{Style.RESET_ALL} {format_colour(message)}")

	def debug(message):
		_logging.debug(
			f"{Fore.GREEN}DEBUG:{Style.RESET_ALL} {format_colour(message)}")

