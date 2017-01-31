# nginx tweaks

## turn off http

On my fedora I did the following in `/etc/nginx/nginx.conf`

That is, redirect all the http traffix to https, and delete default http entry points.


```
root@thermals /etc/nginx # diff nginx.conf.rpm nginx.conf
38,42c38,43
<     server {
<         listen       80 default_server;
<         listen       [::]:80 default_server;
<         server_name  _;
<         root         /usr/share/nginx/html;
---
> server {
> 	listen 80 default_server;
> 	listen [::]:80 default_server;
> 	server_name _;
> 	return 301 https://$host$request_uri;
> }
44,57c45,64
<         # Load configuration files for the default server block.
<         include /etc/nginx/default.d/*.conf;
<
<         location / {
<         }
<
<         error_page 404 /404.html;
<             location = /40x.html {
<         }
<
<         error_page 500 502 503 504 /50x.html;
<             location = /50x.html {
<         }
<     }
---
```