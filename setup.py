from setuptools import setup, find_packages
import glob

DESCRIPTION = "Compiles SPWN files into a standalone executable!"
VERSION = "1.0.0"

container_files = glob.glob("containers/*")
required_modules = open("requirements.txt", "r").read().split("\n")

setup(
	name="spwn-CMPL",
	version=VERSION,
	author="DexterHill",
	url="https://github.com/DexterHill0/spwn-CMPL",
	description=DESCRIPTION,
	license="MIT",
	python_requires=">=3.6",

	packages=find_packages(),
	install_requires=required_modules,
	data_files=[("spwn_cmpl/containers", container_files)],
	entry_points={"console_scripts": ["spwn-CMPL=spwn_cmpl.main:main"]},
)
