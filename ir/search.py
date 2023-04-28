from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MoreLikeThis
from math import asin, pi

import json


def query(preferences_categories: dict) -> Q:
    search_query = input("Enter search query: ")
    should_list = []
    for key, value in preferences_categories.items():
        if value > 2:
            should_list.append(Q("match", tags=key))

    return Q('bool',
             must=[Q('match', headline=search_query)],
             should=should_list,
             minimum_should_match=0
             )


def recommendation(reading_history: list) -> Q:
    q = Q()  # TODO filter dates to get recent articles
    for i, id in enumerate(reversed(reading_history)):
        if i == 0:
            q = Q(MoreLikeThis(like={"_index": "new_news", "_id": id.strip()}, fields=[
                  "tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1, boost=pi/2-asin(i/len(reading_history))))  # TODO maybe have another scoring function
        else:
            q |= Q(MoreLikeThis(like={"_index": "new_news", "_id": id.strip()}, fields=[
                   "tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1, boost=pi/2-asin(i/len(reading_history))))
    return q


def main():
    reading_history = []
    with open("history.txt") as f:
        for id in f:
            reading_history.append(id.strip())

    with open('categories.json') as json_file:
        preferences_categories: dict = json.load(json_file)
    # we can probably do the same with author and make two ints for length(should probably just be used for recommendation without query)

    client = Elasticsearch(
        "http://localhost:9200"
    )

    choice = int(
        input("Do you want to search(1) or get news recommendations(2)?\n"))
    if (choice == 1):
        q = query(preferences_categories)
    else:
        q = recommendation(reading_history)

    # will only produce ten results, we can use scan() to get more: https://stackoverflow.com/questions/53729753/how-to-get-all-results-from-elasticsearch-in-python
    s = Search(using=client, index="new_news").query(q)

    response = s.execute()
    print("The top", len(response), "results are")
    for index, hit in enumerate(response):
        print("----")
        print(str(index), "("+hit.meta.id+")" + ":", hit.meta.score,
              "Title:", hit.headline, hit.tags, "Written by:", hit.authors)

    article_index = int(input("Which article do you want to read? "))

    print(response[article_index].text)

    for tag in response[article_index].tags:
        if tag in preferences_categories:
            preferences_categories[tag] += 1
        else:
            preferences_categories[tag] = 1
    reading_history.append(response[article_index].meta.id)

    with open("categories.json", "w") as outfile:
        json.dump(preferences_categories, outfile)

    with open("history.txt", "w") as f:
        for id in reading_history:
            f.write("%s\n" % id)


if __name__ == "__main__":
    main()
