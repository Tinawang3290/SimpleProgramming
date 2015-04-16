class Machine:
	def __init__(self):
		self._reset()

	def _reset(self):
		self.mmap = {}
		self.pc = 0
		
	def execute(self, program, debug):
		if len(program) == 0:
			print("*** Empty program ***")
			return
		
		ordered_lnums = sorted(program.keys())
		reverse_index = dict(zip(ordered_lnums, range(len(program))))
		last_line = ordered_lnums[-1]

		lnums_loc =  0
		self.pc = ordered_lnums[0]
		while(True):
			old_pc = self.pc
			try:
				program[self.pc].execute()
			except:
				print("Error in line number %d" % old_pc)
				raise
							
			if old_pc == self.pc:
				if old_pc == last_line:
					break
				lnums_loc += 1
				self.pc = ordered_lnums[lnums_loc]
			else:
				if self.pc > last_line:
					break
				if self.pc in reverse_index:
					lnums_loc = reverse_index[self.pc]
				else:
					raise RuntimeError("When executing line %d, can't branch to non-existant"
							" line %d" % (old_pc, self.pc))

			if debug == 'debug':
				print (old_pc, self.mmap)

		print("*** End of program execution ***")
