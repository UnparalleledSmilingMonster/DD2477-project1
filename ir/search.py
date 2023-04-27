from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MoreLikeThis

import json


def query(preferences_categories: dict) -> Q:
    search_query = input("Enter search query: ")
    should_list = []
    must_not_list = []
    for key, value in preferences_categories.items():
        if value > 2:  # TODO decide when we can assume that the user likes an category
            should_list.append(Q("match", tags=key))
        elif value < -3:  # and same for dislikes
            must_not_list.append(Q("match", tags=key))

    return Q('bool',
             must=[Q('match', headline=search_query)],
             should=should_list,
             # this will not be used if we just have positive (implicit) feedback
             must_not=must_not_list,
             minimum_should_match=0
             )


def recommendation(reading_history: list) -> Q:
    q = Q()
    print(q)
    for i, id in enumerate(reading_history):
        if i == 0:
            q = Q(MoreLikeThis(like={"_index": "new_news", "_id": id.strip()}, fields=[
                  "tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1))
        else:
            q |= Q(MoreLikeThis(like={"_index": "new_news", "_id": id.strip()}, fields=[
                   "tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1))
    print(q)
    return q


def main():
    reading_history = []  # We should limit this somehow if it is big
    with open("history.txt") as f:
        for id in f:
            reading_history.append(id.strip())

    with open('categories.json') as json_file:
        preferences_categories: dict = json.load(json_file)
    # the idea is that the number corresponds to how many articles that the user (dis-)liked with that category.
    # we can probably do the same with author and make two ints for length(should probably just be used for recommendation without query)

    # Create the client instance
    client = Elasticsearch(
        "http://localhost:9200"
    )

    choice = int(
        input("Do you want to search(1) or get news recommendations(2)?\n"))
    if (choice == 1):
        q = query(preferences_categories)
    else:
        q = recommendation(reading_history)

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

    print(reading_history)
    with open("history.txt", "w") as f:
        for id in reading_history:
            f.write("%s\n" % id)


if __name__ == "__main__":
    main()
