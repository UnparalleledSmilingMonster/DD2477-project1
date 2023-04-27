from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
# TODO: Look into if MoreLikeThis works better
from elasticsearch_dsl.query import MoreLikeThis

import json

with open('categories.json') as json_file:
    preferences_categories: dict = json.load(json_file)
# the idea is that the number corresponds to how many articles that the user (dis-)liked with that category.
# we can probably do the same with author and make two ints for length(should probably just be used for recommendation without query)

# Create the client instance
client = Elasticsearch(
    "http://localhost:9200"
)


# q = (Q("match", category="SPORTS") | Q("match", category="ENTERTAINMENT"))
search_query = input("Enter search query: ")
should_list = []
must_not_list = []
for key, value in preferences_categories.items():
    if value > 2:  # TODO decide when we can assume that the user likes an category
        should_list.append(Q("match", tags=key))
    elif value < -3:  # and same for dislikes
        must_not_list.append(Q("match", tags=key))

q = Q('bool',
      must=[Q('match', headline=search_query)],
      should=should_list,
      # this will not be used if we just have positive (implicit) feedback
      must_not=must_not_list,
      minimum_should_match=0
      )
# s = Search(using=client, index="new_news").query(q)


# This can be the reccomendation service, only thing we need to add is that the date should be near today.
s = Search(using=client, index="news").query(
    MoreLikeThis(like={"_index": "new_news", "_id": "a8ravYcB2gD1FxEPMjHL"}, fields=[
                 "tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1)
    | MoreLikeThis(like={"_index": "new_news", "_id": "lsravYcB2gD1FxEPKShd"}, fields=["tags", "authors", "headline"], min_term_freq=1, min_doc_freq=1))


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

with open("categories.json", "w") as outfile:
    json.dump(preferences_categories, outfile)

# TODO let the user score results and save to the dict
