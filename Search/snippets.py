from json import loads
from pathlib import Path
from .read import Reader
from config import ARTICLE_INDEX, PATH, NAME_DIR_WITH_DAMPS

class Snippets:
    """ Класс для построения сниппетов. На данный момент работает загрузка
        докуменов по списку их ид. Также есть группировка файлов.
        Нужно реализовать пострение сниппетов по термину и его позиции. """

    article_dict = Reader.article_dict
    _p = Path(NAME_DIR_WITH_DAMPS)
    _directories = [x for x in _p.iterdir() if x.is_dir()]


    # Составляем словарь ид - текст (заголовок в тестовом режиме) статьи.
    @staticmethod
    def _load_articles(ids):
        d = {}
        files = Snippets._group_files(ids)
        for file_number, lines in files.items():
            file_ = Snippets._get_file(file_number)
            articles = Snippets._load_articles_from_file(file_, lines)
            d.update(articles)
        return d


    # Группируем файлы для исключения повторных открытий.
    # На выходе получаем сложный словарь.
    # Первый ключ - номер файла, второй ключ позиция статьи в нем.
    # Таким образом, перед открытием каждого файла мы знаем, какие именно
    # статьи нужно считать в память.
    @staticmethod
    def _group_files(ids):
        d = {}
        for id_ in ids:
            position = Snippets.article_dict.get(id_)
            if position:
                file_number, line = position[0], position[1]
                d[file_number] = d.get(file_number, {})
                if line not in d[file_number]:
                    d[file_number][line] = id_
            else:
                print("Id {} not found!".format(id_))
        return  d


    # Составляем имя требуемого файла по его номеру в индексе.
    @staticmethod
    def _get_file(file_number):
        directory_number = int(file_number / 100)
        file_number = file_number % 100
        if file_number > 10:
            file_number = str(file_number)
        else:
            file_number =  '0' + str(file_number)
        for i,d in enumerate(Snippets._directories):
            if i == directory_number:
                return str(d) + '/' + 'wiki_' + file_number


    # Функция для загрузки статей из файла по заданному порядку.
    def _load_articles_from_file(file_name, lines):
        articles = {}
        with open(file_name, encoding='utf-8') as f:
            for i,line in enumerate(f):
                if i in lines.keys():
                    article = loads(line)
                    id_ = lines[i]
                    articles[id_] = article['title']
                    # articles[id_] = article['text']
        return articles

    # Основная функция для построения сниппетов.
    # На данный момент показывает только заголовки. Для выбранных по ид статей.
    @staticmethod
    def Build(ids):
        answer = Snippets._load_articles(ids)
        return answer
