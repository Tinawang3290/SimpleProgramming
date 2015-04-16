from instruction import Instruction
from machine import Machine
import sys
import re

def parse_program(file_name, machine):
	program = {}
	with open(file_name) as f:
		count = 0
		for line in f:
			count += 1
			## ignore empty lines
			if not line.strip():
				continue
			## ignore comments
			if  line[0] == '#':
				continue
			m = re.search('\s*([0-9]+)\s*\:\s*([A-Z]{3})\s*(.*)', line)
			if not m:
				raise RuntimeError("Invalid syntax in file line number : %d" % count)
			line_num = int(m.group(1))
			instr_code = m.group(2)
			args = m.group(3).split()
			
			mlocs = []
			lnums = []
			consts = []
			try:
				for arg in args:
					if arg[0] == 'M':
						mlocs.append(int(arg[1:]))
					elif arg[0] == 'L':
						lnums.append(int(arg[1:]))
					else:
						consts.append(int(arg))

				instr = Instruction(machine, line_num, instr_code, mlocs, lnums, consts)
				program[line_num] = instr
			except:
				raise RuntimeError("Invalid syntax in file line number : %d" % count)
			
	return program

def main():
	if len(sys.argv) < 2 or len(sys.argv) > 3:
		print("To run: python run_program.py <program_file_name> <optional:debug>")
		sys.exit(0)

	debug = "no"
	if len(sys.argv) > 2:
		debug = sys.argv[2]
		
	m = Machine()
	# self, machine, code, mlocs, lnums, consts
	program = parse_program(sys.argv[1], m)
	m.execute(program, debug)
	print("Memory: ", m.mmap)
	
if __name__ == "__main__":
	main()