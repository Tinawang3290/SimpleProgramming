from enum import Enum, unique

@unique
class Code(Enum):
	ADD = 1
	SUB = 2
	MUL = 3
	DIV = 4
	GOT = 5
	IFE = 6
	IFN = 7
	IFG = 8
	IFL = 9
	PUT = 10
	GET = 11
	COP = 12
	SET = 13
	
class Instruction:
	def __init__(self, machine, thisline, code, mlocs, lnums, consts):
		self.machine = machine
		self.thisline = thisline
		self.code = code
		self.mlocs = mlocs
		self.lnums = lnums
		self.consts = consts
		
		self.instr_map = { 
			Code.ADD : self._add,
			Code.SUB : self._sub,
			Code.MUL : self._mul,
			Code.DIV : self._div,
			Code.GOT : self._got,
			Code.IFE : self._ife,
			Code.IFN : self._ifn,
			Code.IFG : self._ifg,
			Code.IFL : self._ifl,
			Code.PUT : self._put,
			Code.GET : self._get,
			Code.COP : self._cop,
			Code.SET : self._set,
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
		self.machine.mmap[self.mlocs[2]] = self.machine.mmap[self.mlocs[0]] / self.machine.mmap[self.mlocs[1]]

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
