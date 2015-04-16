import math

class Instruction:
	def __init__(self, machine, thisline, code, mlocs, lnums, consts):
		self.machine = machine
		self.thisline = thisline
		self.code = code
		self.mlocs = mlocs
		self.lnums = lnums
		self.consts = consts
		
		self.instr_map = { 
			'ADD' : self._add,
			'SUB' : self._sub,
			'MUL' : self._mul,
			'DIV' : self._div,
			'GOT' : self._got,
			'IFE' : self._ife,
			'IFN' : self._ifn,
			'IFG' : self._ifg,
			'IFL' : self._ifl,
			'PUT' : self._put,
			'GET' : self._get,
			'COP' : self._cop,
			'SET' : self._set,
		}
			
	def execute(self):
		self.instr_map[self.code]()
			
	def _add(self):
		self.machine.mmap[self.mlocs[2]] = self.machine.mmap[self.mlocs[0]] + self.machine.mmap[self.mlocs[1]]

	def _sub(self):
		self.machine.mmap[self.mlocs[2]] = self.machine.mmap[self.mlocs[0]] - self.machine.mmap[self.mlocs[1]]

	def _mul(self):
		self.machine.mmap[self.mlocs[2]] = self.machine.mmap[self.mlocs[0]] * self.machine.mmap[self.mlocs[1]]

	def _div(self):
		self.machine.mmap[self.mlocs[2]] = math.floor(self.machine.mmap[self.mlocs[0]] / self.machine.mmap[self.mlocs[1]])

	def _got(self):
		self.machine.pc = self.lnums[0]
		
	def _ife(self):
		if self.machine.mmap[self.mlocs[0]] == self.machine.mmap[self.mlocs[1]]: 
			self.machine.pc = self.lnums[0]

	def _ifn(self):
		if self.machine.mmap[self.mlocs[0]] != self.machine.mmap[self.mlocs[1]]:
			self.machine.pc = self.lnums[0]

	def _ifg(self):
		if self.machine.mmap[self.mlocs[0]] > self.machine.mmap[self.mlocs[1]]:
			self.machine.pc = self.lnums[0]
	
	def _ifl(self):
		if self.machine.mmap[self.mlocs[0]] < self.machine.mmap[self.mlocs[1]]:
			self.machine.pc = self.lnums[0]
			
	def _put(self):
		self.machine.mmap[self.machine.mmap[self.mlocs[1]]] = self.machine.mmap[self.mlocs[0]]

	def _get(self):
		self.machine.mmap[self.machine.mmap[self.mlocs[1]]] = self.machine.mmap[self.mlocs[0]]

	def _cop(self):
		self.machine.mmap[self.mlocs[1]] = self.machine.mmap[self.mlocs[0]]

	def _set(self):
		self.machine.mmap[self.mlocs[0]] = self.consts[0]
