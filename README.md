# Short description
Blocks AD domains on Mikrotik routers with RouterOS installed.
   
# How it works
Script checks router's DNS cache and compares it with allowed and denied domain names. If new domain to block is found, script adds it into the static domains list (IP -> DNS -> Static) and binds it to an IP address which is specified by value of parameter `ip_to_redirect` in the config file. Then script flushes router's DNS cache.
      
Domain names to block are obtained from URLs which are located in the file with a name specified by a value of `ads_blockers_urls_file` parameter in the config file. The script caches obtained denied domain names in the file specified by value of `denied_domains_file` parameter in the config file and checks cached file for its freshness within interval
specified by value of parameter `allowed_domains_file_age` in the config file. If the file is not expired, it won't be updated.
      
If you want to exclude some domain names from blocking you need to place their list in a file which is specified by value of `allowed_domains_file` parameter in the config file.
      
This script can maintain several routers. All you need is just to add them into the config file.
   
# How to use

Using the script is very simple:

- download the script with provided templates to any folder on your host;

For example:

~~~sh
cd your_scripts_folder
git clone https://www.github.com/prokhozhijj/ads_block_routeros
~~~

- open access to the Internet for this host;
- install Python 3.6 or later;
- install 3d party modules (see Requirements section for details);

For example:
~~~shell
pip install -U librouteros
~~~

- enable `api` on a router (menu IP -> Services) for a host on which the script is located;

- create a file with a list of allowed domain names (they won't be blocked by the script under no circumstances);

- create a file with a list of URLs of ADs blocking providers;

- create config file `ads_block_routeros.cfg` from template in the proper folder (see below) and fill it with your values:

    - for Windows the folder is:
    ~~~shell
    %ProgramData%\ads_block_routeros\
    ~~~
    - for Linux the folder is:
    ~~~shell
    /etc/
    ~~~

- start the script without arguments;
- enjoy.

The script was tested under MS Windows 10 only but should work under any posix like OS as well.

# Requirements 
- Python 3.6 or later;
- `librouteros` python module;
- RouterOS 6.48 or later (earlier versions were not tested but the scipt may work with them as well);
- enabled `api` in IP -> Services on a router for the host with the script.

# License

The MIT License (MIT)

Copyright (c) 2021 Prokhozhijj

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.TION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
