from json import loads
from pathlib import Path
from .read import Reader
from config import ARTICLE_INDEX, PATH, NAME_DIR_WITH_DAMPS

class Snippets:
    """ Класс для построения сниппетов. На данный момент работает загрузка
        докуменов по списку их ид. Также есть группировка файлов. """

    def __init__(self, article_dict, stemmer):
        self.stemmer = stemmer
        self.article_dict = article_dict
        self.p = Path(NAME_DIR_WITH_DAMPS)
        self.directories = [x for x in self.p.iterdir() if x.is_dir()]


    # Составляем словарь ид - текст (заголовок в тестовом режиме) статьи.
    def _load_articles(self, ids):
        d = {}
        files = self._group_files(ids)
        for file_number, lines in files.items():
            file_ = self._get_file(file_number)
            articles = self._load_articles_from_file(file_, lines)
            d.update(articles)
        return d


    # Группируем файлы для исключения повторных открытий.
    # На выходе получаем сложный словарь.
    # Первый ключ - номер файла, второй ключ позиция статьи в нем.
    # Таким образом, перед открытием каждого файла мы знаем, какие именно
    # статьи нужно считать в память.
    def _group_files(self, ids):
        d = {}
        for id_ in ids:
            position = self.article_dict.get(id_)
            if position:
                file_number, line = position[0], position[1]
                d[file_number] = d.get(file_number, {})
                if line not in d[file_number]:
                    d[file_number][line] = id_
            else:
                print("Id {} not found!".format(id_))
        return  d


    # Составляем имя требуемого файла по его номеру в индексе.
    def _get_file(self, file_number):
        directory_number = int(file_number / 100)
        file_number = file_number % 100
        if file_number > 10:
            file_number = str(file_number)
        else:
            file_number =  '0' + str(file_number)
        for i,d in enumerate(self.directories):
            if i == directory_number:
                return str(d) + '/' + 'wiki_' + file_number


    # Функция для загрузки статей из файла по заданному порядку.
    def _load_articles_from_file(self, file_name, lines):
        articles = {}
        with open(file_name, encoding='utf-8') as f:
            for i,line in enumerate(f):
                if i in lines.keys():
                    article = loads(line)
                    id_ = lines[i]
                    # articles[id_] = article['title']
                    articles[id_] = article['text']
        return articles


    # Функция для получения контекста слова из текста.
    # Пока работает только для одного слова.
    def _get_context(self, text, termin, n=10):
        text = text.replace('"См. также: "','')
        text = text.split()
        snippet = ''
        for pos, word in enumerate(text):
            word = word.lower().strip(",'.!")
            word = self.stemmer.stemWord(word)
            if word == termin:
                break
        # Можно добавить гибкие границы для красоты и информативности.
        # Также стоит добавить пометку для выделения слова курсивом.
        start = pos - n
        end = pos + n + 1
        snippet = snippet + ' '.join(text[start:pos] + text[pos:end])
        return snippet


    # Основная функция для построения сниппетов.
    # На данный момент показывает только заголовки.
    # На вход получает словарь (ид -> позиция).
    def Build(self, ids, query):
        """ Id -> snippet dictionary. """
        articles = self._load_articles(ids)
        snippets = {}
        for id, text in articles.items():
            snippets[id] = self._get_context(text, query)
        return snippets
