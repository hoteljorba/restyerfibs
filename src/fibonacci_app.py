#!/usr/bin/env python
# encoding:utf-8
"""
    fibonacci series generator with 
        restful interface
        xml or json response documents
    
    version; NA
    date: TBD
    author: bebo
    
    instead of using the method dispatcher, url pop, json tool, etc. decoratos
    i stuck with the direct, bare metals approach.
    
"""
import os, sys
reload(sys)
sys.setdefaultencoding('utf-8')

#for some reason, the recursion depth for the fib series going through
#cherrypy can be a lower value than the sys default, e.g. on the mac. 
#raising the limit a bit works but i need to give that a closer look
#as the undoutedly will come in handy some day
sys.setrecursionlimit(1100)

import json
import threading
from urlparse import urlparse
from datetime import datetime

try:
    import cherrypy
    if int(cherrypy.__version__[0]) != 3:
        print 'we\'d like to see cherrypy version 3ish.'
        sys.exit(errno.EINVAL)
except:
    print 'you need cherrypy. (sudo) pip install cherrypy and try again.'
    sys.exit(errno.ENOENT)

try:
    from lxml import etree
    if int(etree.__version__[0])!=3:
        print 'we\'d like to see etree version 3ish.'
        sys.exit(errno.EINVAL)
except:
    print 'you need lxml. (sudo) pip install lxml and try again.'
    sys.exit(errno.ENOENT)

#all this should come from a config file
local_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
xsd_path = os.path.join(parent_dir, 'xsd', 'fib.xsd')


mlock = threading.RLock()

header_data = {'contact': 'me', 'email':'me@example.com', 'phone': '+1 xxx yyy zzzz'}
header_order = ['contact', 'email', 'phone', 'date', 'requestIP', 'requestUrl', 
                'responseStatus','responseMsg', 'resultsCount']

class GlobalMemo(object):
    '''
        global memo dict
        
        should add a few improvments, such as admin access(get, load)
        and maybe make it an OrderedDict mixin. however, this really should
        be a Redit type storage and the class should wrap the access and admin
        methods.
    '''
    def __init__(self, memo_dict={0:0, 1:1}):
        '''
        '''
        self.memo = memo_dict
    
    
    def add(self, k, v):
        '''
            we lock/unlock and enforce "unique" index/key value
            with a (silent) on duplicate, do nothing
        '''
        mlock.acquire()
        if self.memo.get(k) is None:
            self.memo[k] = v
        mlock.release()
    
    
    def get(self, n, series=False):
        '''
            series  True - return the whole dict
                    False - return nth value
        '''
        if self.memo.get(n) is None:
            return None
            
        if series:
            return dict((k, self.memo.get(k)) for k in range(n+1))
        else:
            return self.memo[n]
    


class XmlMaker(object):
    '''
        there really wasn't much popint to use lxml to generate the xml strings
        but since we need xsd and validation tests, it seems a semi decent use 
        of that module. however, lxml has a lot of overhead compared to str 
        concatentation or even minidom. so it's probably nto advisable to use
        for a production service. also, the xml body strings, by index, should
        be persistet.
    '''
    def __init__(self, xsd_uri=None):
        '''
        '''
        self.xsi_uri = u'http://www.w3.org/2001/XMLSchema-instance'
        self.xsd_uri = u'%s'%(xsd_uri or'')
    
    
    def xmlHeader(self, header, header_dict):
        '''
        '''
        try:
            for h in header_order:
                k = u'%s'%h
                v = u'%s'%(header_dict.get(k) or '')
                value = etree.Element(k)
                value.text = v
                header.append(value)
                
            return True, 'ok'
        except Exception, e:
            msg = '%s'%e
            return False, msg
    
    
    def xmlBody(self, results, results_dict):
        '''
            a little hacky, we could have used a ordered dict but the overhead
            just doesn't seem to waarrent the order list creation
        '''
        try:
            order_index = results_dict.keys()
            order_index.sort()
        
            for k in order_index:
                value = etree.Element(u'value', index=u"%s"%k,)
                value.text = u'%s'%results_dict[k]
                results.append(value)
            
            return True, 'ok'
        except Exception, e:
            msg = ' lxml body creation failure for %s: %s'%(results_dict, e)
            return False, msg
    
    
    def run(self, header_dict, body_dict, output="str"):
        '''
            
        '''
        try:
            err_msg = str()
            
            nsmap = {'xsi': self.xsi_uri}
            ns_attr = {'{' + self.xsi_uri +'}schemaLocation': self.xsd_uri}
            xml_doc = etree.Element('FibonacciResults', nsmap=nsmap, attrib=ns_attr, version="0.0.1")
            header = etree.SubElement(xml_doc, 'header')
            results = etree.SubElement(xml_doc, 'fibonacci')
            
            state, data = self.xmlBody(results, body_dict)
            if not state:
                raise Exception(data)
            
            header_dict.update(header_data)
            state, data = self.xmlHeader(header, header_dict)
            if not state:
                raise Exception(data)
            
            if output.lower()=='str':
                return True, etree.tostring(xml_doc, xml_declaration=True, encoding='utf8')
                    
            return True, xml_doc
        except Exception, e:
            msg = '%s'%e
            return False, msg
    


class JsonMaker(object):
    '''
        format header and results dicts for a json response doc
    '''
    def __init__(self, ):
        '''
        '''
        self.n_header = u'header'
        self.n_results = u'fibonacci'
        self.n_k = u'index'
        self.n_v = u'value'
    
    
    def jsonHeader(self, header_dict):
        '''
            runnign in hader order to commit to a dict is not necessary
            but it helps in controlling response doc kv items and aids
            in the unicode conversions. why not.
        '''
        h_dict = dict()
        for k in header_order:
            h_dict[k] = u'%s'%(header_dict.get(k) or '')
        return h_dict
    
    
    def jsonBody(self, results_dict):
        '''
        '''
        body_list = list()
        for k,v in results_dict.items():
            body_list.append({self.n_k : k, self.n_v : v})
            
        return body_list
    
    
    def run(self, header_dict, results_dict):
        '''
        '''
        try:
            header_dict.update(header_data)
            d = dict()
            d[self.n_header] = self.jsonHeader(header_dict)
            d[self.n_results] = self.jsonBody(results_dict)
            return True, json.dumps(d)
        except Exception, e:
            msg = 'jsonMaker failure: %s'%e
            return False, msg
    


class FibonacciHandler(object):
    '''
        simple Fibonacci number generator using basic recursion and memoization 
        for series and Binet's formula for nth number approximation
        see, for example:
            http://en.wikipedia.org/wiki/Fibonacci_number
            http://en.literateprograms.org/Fibonacci_numbers_(Python)
        
    '''
    def __init__(self, max_n=998, memo={0:0, 1:1}, gMemo=None):
        '''
        max_n:  we set the max N to 998 to accomodate the python default
                recursion depth. we could write a generator- or eventlet-
                based method for n > max_n (or all claculations, for that 
                matter) to circumvent this issue
        gmemo:  use of a global memo cache for fib numbers. if None, we run a
                local memoization dict.
        '''
        self.max_n = max_n
        self.gMemo = gMemo
        self.memo_dict = memo
        self.memo = dict()
    
    
    def _fibNumber(self, n):
        '''
            for future development when a service is wanted to estimate
            the nth fibonacci number only
        '''
        return False, 'not implemented'
    
    
    def _fibSeries(self, n):
        '''
        '''
        if not self.gMemo or self.gMemo is None:
            if n not in self.memo:
                self.memo[n] = self._fibSeries(n-1) + self._fibSeries(n-2)
            return self.memo[n]
        else:
            if self.gMemo.get(n) is  None:
                v = self._fibSeries(n-1) + self._fibSeries(n-2)
                self.gMemo.add(n, v)
            return self.gMemo.get(n)
                
    
    
    def run(self, n, series=True):
        '''
            n:      
                fibonacci series up to the nth number
                    
            series: 
                if True, return the series of n fibonacci numbers,
                else, return the nth fibonacci number only
            
            return values:  
                tuple of method status,  True or False, and data or
                error message
        '''
        _status = False
        _data = None
        
        try:
            if n < 0:
                _status = False
                _data = 'invalid parameter, n, :%s'%n
            elif n > self.max_n:
                _status = False
                _data = 'this service limits the upper value of n to %s.'%self.max_n
            elif n == 0:
                _status = True
                _data = 0
                if series:
                    _data = {0:0}
            elif n == 1:
                _status = True
                _data = 1
                if series:
                    _data = {0:0, 1:1}
            else:
                try:
                    self.memo = self.memo_dict.copy()
                    self._fibSeries(n)
                    _status = True
                    if self.gMemo is None:
                        _data = self.memo
                    else:
                        _data = self.gMemo.get(n, series=True)
                except Exception, e:
                    _data = '_fib recusrion failure for n=%s: %s'%(n, e)
                    _status = False
        except Exception, e:
            _status = False
            _data = 'Fibonnacci Handler failure for n=%s: %s'%(n, e)
            
        
        finally:
            return _status, _data
    



class WebApp(object):
    '''
    '''
    out_formats = ['json', 'xml']
    xsd_version = '0.0.1'
    
    gH = GlobalMemo()
    
    def xsdUrl(self, ):
        '''
            with a decent config set up, would not need this but ...
        '''
        _version = self.xsd_version.replace('.', '/')
        o = urlparse(cherrypy.url())
        url = o.scheme + '://' + o.netloc + '/xml' + '/' + _version
        return url
    
    
    @cherrypy.expose
    def memo(self, *args):
        '''
            just GET for the time being
        '''
        d = dict()
        d['header'] = dict()
        d['memo'] = list()
        
        d['header']['date'] = u'%s'%datetime.now().date()
        
        if self.gH is None:
            d['header']['responseMsg'] = 'global memo is not in use'
        else:
            _memo = self.gH.memo.copy()
            d['header']['indexCount'] = len(_memo.keys())
            d['memo'] = [{'index':k, 'value':v} for k,v in _memo.items()]
            
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(d)
    
    
    @cherrypy.expose
    def xml(self, *args):
        '''
            since we don't have a versioning process in place, this is a static
            place holder for what could be dynamic uri's'
        '''
        if len(args)!=3:
            raise cherrypy.HTTPError(404, '%s not found'%cherrypy.url())
        
        req_version = '.'.join(args)
        if req_version!=self.xsd_version:
            msg = 'version "%s" not found'%req_version
            raise cherrypy.HTTPError(404, msg)
        
        if not os.path.exists(xsd_path):
            msg = 'xsd file %s is missing, please contact support.'
            raise cherrypy.HTTPError(404, msg%xsd_path)
        
        cherrypy.response.headers['Content-Type'] = 'text/xml'
        return open(xsd_path, 'rb').read()
    
    
    @cherrypy.expose
    def default(self, *args, **kwargs):
        '''
        '''
        results_header = dict()
        results_body = dict()
        stop = False
        
        results_header['date'] = u'%s %s'%(datetime.now().date(), datetime.now().time())
        results_header['requestUrl'] = cherrypy.url()
        results_header['requestIP'] = cherrypy.request.remote.ip
        results_header['responseMsg'] = str()
        
        while 1:
            if len(args)!=2 or args[0].lower()!='fibonacci' or not args[1].isdigit():
                msg = 'invalid url: %s\n'%cherrypy.url()
                results_header['responseMsg'] += msg
                results_header['responseStatus'] = 400
                break
            
            n = int(args[1])
            if n < 0 or n > 998:
                msg = 'invalid series index n =%s. valid range is: 0 < n < 999\n'%args[1]
                results_header['responseMsg'] += msg
                results_header['responseStatus'] = 400
                break
            
            status, data = FibonacciHandler(gMemo=self.gH).run(n)
            
            if not status:
                msg = data + '\n'
                results_header['responseMsg'] += msg
                results_header['responseStatus'] = 400
            else:
                results_header['responseStatus'] = 200
                results_header['resultsCount'] = len(data.keys())
                results_body = data.copy()
            
            break
        
        #html 5 clean up
        for k,v in kwargs.items():
            if not v or len(v)==0:
                kwargs[k] = None
        
        _alt = 'xml'
        if kwargs.get('alt') is not None:
            _alt = kwargs['alt']
        
        if _alt and _alt is not None and _alt.lower() not in self.out_formats:
            msg = '%s is not a valid format. use one of %s and default is xml.\n'
            vals = (_alt, ','.join(out_formats))
            header_results['responseMsg'] += msg%vals
            _alt = 'xml'
        
        doc = str()
        if _alt.lower()=='json':
            status, doc = JsonMaker().run(results_header, results_body)
            if not status:
                return cherrypy.HTTPError(400, 'doc')
            cherrypy.response.headers['Content-Type'] = 'application/json'
        else:
            xsd_uri = self.xsdUrl()
            
            status, doc = XmlMaker(xsd_uri).run(results_header, results_body)
            if not status:
                return cherrypy.HTTPError(400, 'doc')
            cherrypy.response.headers['Content-Type'] = 'text/xml'
        
        return doc
    

