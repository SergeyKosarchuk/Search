from Stemmer import Stemmer
from .read import Reader
<<<<<<< HEAD
# from .snippets import Snippets
=======
from .snippets import Snippets
>>>>>>> 4789ac59c7dacae5b0d459968344c4c0cd343983


class Searcher:
    """ Класс для реализации поиска по готовым индексам.
        Содержит в себе булев, тфидф и поиск по заголовкам.
        Нужно добавить реализацию цитатного поиска. """


    # Отрицание  AND?
    def _and_invert(set_doc_id, set_inv_doc_id):
        if set_doc_id:
            return set_doc_id - set_inv_doc_id
        else:
            return invert(set_inv_doc_id)


    # Отрицание.
    def _invert(self, set_doc_id):
        return set(self.title_dict.keys()) - set_doc_id


    # Поиск по заголовкам.
    def _head(self, query):
        result = []
        for key,value in title_dict.items():
            if query in value.lower():
                result.append(key)
        return result


    # Цитатный поиск.
    def _quote(self, query):
        return


    # Булев поиск. Ну и реализация.. Кто так вообще программирует
    def _boolean(self, query):
        set_result = set()
        termins = query.split(' ')
        for termin in termins:
            temp = termin.split('%')
            if len(temp) > 1:
                if temp[0].startswith('!'):
                    set_and = _invert(Reader.block_for_termin_bool(temp[0][1:], self.token_dict))
                else:
                    set_and = Reader.block_for_termin_bool(temp[0], self.token_dict)
                i = 1
                while i < len(temp):
                    if temp[i].startswith('!'):
                        set_and = _and_invert(set_and, Reader.block_for_termin_bool(temp[i][1:], self.token_dict))
                    else:
                        set_and = set_and & Reader.block_for_termin_bool(temp[i], self.token_dict)
                    i += 1
                set_result = set_result | set_and
            else:
                if termin.startswith('!'):
                    set_result = set_result | _invert(Reader.block_for_termin_bool(termin[1:], self.token_dict))
                else:
                    set_result = set_result | Reader.block_for_termin_bool(termin, self.token_dict)
        return list(set_result)


    # Тфидф поиск.
    def _tfidf(self, query):
        dict_result = {}
        termins = query.split(' ')
        for termin in termins:
            termin = self.stemmer.stemWord(termin)
            Reader.block_for_termin_tfidf(termin, dict_result, self.title_dict, self.token_dict)
        list_result = sorted(dict_result.items(), key=lambda x: x[1], reverse=True)
        list_result = list(map(lambda x: x[0],list_result))
        return list_result

    def _prepare(self, result):
        answer = []
        snippets = self.st.Build(result)
        for id_ in result:
            art = Article(id_)
            art.title = self.title_dict[art.id]
            art.snippet = snippets[art.id]
            answer.append(art)
        return answer


    def __init__(self, reader):
        self.stemmer = Stemmer('russian')
        self.st = Snippets(reader.article_dict)
        self.title_dict = reader.title_dict
        self.token_dict = reader.token_dict
        self.switch = {
            'boolean': self._boolean,
            'tfidf': self._tfidf,
            'head': self._head
        }

    # Общая функция для поиска. Выбор поиска по его типу. Также здесь
    # логично будет добавить сниппеты к результатам. В будущем можно объединить
    # все выходные данные в один объект.
    def Search(self, type_, query, number=30):
        result = self.switch[type_](query)
        total = len(result)
        result = list(result[:number])
        result = self._prepare(result)
        return result, total


class Article:
    __slots__ = ('id', 'snippet', 'title')
    def __init__(self, id_):
        self.id = id_
