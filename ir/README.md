# How to setup

1. install `elasticsearch` and `elasticsearch-dsl` via PIP
2. start elasticsearch on your computer WITHOUT security. Can be done by adding `xpack.security.enabled: false` to config/elasticsearch.yaml (assuming that you downloaded the client from https://www.elastic.co/downloads/elasticsearch)
3. if you have not previously, upload the [formatted_dataset.json](./formated_dataset.json) to elasticsearch and name it `new_news` (easy to do with kibana)
4. start the python program and search
