Overview

Restful web service to obtain Fibonacci series.

Usage

Point your http client or browser to http://your_sever_host:your_sever_port/fibonacci/n where n is an integer 0<= n < 999.  By default, corresponding fibonacci series stream as a xml document. Please note that only POST and GET are implemented which, for the purpose of this service instance, are treated interchangeably.

The app affords additional options with the following parameters:
  
	alt=json:	returns a json document instead of the default xml document.
				see json_example.txt for document details
           	   	e.g. ../fibonacci/n?alt=json

The server also services the corresponding xsd document at http://your_sever_host:your_sever_port/xml/x/y/z/fab.xsd
where x, y, and z are the version increments ...


Note that most input or processing errors are captured in the response document. Hence, you need to pay attention to the 'responseMsg' and 'responseStatus' values in the 'header' section of the response document. Unfortunately, at this time not all possible response errors are presented this way. The complete capture of response errors and message mapping to the specified response content format remains to be completed. Also, the corresponding response error messages should be mapped to a maybe a numerical schema and an associated api via a restful web service. e.g., ./api/version/error_id maps into the actual message.


Performance Considerations

The xml is currently generated with lxml, which is a poor production choice with respect to overhead. It is used since a xsd validation test was needed. For any type of significant production environment, it is advisable to persist both xml and json result bodies. A possible my/nosql schema could look like this:

 	fib_index	fib_value	xml_segement		dict_segment
	  int			int		unicode str			pickled list of dicts

and extend memoization to the response document layer.

Due to the implemented recursion constraint on n, response stream (buffer) sizes are not going to be an issue. For large n, however, one needs to consider the maxint limit as well as the streaming/buffering approach. In fact, it may make sense to look at combining buffer management with a generator approach for large response documents. Another, and possibly complementary, option is to split responses into subsets and use "pagination" links in the response document to provide the user with the corresponding uri's. that in turn, allows a user to parallelize the download of said response docs.


Misc. Tid-Bits

There are a few options currently not exposed and plenty of improvements to be had. Please see the code. Of most interest might be the availability of a global memoization dict which should be extended to persist to redis, memcached, or even mysql as it complements the response document caching outlined above. As is, persistence is in app space ram for the duration of server uptime.


Under ordinary circumstances, each request generates a new, user-specific creation of a memoization dict, which is rather inefficient.
To this end, a global solution was implemented using RLock ... without serialization to a persistence layer, such as redis, mongodb, or mysql, the data only persists during the wep app's uptime. of course

The fib calculator functionality was implemented object-style, which in turn runs within each of the app server thread, or as a global instance accessed by each of the app server threads, memoization persistence can also be attained. However, this is not a particularly clean or scalable approach. Hence, the provision for a global, thread-safe, and extendable data object.

As a quick hack, set the gh to None or  in the initialization section of the WebApp class.