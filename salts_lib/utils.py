import xbmc
from addon.common.addon import Addon

ADDON = Addon('plugin.video.salts')

def enum(**enums):
    return type('Enum', (), enums)

MODES=enum(MAIN='main', BROWSE='browse', TRENDING='trending', RECOMMEND='recommend', FRIENDS='friends', CAL='calendar', MY_CAL='my_calendar', LISTS='lists', SEARCH='search',
           SEASONS='seasons', EPISODES='episodes', GET_SOURCES='get_sources', MANAGE_SUBS='manage_subs', GET_LIST='get_list', SET_URL_MANUAL='set_url_manual', 
           SET_URL_SEARCH='set_url_search', SHOW_FAVORITES='browse_favorites', SHOW_WATCHLIST='browse_watchlist', PREMIERES='premiere_calendar', SHOW_LIST='show_list')
SECTIONS=enum(TV='TV', MOVIES='Movies')
VIDEO_TYPES = enum(TVSHOW='tvshow', MOVIE='movie', EPISODE='episode', SEASON='season')
TRAKT_SECTIONS = {SECTIONS.TV: 'shows', SECTIONS.MOVIES: 'movies'}

def log(msg, level=xbmc.LOGNOTICE):
    # override message level to force logging when addon logging turned on
    if ADDON.get_setting('addon_debug')=='true' and level==xbmc.LOGDEBUG:
        level=xbmc.LOGNOTICE
        
    try: ADDON.log(msg, level)
    except: 
        try: xbmc.log('Logging Failure', level)
        except: pass # just give up
