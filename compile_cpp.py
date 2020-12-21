import subprocess
import os

def compile_cpp(code, exe_fname='build/a.out', src_fname='build/tmp.cpp', run=True):
	subprocess.run(['mkdir', '-p', 'build'])
	with open(src_fname, 'w') as src_file:
		src_file.write('\n'.join(code))
	error = subprocess.run(['g++', src_fname, '-o', exe_fname]).returncode
	if not error:
		completedProcess = subprocess.run([exe_fname], universal_newlines=True, stdout=subprocess.PIPE)
		print(completedProcess.stdout)
	print('rtn:', error)
