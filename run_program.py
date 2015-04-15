from instruction import Code, Instruction
from machine import Machine
import sys

def parse_program(file_name):
	program = {}
	with open(fname) as f:
		for line in f:
			print(line)
			
	return program

def main():
	if len(sys.argv) != 2:
		print("To run: python run_program.py <program_file_name>")
		sys.exit(0)
	
	m = Machine()
	# self, machine, code, mlocs, lnums, consts
	program = parse_program(sys.argv[1])
	program = {
		1: Instruction(m, 1, Code.SET, [1], [], [111]),
		2: Instruction(m, 2, Code.SET, [2], [], [100]),
		3: Instruction(m, 3, Code.MUL, [1,2,3], [], []),
	}
	m.execute(program)
	print("Memory: ", m.mmap)
	
if __name__ == "__main__":
	main()