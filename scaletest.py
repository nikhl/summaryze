import urllib2
import thread
import time

def call_api(tname,delay):
	time.sleep(delay)
	p = urllib2.urlopen('http://summaryze.appspot.com/api/allreviews.xml')
	response_code = p.getcode()
	print '%s response code is %d' % (tname,response_code)

try:
	for i in range(10):
		thread.start_new_thread( call_api, ("Thread-"+str(i+1),0) )
except OSError,e:
   print e.reason

while 1:
   pass