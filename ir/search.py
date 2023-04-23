from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
# TODO: Look into if MoreLikeThis works better
from elasticsearch_dsl.query import MoreLikeThis

# TODO: read dict from file

# the idea is that the number corresponds to how many articles that the user (dis-)liked with that category.
# we can probably do the same with author
preferences_categories = {
    "POLITICS": 1,
    "ENTERTAINMENT": 7,
    "SPORTS": -7
}

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
        should_list.append(Q("match", category=key))
    elif value < -3:  # and same for dislikes
        must_not_list.append(Q("match", category=key))

q = Q('bool',
      must=[Q('match', headline=search_query)],
      should=should_list,
      must_not=must_not_list,
      minimum_should_match=0
      )
s = Search(using=client, index="news").query(q)
'''
s = Search(using=client, index="news").query(
    "match", headline=search_query).query(
    MoreLikeThis(like='SPORTS', fields=['category']))  # .exclude()
'''
response = s.execute()

print("The top", len(response), "results are")
for index, hit in enumerate(response):
    print("----")
    print(str(index) + ":", hit.meta.score,
          "Title:", hit.headline, "\n Description: ", hit.short_description, hit.category)

article_index = int(input("Which article do you want to read? "))

print(response[article_index].link)

# TODO let the user score results and save to the dict
