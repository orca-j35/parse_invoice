class Text():
    a = 1

    def funcname(self, aa=a):
        print(aa)


d = {'a': 1, 'b': 2}
for k, v in enumerate(d.items()):
    print(k, v)
try:
    max([])
except ValueError:
    print('dsda')
import re
r = re.compile(r'\wds')
print(r.pattern)

set(({1: 2}, {1: 3}))
