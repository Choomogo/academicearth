'''
    academicearth.scraper
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains some functions which do the website scraping for the
    API module. You shouldn't have to use this module directly.
'''
import re
from urllib2 import urlopen
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup as BS


BASE_URL = 'http://www.academicearth.org'
def _url(path):
    '''Returns a full url for the given path'''
    return urljoin(BASE_URL, path)


def get(url):
    '''Performs a GET request for the given url and returns the response'''
    conn = urlopen(url)
    resp = conn.read()
    conn.close()
    return resp


def _html(url):
    '''Downloads the resource at the given url and parses via BeautifulSoup'''
    return BS(get(url), convertEntities=BS.HTML_ENTITIES)


def make_showall_url(url):
    '''Takes an api url and appends info to the path to force the page to
    return all entries instead of paginating.
    '''
    if not url.endswith('/'):
        url += '/'
    '''return url + 'page:1/show:500' '''
    return url


def get_subjects():
    '''Returns a list of subjects for the website. Each subject is a dict with
    keys of 'name' and 'url'.
    '''
    '''url = _url('subjects')'''
    url = _url('online-college-courses')
    html = _html(url)
    article = html.article
    subjs = article.findAll('a')

    # subjs will contain some duplicates so we will key on url
    items = []
    urls = set()
    for subj in subjs:
        url = _url(subj['href'])
        if url not in urls:
            urls.add(url)
            items.append({
                'name': subj.string,
                'url': url,
            })

    # filter out any items that didn't parse correctly
    return [item for item in items if item['name'] and item['url']]


def get_subject_metadata(subject_url):
    '''Returns metadata for a subject parsed from the given url'''
    html = _html(make_showall_url(subject_url))
    name = get_subject_name(html)
    courses = get_courses(html, subject_url=subject_url)
    lectures = get_lectures(_html(subject_url))
#     lectures = []
#     lectures += [course['lectures'] for course in courses]
    desc = get_subject_description(html)

    return {
        'name': name,
        'courses': courses,
        'lectures': lectures,
        'description': desc,
    }


def get_subject_name(html):
    return html.find('article').h1.text


def get_course_name(html):
    return html.find('section', {'class': 'pagenav'}).span.text


def get_lecture_name(html):
    return html.find('section', {'class': 'pagenav'}).span.text


def get_subject_description(html):
#     desc_nodes = html.find('article').findAll('span')
    desc_nodes = html.find('div', {'itemprop': 'description'})
#     return '\n'.join(node.text.strip() for node in desc_nodes)
    joined = '\n'.join(str(node.string) for node in desc_nodes)
    return joined

'''deprecated'''
def _get_courses_or_lectures(class_type, html):
    '''class_type can be 'course' or 'lecture'.'''
    nodes = html.findAll('div', {'class': class_type})

    items = [{
        'name': node.h3.text,
        'url': _url(node.a['href']),
        'icon': node.img['src'],
        #'university':  '',
        #'speaker': '',
    } for node in nodes]

    return items

# '''Working! Don't touch this!'''
def get_lectures(html, course_name=None):
#     '''Stores concatenated list of all found lectures.'''
    lectures = []

#     '''The number and order of 'lectures-list' will be equivalent to amount of courses'''
    lecture_lists = html.findAll('div', {'class': 'lectures-list'})

#     '''Iterates through each lecture-list pulling relevant data for each lecture
#         into a data structure.'''
    for lecture_list in lecture_lists:
        lecture_list = lecture_list.findAll('li')
        items = [{
                  'name': lecture.article.h4.text,
                  'url': lecture.a['href'],
                  'icon': lecture.a.img['src'],
#                   'instructor': lecture.find('span', {'class': 'video-instructor'}).text,
#                   'length': lecture.find('span', {'class': 'video-length'}).text
                  } for lecture in lecture_list]

#         '''Adds lectures found in current lecture-list to the previously collected lectures'''
        lectures += items

#     '''If course_name is defined, all lectures found will be filtered to only
#         include lectures that correspond to defined course_name.'''
    if course_name != None:
        lectures = filter(lambda x: not course_name in x['name'], lectures)

    return lectures


def get_courses(html, subject_url=None):
    nodes = html.findAll('article', {'class': 'course-details'})

    items = [{
          'name': node.h3.text,
          'url': subject_url,
          'lectures': get_lectures(html, course_name=node.h3.text)
          } for node in nodes]

    return items


def get_course_metadata(course_url, course_name):
    html = _html(course_url)
    lectures = get_lectures(html, course_name)
#     name = get_course_name(html)
    return {
        'lectures': lectures,
        'name': course_name
    }


def get_lecture_metadata(lecture_url, course_name):
    html = _html(lecture_url)
    name = get_lecture_name(html)
    youtube_id = parse_youtube_id(html)
    return {
        'name': name,
        'youtube_id': youtube_id
    }



def parse_youtube_id(html):
    embed = html.find('embed')
    yt_ptn = re.compile(r'http://www.youtube.com/v/(.+?)\?')
    match = yt_ptn.search(embed['src'])
    if match:
        return match.group(1)
    return None
