# __init__.py
from .gatherJournals import get_sparql_results, build_sparql_query
from .downloadFromOpenAlex import request_works
from .preprocessing import filter_eu_articles, filter_keywords, flatten_works, get_authors, get_single_authors, get_eu_authors