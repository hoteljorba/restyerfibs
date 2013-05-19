#!/usr/bin/env python
# encoding:utf-8
"""
    just a wrapper to set up and kick-off the web app
    
    we should/could use a config file, mysql table, or mongodb collection
    to set this up but for the sake of max portability and and ease of deployment
    we go with hardcoding
"""
import os, sys
reload(sys)
sys.setdefaultencoding('utf-8')

import errno
import logging
import logging.handlers as handlers

try:
    from src.fibonacci_app import cherrypy, WebApp
except Exception, e:
    print 'module import failure: %s'%e
    sys.exit(errno.ENOENT)


LOG_MAX_BYTES = 1000000
MAX_LOGS = 10
CFG_FNAME = 'cp.cfg'

LOCAL_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
LOG_DIR = os.path.join(LOCAL_DIR, 'logs')

def main():
    '''
        a little hacky but it'll do until we igure out the production environment,
        e.g. a set of instances behind nginx reverse proxy or a wsgi instance, such as
        uWSGI, behind nginx or, the heavens forbid, behind apache
        
    '''
    try:
        
        e_log_fname = 'error.log'
        a_log_fname = 'access.log'
    
        log = cherrypy.log
        log.error_file = ''
        log.access_file = ''
        maxBytes = getattr(log, "rot_maxBytes", LOG_MAX_BYTES)
        backupCount = getattr(log, "rot_backupCount", MAX_LOGS)
        
        fname = getattr(log, "rot_%s_file"%'error', os.path.join(LOG_DIR, e_log_fname))
        h = handlers.RotatingFileHandler(fname, 'a', maxBytes, backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(cherrypy._cplogging.logfmt)
        log.error_log.addHandler(h)
        
        fname = getattr(log, "rot_%s_file"%'access', os.path.join(LOG_DIR, a_log_fname))
        h = handlers.RotatingFileHandler(fname, 'a', maxBytes, backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(cherrypy._cplogging.logfmt)
        log.access_log.addHandler(h)
        
        cfg_path = os.path.join(LOCAL_DIR, CFG_FNAME)
        if not os.path.exists(cfg_path):
            print 'config file missing'
            return
        else:
            cherrypy.config.update('cp.cfg')
        
        
        
        cherrypy.quickstart(WebApp(), )
    
    except Exception, e:
        print e


if __name__=='__main__':
    main()