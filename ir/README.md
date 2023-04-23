# How to setup

1. install `elasticsearch` and `elasticsearch-dsl` via PIP
2. start elasticsearch on your computer WITHOUT security. Can be done by adding `xpack.security.enabled: false` to config/elasticsearch.yaml (assuming that you downloaded the client from https://www.elastic.co/downloads/elasticsearch)
3. if you have not previousy, upload the news dataset to elasticsearch and name it `news` (easy to do with kibana)
4. start the python program and search
