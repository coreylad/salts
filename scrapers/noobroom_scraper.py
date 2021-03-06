"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import scraper
import re
import urllib
import urllib2
import urlparse
import xbmcaddon
import xbmc
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES
from salts_lib.constants import USER_AGENT

BASE_URL = 'http://superchillin.com'

class NoobRoom_Scraper(scraper.Scraper):
    base_url=BASE_URL
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout=timeout
        self.db_connection = DB_Connection()
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))
        self.username = xbmcaddon.Addon().getSetting('%s-username' % (self.get_name()))
        self.password = xbmcaddon.Addon().getSetting('%s-password' % (self.get_name()))
        self.include_paid = xbmcaddon.Addon().getSetting('%s-include_premium' % (self.get_name())) == 'true'
   
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    @classmethod
    def get_name(cls):
        return 'NoobRoom'
    
    def resolve_link(self, link):
        url = urlparse.urljoin(self.base_url, link)
        html = self._http_get(url, cache_limit=.5)
        match = re.search('"file"\s*:\s*"([^"]+)', html)
        if match:
            file_link = match.group(1)
            stream_url = urlparse.urljoin(self.base_url, file_link)
            self._set_cookies(self.base_url, {})
            request = urllib2.Request(stream_url)
            request.add_header('User-Agent', USER_AGENT)
            request.add_unredirected_header('Host', request.get_host())
            request.add_unredirected_header('Referer', url)
            response = urllib2.urlopen(request)
            return response.geturl()
    
    def format_source_label(self, item):
        label='[%s] (%s) %s (%s/100) ' % (item['quality'], item['res'], item['host'], item['rating'])
        return label
    
    def get_sources(self, video):
        source_url=self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
                    
            has_1080p=False
            match = re.search('Watch in 1080p', html)
            if match:
                has_1080p=True
            
            if video.video_type == VIDEO_TYPES.MOVIE:
                quality = QUALITIES.HD
            else:
                quality = QUALITIES.HIGH
                
            for match in re.finditer("class='hoverz'.*?href='([^']+)'>([^<]+)\s+\(([^)]+).*?>(\d+)%", html, re.DOTALL):
                url, host, status, load = match.groups()
                if not self.include_paid and status.upper()=='PAID':
                    continue
                
                url = url.replace('&amp;', '&')
                host = '%s (%s)' % (host, status)
                hoster = {'multi-part': False, 'host': host, 'class': self, 'url': url, 'quality': quality, 'views': None, 'rating': 100 - int(load), 'direct': True, 'res': '720p'}
                if quality== QUALITIES.HD:
                    hoster['res']='720p'
                else:
                    hoster['res']='480p'
                hosters.append(hoster)
                
                if self.include_paid and has_1080p:
                    url += '&hd=1'
                    hoster = {'multi-part': False, 'host': host, 'class': self, 'url': url, 'quality': QUALITIES.HD, 'views': None, 'rating': 100 - int(load), 'direct': True, 'res': '1080p'}
                    hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(NoobRoom_Scraper, self)._default_get_url(video)
    
    def _get_episode_url(self, show_url, video):
        episode_pattern = "%sx%02d\s*-\s*.*?href='([^']+)" % (video.season, int(video.episode))
        title_pattern="\d+x\d+\s*-\s*.*?href='([^']+)'>([^<]+)"
        return super(NoobRoom_Scraper, self)._default_get_episode_url(show_url, video, episode_pattern, title_pattern)
        
    def search(self, video_type, title, year):
        if not self.include_paid and video_type != VIDEO_TYPES.MOVIE: return []
        search_url = urlparse.urljoin(self.base_url, '/search.php?q=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=.25)
        results=[]
        if video_type == VIDEO_TYPES.MOVIE:
            pattern = '<i>\s*Movies\s*</i>(.*)'
        else:
            pattern = '<i>\s*TV Series\s*</i>(.*)'

        match = re.search(pattern, html)
        if match:
            container = match.group(1)
            pattern = "href='([^']+)'>([^<]+)\s*</a>\s*(?:\((\d{4})\))?"
            for match in re.finditer(pattern, container):
                url, match_title, match_year = match.groups('')
                if not year or not match_year or year == match_year:
                    result = {'url': url, 'title': match_title, 'year': match_year}
                    results.append(result)
            
        return results
    
    @classmethod
    def get_settings(cls):
        settings = super(NoobRoom_Scraper, cls).get_settings()
        name=cls.get_name()
        settings.append('         <setting id="%s-username" type="text" label="     Username" default="" visible="eq(-6,true)"/>' % (name))
        settings.append('         <setting id="%s-password" type="text" label="     Password" option="hidden" default="" visible="eq(-7,true)"/>' % (name))
        settings.append('         <setting id="%s-include_premium" type="bool" label="     Include Premium" default="false" visible="eq(-8,true)"/>' % (name))
        return settings
    
    def _http_get(self, url, data=None, cache_limit=8):
        # return all uncached blank pages if no user or pass
        if not self.username or not self.password:
            return ''
         
        html=super(NoobRoom_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
        if not re.search('href="logout.php"', html):
            log_utils.log('Logging in for url (%s)' % (url), xbmc.LOGDEBUG)
            self.__login()
            html=super(NoobRoom_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=0)
        
        return html

    def __login(self):
        url = urlparse.urljoin(self.base_url, '/login2.php')
        data = {'email': self.username, 'password': self.password}
        html = super(NoobRoom_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=0)
        if not re.search('href="logout.php"', html):
            raise Exception('noobroom login failed')
