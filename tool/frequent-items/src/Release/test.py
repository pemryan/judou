#coding:utf-8
from pyzlcl import Lcl

#0.001 是要统计的频率下限
lcl = Lcl(0.001)

for i in xrange(2000):
    for j in xrange(1000):
        lcl.update(i,1)

for i in xrange(200):
    lcl.update(i,-1)

for i in xrange(1,100,30):
    print i
    print "出现的次数(估计值)",lcl.est(i)
    print "estimate the worst case error in the estimate of a particular item :" ,lcl.err(i)
    print "---"*20

result = lcl.output(1000)
result.sort(key=lambda x:-x[1])
print result

print lcl.capacity()

