from flask import render_template,request
from Search import sh, app



@app.route('/')
def index():
    result = []
    query = request.args.get('search')
    if query:
        type_ = request.args.get('option', 'tfidf')
        result = sh.Search(type_, query)
        return render_template('index.html', result=result)
    return render_template('index.html')
