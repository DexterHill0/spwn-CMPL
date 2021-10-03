#![allow(non_snake_case)]
#![allow(unused_must_use)]

use std::env::{temp_dir, set_current_dir, args};
use std::path::PathBuf;
use std::fs::{File, metadata, remove_dir_all, create_dir};
use std::process::{Command, ExitStatus, Stdio, exit};
use std::time::{SystemTime, UNIX_EPOCH};
use std::io::{BufRead, Write, Read, ErrorKind, Seek, SeekFrom, stdin, stdout};

extern crate rev_buf_reader;
use rev_buf_reader::RevBufReader;

extern crate unzpack;
use unzpack::Unzpack;

//file extensions on different platforms
#[cfg(target_os = "windows")]
const SCRIPT_EXT: &str = "bat";
#[cfg(target_os = "windows")]
const EXE_EXT: &str = "exe";
#[cfg(target_os = "windows")]
const QUIET : &str = "@";

#[cfg(target_os = "linux")]
const SCRIPT_EXT: &str = "bash";
#[cfg(target_os = "linux")]
const EXE_EXT: &str = "";
#[cfg(target_os = "linux")]
const QUIET : &str = "";

#[cfg(target_os = "macos")]
const SCRIPT_EXT: &str = "command";
#[cfg(target_os = "macos")]
const EXE_EXT: &str = "";
#[cfg(target_os = "macos")]
const QUIET : &str = "";

const NAME: &str = "spwn-CMPL: ";
const ERROR: &str = "ERROR: ";
const WARN: &str = "WARN: ";
const INFO: &str = "INFO: ";

//panics in the spwn-CMPL style
macro_rules! cmpl_panic {
	($l: expr, $t: expr) => ( panic!("{}{}{}", NAME, $l, $t) );
}
//returns a handle that panics if there's an error (for `.unwrap_or_else`)
fn err<T, E>(level: &'static str, text: &'static str) -> impl FnOnce(E) -> T {
    move |_| { cmpl_panic!(level, text) }
}

fn main() {
	let args: Vec<String> = args().collect();

	//get ourself
	let FILE: &str = args.get(0).unwrap();

	//use the created date (in millis) to get a unique folder name between executables (but that is constant with the same executable)
	let created: SystemTime = metadata(FILE)
								.unwrap_or_else(err(ERROR, "File does not exist!")).created().unwrap();

	let full_name: String = format!("spwncmpl_{}", created.duration_since(UNIX_EPOCH)
								.unwrap()
								.as_millis()
								.to_string()).to_owned();
	let folder: PathBuf = temp_dir().join(&full_name);

	let mut exists: bool = false;

	match create_dir(&folder) {
		Ok(_) => {},
		//catch only the `AlreadyExists` error if it already exists
		Err(ref error) if error.kind() == ErrorKind::AlreadyExists => exists = true,
		Err(_) => cmpl_panic!(ERROR, "Failed to create directory!"),
	}

	set_current_dir(&folder).unwrap_or_else(err(ERROR, "Failed to change directory!"));

	//function to remove the current directory
	let clean_up = || {
		//go up into the temp directory
		set_current_dir("../");
		if remove_dir_all(&folder).is_err() { cmpl_panic!(WARN, "Unable to remove directory! (might have already been removed)") }
	};

	let mut one_time: bool = false;

    let mut args_iter = args.iter();
    args_iter.next();

    match &args_iter.next() {
        Some(a) => {
            match a as &str {
                "-o" | "--once" => {
					one_time = true;	
                }
                "-c" | "--clean" => {
					clean_up();
					exit(0);
                }
				_ => {}
			}
		}
		None => {}
	}

	let script_name = format!("start.{}", SCRIPT_EXT);

	//if the folder doesnt already exists this probably hasnt been executed before
	if !exists {
		//from now on we need to handle errors with the macro because the folder needs to be delete after an error
		//to avoid a corrupt "install"
		macro_rules! hndl {
			($e:expr, $err_handle: expr) => (match $e {
				Ok(val) => val,
				//first remove the folder, then panic
				Err(err) => { clean_up(); $err_handle(err) },
			});
		}

		let mut byte_vec: Vec<u8> = Vec::<u8>::new();
		let slf: File = hndl!(File::open(FILE), err(ERROR, "File does not exist!"));

		let mut rev_slf: RevBufReader<File> = RevBufReader::new(slf);
		
		let mut read_next_data = |vec: &mut Vec<u8>| {
			//remove previous data
			vec.clear();

			//read bytes into vector
			rev_slf.read_until(b'\0', vec);
		};

		let mut values: [u64; 2] = [0; 2];

		//use a loop to get the 3 int values
		for i in 0..2 {
			read_next_data(&mut byte_vec);

			let value = String::from_utf8_lossy(&byte_vec);
			values[i] = value.trim_end_matches('\0').parse::<u64>().unwrap();
		}

		let [exe_size, zip_size] = values;

		//just do the last one manually since it's a string
		read_next_data(&mut byte_vec);
		let args = String::from_utf8(byte_vec.clone())
								.unwrap_or_else(err(ERROR, "Failed to convert bytes! (corrupt file?)"));

		//dont need it anymore
		drop(byte_vec);

		//opens and writes data to a file
		let open_and_write = |filename: &str, data: &[u8]| {
			let mut file = hndl!(File::create(filename), err(ERROR, "Failed to create file!"));
			hndl!(file.write_all(data), err(ERROR, "Failed to create file!"));
		};

		//move back 1 character
		rev_slf.seek(SeekFrom::Current(-1));

		let mut buf: Vec<u8> = vec![0; zip_size as usize];

		//read & write zip data
		rev_slf.read_exact(buf.as_mut_slice()).unwrap();

		hndl!(Unzpack::unpack(buf.clone().leak(), "_.zip", "."), err(ERROR, "Failed to extract zip file!"));

		//resize to exe data
		buf.resize(exe_size as usize, 0);

		let exe_name = format!("run.{}", EXE_EXT);
		//read & write exe data
		rev_slf.read_exact(buf.as_mut_slice());
		open_and_write(&exe_name, &buf);

		//resize the buffer once more, fill the the command, and write
		//QUIET will disable the echoing of the command back to the output
		buf.resize(exe_name.len() + args.len() + 2, 0);
		buf.copy_from_slice(format!("{}{} {}", QUIET, &exe_name, args).as_bytes());
		open_and_write(&script_name, &buf);
	}

	//execute the scripts!
	let status = execute_spwn(&script_name);
	println!("{}{}{}{}", NAME, INFO, "Finished with exit code: ", status);

	//remove the directory if one time is enabled
	if one_time {
		clean_up();
	}

	//wait to exit
	pause();
	
	exit(0);
}

fn execute_spwn(command: &str) -> ExitStatus {
	//run command and redirect stdout
	return Command::new(command)
					.stdout(Stdio::inherit())
					.output()
					.unwrap_or_else(err(ERROR, "Failed to execute SPWN script(s)!")).status;
}

fn pause() {
	let mut stdin = stdin();
    let mut stdout = stdout();

	write!(stdout, "\nPress any key to continue...").unwrap();
    stdout.flush().unwrap();

    //read a single byte and discard
    stdin.read(&mut [0u8]).unwrap();
}