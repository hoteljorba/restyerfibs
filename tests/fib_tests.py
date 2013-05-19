#!/usr/bin/env python
# encoding:utf-8
"""
    basic and somehwat incomplete unittests for the fibonacci web service
"""
import os, sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import lxml
import unittest
import threading
from random import randrange
from urlparse import urlparse
from datetime import datetime

try:
    import cherrypy
except:
    print 'cherrypy is needed'
    sys.exit()

try:
    from lxml import etree
except:
    print 'lxml required'
    sys.exit()

try:
    import requests
except:
    print ' requests module requried'
    sys.exit()

local_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
xsd_path = os.path.join(parent_dir, 'xsd', 'fib.xsd')

sys.path.append(parent_dir)

from src.fibonacci_app import GlobalMemo, FibonacciHandler, XmlMaker, JsonMaker, WebApp



class GlobalMemoTests(unittest.TestCase):
    '''
    '''
    def setUp(self,):
        '''
        '''
        self.gM = GlobalMemo
        self.valid_fibs = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5, 6:8, 7:13, 8:21, 9:34}
        self.max_threads = 10
        
    
    
    def testInit(self, ):
        '''
        '''
        gM = self.gM({0:0, 1:1})
        self.assertEqual(gM.memo, {0:0, 1:1})
        del gM
    
    
    def testAdd(self,):
        '''
            we only run tests for adding a new and an existing key-value pair
            since this is "just" a persitance layer, we don't check on the validity
            of k-v pairs.
            
            we also need to test the lock/release functionality
        '''
        gM = self.gM({0:0, 1:1})
        for k,v in self.valid_fibs.items():
            gM.add(k,v)
        
        self.assertEqual(gM.memo, self.valid_fibs)
        
    
    
    def testAddThreadedFixed(self, ):
        '''
        '''
        gM = self.gM({0:0, 1:1})
        threads = list()
        
        for i in range(self.max_threads):
            t = threading.Thread(target=gM.add, args=(0, i))
            t.start()
            threads.append(t)
            
        [t.join() for t in threads]
        
        self.assertEqual(gM.memo, {0:0, 1:1})
    
    
    def testAddThreadedSeries(self,):
        '''
        '''
        gM = self.gM({0:0, 1:1})
        threads = list()
        fnum = len(self.valid_fibs.keys())
        
        for i in range(fnum-1, -1, -1):
            t = threading.Thread(target=gM.add, args=(i,self.valid_fibs[i]))
            t.start()
            threads.append(t)
            
        [t.join() for t in threads]
        
        self.assertEqual(gM.memo, self.valid_fibs)
    
    
    def testGetDict(self):
        '''
        '''
        gM = self.gM(self.valid_fibs)
        n = len(self.valid_fibs.keys())
        _series = True
        
        self.assertEqual(gM.get(n, _series), None)
        
        self.assertEqual(gM.get(n-1, _series), self.valid_fibs)
    
    
    def testGetNumber(self,):
        '''
        '''
        gM = self.gM(self.valid_fibs)
        _series = False
        
        for k, v in self.valid_fibs.items():
            self.assertEqual(gM.get(k, _series), v)
    


class FibonacciTest(unittest.TestCase):
    '''
    '''
    def setUp(self):
        '''
        '''
        self.base_fibs = {0:0, 1:1}
        self.valid_fibs = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5, 6:8, 7:13, 8:21, 9:34}
    
    
    def testFibHandlerInit(self):
        '''
        '''
        _max_n = 100
        _gmemo = None
        _memo = self.base_fibs
        fH = FibonacciHandler(max_n=_max_n, memo=_memo, gMemo=_gmemo)
        
        #self.assertEqual(fH.memo, {})
        #self.assertEqual(fh.max_n, )
        
    
    
    def testFibNumber(self,):
        '''
            that method is not implemented so we want the test to reflect that
        '''
        fH = FibonacciHandler()
        self.assertEqual(fH._fibNumber(None), (False, 'not implemented'))    
    
    
    def testFibSeriesLMemo(self,):
        '''
            test with local memo
            the way the class is set up, we need to prime the
            memo dict direcctly
        '''
        for k, v in self.valid_fibs.items():
            fH = FibonacciHandler()
            fH.memo = {0:0, 1:1}
            self.assertEqual(fH._fibSeries(k), v)
    
    
    def testFibSeriesGMemo(self):
        '''
            test with global memo
        '''
        gM = GlobalMemo(memo_dict=self.base_fibs)
        for k, v in self.valid_fibs.items():
            fH = FibonacciHandler(gMemo=gM)
            self.assertEqual(fH._fibSeries(k), v)
        
        self.assertEqual(gM.memo, self.base_fibs)
    
    
    def testFibRunBoundries(self):
        '''
        '''
        lower_bad_n = -1
        upper_bad_n = 999
        lower_good_n = 0
        upper_good_n = 998
        
        
        gM = GlobalMemo(memo_dict=self.base_fibs)
        self.assertFalse(FibonacciHandler().run(lower_bad_n)[0])
        self.assertFalse(FibonacciHandler(gMemo=gM).run(lower_bad_n)[0])
        
        self.assertFalse(FibonacciHandler().run(upper_bad_n)[0])
        self.assertFalse(FibonacciHandler(gMemo=gM).run(upper_bad_n)[0])
        
        self.assertTrue(FibonacciHandler().run(lower_good_n)[0])
        self.assertTrue(FibonacciHandler(gMemo=gM).run(lower_good_n)[0])
        
        self.assertTrue(FibonacciHandler().run(lower_good_n)[0])
        self.assertTrue(FibonacciHandler(gMemo=gM).run(lower_good_n)[0])
        
    
    
    def testFibRunValids(self):
        '''
        '''
        for k, v in self.valid_fibs.items():
            fH = FibonacciHandler()
            s, d = fH.run(k)
            self.assertTrue(s)
            self.assertEqual(d[k], self.valid_fibs[k])
    
    


class XmlMakerTest(unittest.TestCase):
    '''
        we need the xsd file, need to accommodate versioning which is NOT taken
        care of here. keep that in mind.
    '''
    def setUp(self, ):
        '''
        '''
        self.valid_fibs = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5, 6:8, 7:13, 8:21, 9:34}
        self.header_data = {'contact': 'me', 'email':'me@example.com', 
                            'phone': '+1 xxx yyy zzzz'}
    
    
    def testXMLMakerRun(self):
        '''
            only testing for the core features requried for the project at hand
            at the very least makign sure all the extra features making the core
            kaputt
        '''
        self.assertTrue(os.path.exists(xsd_path))
        self.header_data['resultsCount'] = len(self.valid_fibs.keys())
        status, xml_str = XmlMaker().run(self.header_data, self.valid_fibs)
        self.assertTrue(status)
        
        xsd_str = etree.parse(open(xsd_path, 'rb'))
        xmlSchema = etree.XMLSchema(xsd_str)
        xml_doc = etree.fromstring(xml_str)
        
        self.assertEqual(xmlSchema.assertValid(xml_doc), None)
        
        h_list = xml_doc.find('header')
        b_list = xml_doc.find('fibonacci')
        
        h_dict = dict()
        b_dict = dict()
        
        for e in h_list:
            if e.text and e.text is not None:        
                h_dict[e.tag] = e.text
                
        self.assertEqual(len(h_dict), len(self.header_data))
        
        for e in b_list:
            if e.text and e.text is not None:
                b_dict[int(e.attrib['index'])] = int(e.text)
        
        self.assertEqual(len(b_dict), len(self.valid_fibs))
        
        for k, v in h_dict.items():
            self.assertEqual(str(self.header_data.get(k)), v)
            
        for k, v in b_dict.items():
            self.assertEqual(self.valid_fibs.get(k), v)
    


class JsonMakerTest(unittest.TestCase):
    '''
        short and sweet
    '''
    def setUp(self, ):
        '''
        '''
        self.valid_fibs = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5, 6:8, 7:13, 8:21, 9:34}
        self.header_data = {'contact': 'me', 'email':'me@example.com', 
                            'phone': '+1 xxx yyy zzzz'}
    
    
    
    def testRunTrue(self, ):
        '''
        '''
        status, doc = JsonMaker().run(self.header_data, self.valid_fibs)
        self.assertTrue(status)
        self.assertTrue(type(doc), json)
        body_list = json.loads(doc)['fibonacci']
        header_dict = json.loads(doc)['header']
        
        for k,v in header_dict.items():
            if self.header_data.get(k) is not None:
                self.assertEqual(v, self.header_data[k])
        
        for value_dict in body_list:
            k = value_dict['index']
            v = value_dict['value']
            self.assertEqual(self.valid_fibs[k], v)
            
            
    
    
    def testRunFalse(self, ):
        '''
        '''
        status, doc = JsonMaker().run(['no', 'valid', 'type'], ['also', 'false'])
        self.assertFalse(status)
        
    


class WebAPPTest(unittest.TestCase):
    '''
        those are static tests. for dynamic tests, we need to
        have cherrypy running, need a client, 
    '''
    def setUp(self, ):
        '''
        '''
        self.base_url = 'http://127.0.0.1:8080'
        self.valid_fibs = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5, 6:8, 7:13, 8:21, 9:34}
    
    
    def testXsdServeStale(self):
        '''
            basic xsd retrieval tests
        '''
        app = WebApp()
        
        self.assertEqual(app.xml(*('0','0','1')), open(xsd_path, 'rb').read())
        
        expected_xsd_path = '/xml/0/0/1'
        url = app.xsdUrl()
        o = urlparse(url)
        self.assertEqual(o.path, expected_xsd_path)
    
    
    def testRestServiceStale(self, ):
        '''
            testing for basic boundary conditions only; some in json
            some in xml
        '''
        app = WebApp()
        response_doc = app.default(*('fibonacci', '999'), **{'alt':'json'})
        response_dict = json.loads(response_doc)
        self.assertNotEqual(response_dict['header']['responseStatus'], '200')
    
    
    def testRestServiceLive(self, ):
        '''
        '''
        lower_limit_url = self.base_url + '/fibonacci' + '/-1'
        upper_limit_url = self.base_url + '/fibonacci' + '/999'
        fail_urls = [lower_limit_url, upper_limit_url]
        
        lower_bound_url = self.base_url + '/fibonacci' + '/0'
        upper_bound_url = self.base_url + '/fibonacci' + '/5'
        valid_fibs_url = self.base_url + '/fibonacci' + '/10'
        success_urls = [lower_bound_url, upper_bound_url, valid_fibs_url ]
        
        for url in fail_urls:
            r = requests.get(url)
            xml_doc = etree.fromstring(r.text.encode(r.encoding))
            hdr = xml_doc.find('header')
            rStatus = hdr.find('responseStatus')
            self.assertNotEqual(rStatus.text, '200')
            
        for url in success_urls:
            r = requests.get(url)
            xml_doc = etree.fromstring(r.text.encode(r.encoding))
            hdr = xml_doc.find('header')
            status = hdr.find('responseStatus')
            self.assertEqual(status.text, '200')
    


def main():
    unittest.main(verbosity=2)


if __name__=='__main__':
    main()