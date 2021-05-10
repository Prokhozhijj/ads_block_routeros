#!/usr/bin/python3

""" Copyright (c) 2021 Prokhozhijj
    Blocks AD domains on Mikrotik routers with RouterOS installed.
   
    https://github.com/Prokhozhijj/ads_block_routeros
   
    This is licensed under an MIT license. See the README.md
    file for more information.
"""


# Standard
from configparser import ConfigParser, ExtendedInterpolation
from typing import Set, List, Tuple
import urllib.request
import re
from os.path import getmtime
import os
from time import gmtime
from calendar import timegm
from pathlib import Path

# 3d party
import librouteros
from librouteros import connect
from librouteros.login import plain, token
from librouteros.query import Key, Or


class GlobalConfig(ConfigParser):
    """ Stores global system settings
    """
    
    if os.name == 'posix':
        config_file = os.path.join(os.sep + 'etc', 'ads_block_routeros.cfg')
    elif os.name == 'nt':
        config_file = os.path.join(os.getenv('ProgramData'),
                                   'ads_block_routeros',
                                   'ads_block_routeros.cfg'
                                  )
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
                     interpolation=ExtendedInterpolation(), 
                     *args,
                     **kwargs
                )
        self.read_file(open(GlobalConfig.config_file))

    @property
    def app_root_dir(self) -> str:
        """ Property. Returns root dir for the system
            
            Parameters
            ----------
            None
        
            Returns
            -------
            result : str
                    path where application resides
        """
        return os.path.join(self['COMMON']['app_root_dir'], '')
    
    @property
    def routers(self) -> List[str]:
        """ Property. Returns list of parameters names related to routers
        
            Parameters
            ----------
            None
            
            Returns
            -------
            result: List[str]
                list of parameters (like "router1" and so on)
        """
        return [k for k in list(self['COMMON'].keys()) if 'router' in k]
        
    def credentials(self, prouter:str) -> Tuple[str,str,str,str]:
        """ Returns login credentials for the given router
        
            Parameters
            ----------
            prouter: str
                router name, like "router1"
            
            Returns
            -------
            user:str
                user name
            password:str
                user's password
            IP: str
                router IP address
            method:str
                connection method to the router 
                ('plain' only in the current version)
        """
        cmn = 'COMMON'
        conn_str = self[cmn][prouter]
        user = conn_str.split('/')[0]
        password = conn_str.split('/')[1].split('@')[0]
        ip = conn_str.split('/')[1].split('@')[1].split(':')[0]
        # method = conn_str.split('/')[1].split('@')[1].split(':')[1]
        method = 'plain'
        return user, password, ip, method


def remove_garbage(pstr:str) -> str:
    """ Removes extra symbols from the given text
        
        Parameters
        ----------
        pstr: str
            given text to process
        
        Returns
        -------
        result: str
            processed text
    """
    result = pstr + '\n' if pstr[-1] != '\n' else pstr
    # comments
    result = re.sub('#.*\n', '', result)
    # tabs
    result = re.sub('\t+', '\n', result)
    # spaces in the row beginning
    result = re.sub('\n +', '\n', result)
    # two or more empty strings in a row
    result = re.sub('\n+', '\n', result)
    # first empty string
    result = re.sub('^\n', '', result)
    # last empty string
    result = re.sub('\n$', '', result)
    # some extra symbols
    result = re.sub('\r+', '', result)
    return result


def get_connection(  prouter_ip:str
                   , puser:str
                   , ppassword:str
                   , pmethod:str='plain'
                  ) -> librouteros.api.Api:
    """ Returns connection object to a router
        
        Parameters
        ----------
        prouter_ip: str
            router IP address
        puser: str
            router user
        ppassword: str
            user's password
        pmethod: str
            connection's type 
            see details in librouteros.login documentaion
            
        Returns
        -------
        result: librouteros.api.Api
            connection object to a router
    """
    if pmethod.lower() == 'plain': 
        method = plain
    connection = connect(username=puser,
                         password=ppassword,
                         host=prouter_ip,
                         login_method=method
                        )
    return connection


def get_static_domains_from_router(  pconnection: librouteros.api.Api
                                  ) -> Set[str]:
    """ Returns set with static domains from a router
    
        Parameters
        ----------
        pconnection: librouteros.api.Api
            connection object to a router
            
        Returns
        -------
        result: Set[str]
            set with static domains
            
    """
    name = Key('name')
    comment = Key('comment')
    result = set()
    for row in pconnection.\
               path('/ip/dns/static').\
               select(name):
        result.add(row['name'])
    return result


def get_cached_domains_from_router(  pconnection: librouteros.api.Api
                                  ) -> Set[str]:
    """ Returns set with cached domains from a router
    
        Parameters
        ----------
        pconnection: librouteros.api.Api
            connection object to a router
            
        Returns
        -------
        result: Set[str]
            set with cached domains
            
    """
    name = Key('name')
    type = Key('type')
    result = set()
    for row in pconnection.\
               path('/ip/dns/cache/all').\
               select(name).\
               where(Or(type == 'A',
                        type == 'CNAME'
                       )
                    ):
        result.add(row['name'])
    return result


def get_domains_from_url(purl:str) -> Set[str]:
    """ Returns set of domains obtained from the given URL
    
        Parameters
        ----------
        purl: str
            URL whith domains list
            
        Returns
        -------
        result: Set[str]
            set with domains
    """
    # get content
    with urllib.request.urlopen(purl) as response:
        domains = response.read()
    
    # remove garbage
    # comments
    domains = remove_garbage(domains.decode())
    # IP addresses
    domains = re.sub('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ ', '', domains)
    # spaces
    domains = re.sub(' +', '\n', domains) 
    # two or more empty strings in a row
    domains = re.sub('\n+', '\n', domains)
    # first empty string
    domains = re.sub('^\n', '', domains)
    # convert to set
    result = set(domains.split('\n'))
    
    return result


def get_domains_from_urls(purls:List[str]) -> Set[str]:
    """ Returns set of domains obtained from the given list of URLs
    
        Parameters
        ----------
        purl: List[str]
            list of URLs
            
        Returns
        -------
        result: Set[str]
            set with domains
    """
    result = set()
    for url in purls:
        result = result.union(get_domains_from_url(url))
    return result


def get_urls_from_file(pfile:str) -> List[str]:
    """ Returns list of URLs obtained from the given file
    
        Parameters
        ----------
        pfile: str
            full file name with URLs list
            
        Returns
        -------
        result: List[str]
            list of URLs
    """
    with open(pfile) as file:
        content = file.read()
    content = remove_garbage(content)
    result = content.split('\n')
    return result


def write_domains_to_file(pfile:str, pdomains:Set[str]) -> None:
    """ Writes set of domains to the given file
    
        Parameters
        ----------
        pfile: str
            full path to the file
        pdomains: Set[str]
            set of domains
        
        Returns
        -------
        None
    """
    print(f'Updating file {pfile}')
    Path(pfile).touch()
    with open(pfile, "w") as outfile:
        outfile.write("\n".join(pdomains))


def update_denied_domains_file(  
        pdomains_file:str
      , purls_file:str
      , ptime_diff:float=2.0 # refresh interval in hours
    ) -> None:
    """ Updates file with denied domains
    
        Parameters
        ----------
        pdomains_file: str
            full path to the file
        purls_file:str
            file with list of URLs where we can obtain domains list to block_domain
        ptime_diff:float (2.0 by default)
            how old file should be before being updated
            
        Returns
        -------
        None
    """
    # calculating difference between last time when file was modified
    # and the current time
    diff = None
    if os.path.isfile(pdomains_file):
        diff = (timegm(gmtime()) - getmtime(pdomains_file))/3600
    else:
        Path(pdomains_file).touch()
    if diff is None or diff > ptime_diff:
        urls = get_urls_from_file(purls_file)
        denied_domains = get_domains_from_urls(urls)
        write_domains_to_file(pdomains_file, denied_domains)


def get_domains_from_file(pfile:str) -> Set[str]:
    """ Obtains set of domains from the given file
    
        Parameters
        ----------
        pfile: str
            full path to the file
            
        Returns
        -------
        result: Set[str]
            set of domains
    """
    with open(pfile) as file:
        content = file.read()
    content = remove_garbage(content)
    result = set(content.split('\n'))
    return result


def get_domains_to_block(  pdd:Set[str] 
                         , psdr:Set[str]
                         , pcdr:Set[str]
                         , pda:Set[str] 
                        ) -> Set[str]:
    """ Obtains set of domains from the given file
    
        Parameters
        ----------
        pdd:Set[str]  
            denied domains from urls
        psdr:Set[str] 
            static domains
        pcdr:Set[str]
            cached domains
        pda:Set[str]
            allowed domains
            
        Returns
        -------
        result: Set[str]
            set of domains to block
    """
    dr = pcdr.difference(psdr) # cached - static
    dr = dr.difference(pda)    # (cached - static) - allowed
    result = dr.intersection(pdd)
    return result


def block_domain(  pconnection:librouteros.api.Api
                 , predirect_to_ip:str
                 , pdomain:str
                 , pcomment:str='ADBlock'
                ) -> None:
    """ Creates a rule on a router for redirecting domain to the given IP
    
        Parameters
        ----------
        pconnection:librouteros.api.Api
            connection object to a router
        predirect_to_ip: str
            IP address to redirect domain to
        pdomain:str
            domain to redirect to
        pcomment:str
            comment to a rule (ADBlock by default)
        
        Returns
        -------
        None
    """
    ip_dns_static = connection.path('ip', 'dns', 'static')
    ip_dns_static.add(address=predirect_to_ip,
                      comment=pcomment,
                      disabled='no',
                      name=pdomain
                     )
    return


def block_domains(  pconnection:librouteros.api.Api
                  , pdomains:Set[str]
                  , predirect_to_ip:str
                  , pcomment:str='ADBlock'
                 ) -> None:
    """ Creates set of rules on a router to redirect set of domains
        to the given IP
    
        Parameters
        ----------
        pconnection:librouteros.api.Api
            connection object to a router
        pdomains:Set[str]
            set of domains to redirect to
        predirect_to_ip:str
            IP address to redirect domains to
        pcomment:str
            comment to a rule (ADBlock by default)
        
        Returns
        -------
        None
    """
    for domain in pdomains:
        print('blocked: ', domain)
        block_domain(pconnection, predirect_to_ip, domain, pcomment)
    ip_dns_cache = connection.path('ip', 'dns', 'cache')
    tuple(ip_dns_cache('flush'))
    return


# read config file
gcfg = GlobalConfig()
gcfg_cmn = gcfg['COMMON']

# get values from config file
redirect_to_ip = gcfg_cmn['ip_to_redirect']
urls_file = gcfg_cmn['ads_blockers_urls_file']
denied_domains_file = gcfg_cmn['denied_domains_file']
allowed_domains_file_age = float(gcfg_cmn['allowed_domains_file_age'])
ads_comment = gcfg_cmn['ads_comment']

# update denied_domains_file if required
update_denied_domains_file(
      denied_domains_file
    , urls_file
    , allowed_domains_file_age
)

denied_domains = get_domains_from_file(denied_domains_file)

allowed_domains_file = gcfg_cmn['allowed_domains_file']
allowed_domains = get_domains_from_file(allowed_domains_file)

for router in gcfg.routers:
    user, password, router_ip, method = gcfg.credentials(router)
    print('\nprocessing router:', router_ip)
    # print(user, password, redirect_to_ip, method)
    try:
        connection = get_connection(router_ip, user, password)
    except Exception as error:
        print(error)
        continue
    cached_domains = get_cached_domains_from_router(connection)
    static_domains = get_static_domains_from_router(connection)
    domains_to_block = get_domains_to_block(
                           denied_domains,
                           static_domains,
                           cached_domains,
                           allowed_domains
                       )
    block_domains(connection, domains_to_block, redirect_to_ip, ads_comment)
