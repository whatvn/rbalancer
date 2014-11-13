rbalancer
============
* This thing is deprecated, please use my py-balancer, it does the samething, but much faster, and easier.


*rbalancer is a simple HTTP load balancer using HTTP 302 redirect response with round-robin and weighted random support built on* ``tornado``.
*rbalancer can perform health check on server in balancer list, when a server went down, rbalancer will automatic re-balance request to alive servers.*
*When dead one goes up, it will be added to cluster and serving request likes normal* 

Example usage
============
If you have a farm servers to serve static file, and you want to load balancing between them, of course just once you have problem with LVS ldirector, (We used to have 3 LVS server to load balance our video streaming farm, when switching to rbalancer, we just need one 2 cores server with 200 MB ram usage)  rbalancer will be your right choice.

Rbalancer server has original domain: img.org.domain.cdn.com, a img file on your site will have url img.org.domain.cdn.com/img/front_shadow.jpeg. 

You have 2 servers behind rbalancer to serv that jpeg file which have following domain names:

- server 1 : img1.org.domain.cdn.com
- server 2 : img2.org.domain.cdn.com 

Base on weigh of each server your defined in configuration file, rbalancer will balance request to server 1, or server 2 with a redirect response like this:


REQUEST (to rbalancer) 

::
    
    GET /img/front_shadow.jpeg HTTP/1.1
    Host: img.org.domain.cdn.com

RESPONSE (from rbalancer) 

::

    HTTP/1.1 302 Found
    Location: img1.org.domain.cdn.com/img/front_shadow.jpeg 


you can also view stats of rbalancer using URL: http://rbalancer_domain_name/stats . Stats of rbalancer shows how much request each server in cluster receive, how many requests/s it's serving, which servers was down. 


Usage
=====

rbalancer.conf
-----------------

``rbalancer.conf`` is by default placed in ``/etc`` if the package was intalled with root privileges. rbalancer itself can run as non root user which bind to high port. By default, rbalancer will run on port ``9998``.

::

    [global]
    port = 9998              # Listening port.
    static_dir=/var/www/

    [farms]
    list=stc,img 

    ; config for ``img`` farm 
    [img]
    list=srv1,srv2
    domain=img.org.domain.cdn.com   ;original domain 

    [srv1] 
    domain=http://img1.org.domain.cdn.com
    weight=20
    enable=on

    [srv2]
    domain=http://img2.org.domain.cdn.com
    weight=10
    enable=on


    ; config for ``stc`` farm
    [stc] 
    list=srv3,srv4
    domain=stc.org.domain.cdn.com

    [srv3] 
    domain=http://img1.org.domain.cdn.com
    weight=10
    enable=on
    [srv4]
    domain=http://img2.org.domain.cdn.com
    weight=10
    enable=off

Server was configured with ``enable=off`` will not receive request from rbalancer untill it is turned on. 

``Final note``: you should put your favicon.ico in static folder configure in configuration file. Every http request made to your server will look for a favicon file. 
In my test case, a 404 Not Found response costs 8ms when a 302 Redirect response just costs 0.03ms. It meant if you dont have favicon.ico file, it will take 8.03ms to serve a request. I will let you do the math. 


Installation
============

*See below for OS-specific preparations.*

Install *rbalancer* with:

::

    # python setup.py install 

- Modify and rename /etc/rbalancer.conf.default to /etc/rbalancer.conf 

- Start rbalancer 

::

    # /etc/init.d/rbalancer start 



License
=======
`GPL <http://www.gnu.org/licenses/gpl-3.0.txt>`_
