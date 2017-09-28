from flask import Flask

from .search import Searcher
from .read import Reader


app = Flask(__name__)
rd = Reader()
sh = Searcher(rd)


from . import views
