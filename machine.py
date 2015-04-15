class Machine:
	def __init__(self):
		self._reset()

	def _reset(self):
		self.mmap = {}
		
	def execute(self, program):
		if len(program) == 0:
			print("*** Empty program ***")
			return
		
		ordered_lnums = sorted(program.keys())
		reverse_index = zip(ordered_lnums, range(len(program)))
		last_line = ordered_lnums[-1]

		lnums_loc =  0
		pc = ordered_lnums[0]
		while(True):
			old_pc = pc
			try:
				program[pc].execute()
			except:
				print("Error in line number %d" % old_pc)
				raise
							
			if old_pc == pc:
				if old_pc == last_line:
					break
				lnums_loc += 1
				pc = ordered_lnums[lnums_loc]
			else:
				if pc > last_line:
					break
				if pc in reverse_index:
					lnums_loc = reverse_index[pc]
				else:
					raise RuntimeError("When executing line %d, can't branch to non-existant"
							+ "line %d" % (old_pc, pc))
		
		print("*** End of program execution ***")

