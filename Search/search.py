from Stemmer import Stemmer
from .read import Reader


class Search:
    """ Класс для реализации поиска по готовым индексам.
        Содержит в себе булев, тфидф и поиск по заголовкам.
        Нужно добавить реализацию цитатного поиска. """


    stemmer = Stemmer('russian')
    title_dict = Reader.title_dict
    token_dict = Reader.token_dict


    # Отрицание  AND?
    def _and_invert(set_doc_id, set_inv_doc_id):
        if set_doc_id:
            return set_doc_id - set_inv_doc_id
        else:
            return invert(set_inv_doc_id)


    # Отрицание
    @staticmethod
    def _invert(set_doc_id):
        return set(Search.title_dict.keys()) - set_doc_id


    # Поиск по заголовкам.
    @staticmethod
    def _head(query):
        result = []
        for key,value in Search.title_dict.items():
            if query in value.lower():
                result.append(key)
        return result


    # Цитатный поиск.
    def _quote(query):
        return


    # Булев поиск. Ну и реализация.. Кто так вообще программирует
    @staticmethod
    def _boolean(query):
        set_result = set()
        termins = query.split(' ')
        for termin in termins:
            temp = termin.split('%')
            if len(temp) > 1:
                if temp[0].startswith('!'):
                    set_and = _invert(Reader.block_for_termin_bool(temp[0][1:], Search.token_dict))
                else:
                    set_and = Reader.block_for_termin_bool(temp[0], Search.token_dict)
                i = 1
                while i < len(temp):
                    if temp[i].startswith('!'):
                        set_and = _and_invert(set_and,Reader.block_for_termin_bool(temp[i][1:], Search.token_dict))
                    else:
                        set_and = set_and & Reader.block_for_termin_bool(temp[i], Search.token_dict)
                    i+=1
                set_result = set_result | set_and
            else:
                if termin.startswith('!'):
                    set_result = set_result | _invert(Reader.block_for_termin_bool(termin[1:], Search.token_dict))
                else:
                    set_result = set_result | Reader.block_for_termin_bool(termin, Search.token_dict)
        return list(set_result)


    # Тфидф поиск.
    @staticmethod
    def _tfidf(query):
        dict_result = {}
        termins = query.split(' ')
        for termin in termins:
            termin = Search.stemmer.stemWord(termin)
            Reader.block_for_termin_tfidf(termin,dict_result, Search.token_dict)
        list_result = sorted(dict_result.items(), key=lambda x: x[1], reverse=True)
        list_result = list(map(lambda x: x[0],list_result))
        return list_result


    # Общая функция для поиска. Выбор поиска по его типу. Также здесь
    # логично будет добавить сниппеты к результатам. В будущем можно объединить
    # все выходные данные в один объект.
    @staticmethod
    def Search(type_, query):
        result = []
        if (type_ == 'boolean'):
            result = Search._boolean(query)
        elif (type_ == 'tfidf'):
            result = Search._tfidf(query)
        else:
            result = Search._head(query)
        if result:
            result = (list(map(lambda x: (x, Search.title_dict[x]), result[:30])), len(result))
        return result
