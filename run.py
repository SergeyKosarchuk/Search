from flask import Flask,render_template,request

from Search.search import Search

from Search.index import Build


app = Flask(__name__)

@app.route('/')
def index():
    result = []
    query = request.args.get('search')
    if query:
        type_ = request.args.get('option', 'tfidf')
        print('type = ',type_)
        result = Search.Search(type_, query)
        return render_template('index.html', result=result)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
