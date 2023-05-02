from newscatcher import Newscatcher
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup


## To install newscatcher, run the following commands in the terminal: 
# pip install feedparser --upgrade
# python newsPack/setup.py install


newsPages = {'nbcnews.com': 'article-body__content', 'vox.com': 'c-entry-content', 'edition.cnn.com':'article__content-container'}

def get_text_news(link, div):
    r1 = requests.get(link)
    r1.status_code

    coverpage = r1.content

    soup1 = BeautifulSoup(coverpage, 'html5lib')
    coverpage_news = soup1.find('div', class_=div)
    text = coverpage_news.get_text()
    textSplit = text.split("\n")

    bad =[]

    for text in textSplit:
        if(len(text) == 0):
            bad.append(text)
        elif('()' in text or '{' in text or '}' in text or ';' in text):
            bad.append(text)

    for text in bad:
        textSplit.remove(text)

    #join the list
    text = ' '.join(textSplit)
    return text


## Call this function to update the dataset.json file with new articles

def read_new_articles(path='formated_dataset.json'):
    links = []
    data = []
    with open(path) as json_file:
        for obj in json_file:
            dic = json.loads(obj)
            data.append(dic)
            links.append(dic['link'])

    for site, div in newsPages.items():
        nc = Newscatcher(website=site)
        result = nc.get_news()
        for article in result['articles']:
            if article['link'] not in links:
                tags = []
                if 'tags' in article:
                    for tag in article['tags']:
                        tags.append(tag['term'])

                authors = []
                if 'authors' in article:
                    for author in article['authors']:
                        if 'name' in author:
                            authors.append(author['name'])

                if 'summary' in article:
                    summary = article['summary']
                else:
                    summary = ''

                if 'published_parsed' in article:
                    date = article['published_parsed']
                else:
                    date = ''

                if article['link'] not in links:
                    if 'video' in article['link'] or 'live-news' in article['link'] or 'audio' in article['link']:
                        continue
                    else:
                        try:
                            text = get_text_news(article['link'], div)
                        except:
                            text = ''

                        # remove all the newlines in text and headline
                        text = text.replace('\n', ' ')
                        article['title'] = article['title'].replace('\n', ' ')

                        data.append({'link': article['link'], 'headline': article['title'], 'text': text, 'tags': tags, 'summary': summary, 'authors': authors, 'date': date})


    with open(path, 'w') as outfile:
        for obj in data:
            json.dump(obj, outfile)
            outfile.write('\n')


if __name__ == "__main__":
    read_new_articles()