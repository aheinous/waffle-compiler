class _FuncPush:
	def __init__(self, call_stack):
		self._call_stack = call_stack
	def __enter__(self):
		pass
	def __exit__(self, exc_type, exc_val, exc_tb):
		self._call_stack._pop()

class CallStack:
	def __init__(self):
		self._stack = []

	def push(self, func):
		self._stack.append(func)
		return _FuncPush(self)

	def _pop(self):
		self._stack.pop()

	def peek(self):
		return self._stack[-1]


