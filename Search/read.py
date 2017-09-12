import struct
from math import log
from config import *


class Reader:
    """ Класс для загрузки разных словарей с диска в память.
        Также есть функции для чтения блоков из индекса. """


    def _article_dict(self):
        d = {}
        with open(PATH + ARTICLE_INDEX, 'rb') as f:
            amount = struct.unpack('H', f.read(2))[0]
            for _ in range(amount):
                data = f.read(4)
                number = struct.unpack('I', data) [0]
                count = struct.unpack('I', f.read(4)) [0]
                for i in range(count):
                    id_ = struct.unpack('I', f.read(4)) [0]
                    d[id_] = (number, i)
        return d


    def _title_dict(self):
        d = {}
        with open(PATH + TITLE_DICTIONARY,'rb') as f:
            amount = struct.unpack('I', f.read(4))[0]  # Кол-во документов
            for _ in range(amount):
                docId = struct.unpack('I', f.read(4))[0]  # Номер документа
                lenght = struct.unpack('I', f.read(4))[0]  # Длинна заголовка
                d[docId] = struct.unpack(str(lenght) + 's', f.read(lenght))[0].decode('utf-8')
        return d


    def _token_dict(self):
        d = {}
        with open(PATH + TOKEN_DICTIONARY_BOOL,'rb') as f:
            amount = struct.unpack('I', f.read(4))[0]  # Кол-во токенов
            for _ in range(amount):
                l = struct.unpack('I', f.read(4))[0]  # Длинна токена
                token = struct.unpack(str(l) + 's', f.read(l))[0].decode('utf-8')
                if token in d:
                    d[token].append(struct.unpack('L',f.read(8))[0])
                else:
                    d[token] = [struct.unpack('L',f.read(8))[0]]

        with open(PATH + TOKEN_DICTIONARY_TFIDF,'rb') as f:
            amount = struct.unpack('I', f.read(4))[0]  # Кол-во токенов
            for _ in range(amount):
                l = struct.unpack('I', f.read(4))[0]  # Длинна токена
                token = struct.unpack(str(l) + 's', f.read(l))[0].decode('utf-8')
                if token in d:
                    d[token].append(struct.unpack('L',f.read(8))[0])
                else:
                    d[token] = [struct.unpack('L',f.read(8))[0]]

        return d


    # Чтение координатного блока из булева индекса в список, аргументы:
    # файл, offset токена в файле
    def block_for_termin_bool(termin, token_dict):
        file_name = PATH + INDEX_BOOL
        offset = token_dict.get(termin, None)
        if offset is None:
            return set()
        offset = offset[0]
        coord_block = []
        with open(file_name,'rb') as f:
            f.seek(offset) #Переход в начало нужного коорд блока
            l = struct.unpack('I', f.read(4))[0] #длина блока (кол-во docId)
            for _ in range(l):
                coord_block.append(struct.unpack('I', f.read(4))[0])
        return set(coord_block)


    # Чтение координатного блока из tfidf индекса в список, аргументы:
    # файл, offset токена в файле
    def block_for_termin_tfidf(termin, coord_block, title_dict, token_dict):
        file_name = PATH + INDEX_TFIDF
        offset = token_dict.get(termin, None)
        if offset is None:
            return coord_block
        offset = offset[1]
        with open(file_name,'rb') as f:
            f.seek(offset) #Переход в начало нужного коорд блока
            l = struct.unpack('I', f.read(4))[0] #длина блока (кол-во docId)
            value_idf = log(len(title_dict)/l)
            for _ in range(l):
                doc_id = struct.unpack('I', f.read(4))[0]
                value_tf = struct.unpack('f', f.read(4))[0]
                coord_block[doc_id] = coord_block.get(doc_id,0) + value_tf * value_idf
        return coord_block


    def __init__(self):
        self.title_dict = self._title_dict()
        self.token_dict = self._token_dict()
        self.article_dict = self._article_dict()
