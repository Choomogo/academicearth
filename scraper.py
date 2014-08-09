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
    html = _html(subject_url)
    name = get_subject_name(html)
    courses = get_courses(subject_url)
    desc = get_subject_description(html)

    return {
        'name': name,
        'courses': courses,
        'lectures': [],
        'description': desc,
    }


def get_subject_name(html):
    return html.find('article').h1.text


def get_course_name(html):
    return html.find('section', {'class': 'pagenav'}).span.text


def get_lecture_name(html):
    return html.find('span', {'id': 'eow-title'}).text


def get_subject_description(html):
    desc_nodes = html.find('div', {'itemprop': 'description'})
    joined = '\n'.join(str(node.string) for node in desc_nodes if node.string != None)
    return joined

# Working! Don't touch this!
def get_lectures(html, course_name=None):
#     Stores concatenated list of all found lectures.
    lectures = []

#     The number and order of 'lectures-list' will be equivalent to amount of courses
    lecture_lists = html.findAll('div', {'class': 'lectures-list'})

#     Iterates through each lecture-list pulling relevant data for each lecture
#     into a data structure.
    for lecture_list in lecture_lists:
        lecture_list = lecture_list.findAll('li')
        items = [{
                'name': lecture.article.h4.text,
                'url': lecture.a['href'],
                'icon': lecture.a.img['src'],
                'instructor': lecture.find('span', {'class': 'video-instructor'}).text,
                'length': lecture.find('span', {'class': 'video-length'}).text
                  } for lecture in lecture_list]

        lectures += items

#     If course_name is defined, all lectures found will be filtered to only
#     include lectures that correspond to defined course_name.
    if course_name != None:
        lectures = filter(lambda x: not course_name in x['name'], lectures)

    return lectures

def get_courses(subject_url):
    page1 = _html(subject_url)
    pages = [page1]

    page_numbers = page1.findAll('a', {'class': 'page-numbers'})
    if page_numbers != None:
        pages += [_html(subject_url + a['href']) for a in page_numbers]

    course_previews = []
    for page in pages:
        course_previews += page.findAll('li', {'class': 'course-preview'})

    courses = [{
                'name': course_preview.article.h3.a.text,
                'url': subject_url,
                'lectures': get_lectures_from_preview(course_preview)
                } for course_preview in course_previews if course_preview.article != None]
    return courses


def get_lectures_from_preview(course_preview):
    lecture_lists = course_preview.findAll('li', {'class': 'lecture-preview'})

    lectures = [{
                'name': lecture_list.article.h4.text,
                'url': lecture_list.a['href'],
                'icon': lecture_list.a.img['src'],
                'instructor': lecture_list.find('span', {'class': 'video-instructor'}).text,
                'length': lecture_list.find('span', {'class': 'video-length'}).text
                  } for lecture_list in lecture_lists]
    return lectures

def get_course_metadata(course_url, course_name):
    html = _html(course_url)
    lectures = get_lectures(html, course_name)

    return {
        'lectures': lectures,
        'name': course_name
    }


def get_lecture_metadata(lecture_url):
    html = _html(lecture_url)
    name = get_lecture_name(html)
#     youtube_id = parse_youtube_id(html)
    youtube_id = parse_youtube_id(lecture_url)
    return {
        'name': name,
        'youtube_id': youtube_id
    }

def parse_youtube_id(lecture_url):
    return lecture_url.split('v=')[1]

