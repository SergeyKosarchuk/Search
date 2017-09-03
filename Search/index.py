# -*- coding: utf-8 -*-
from json import loads
from re import split
from os import remove
from pathlib import Path
from struct import pack
from Stemmer import Stemmer
from progressbar import ProgressBar

import sys
import time
import shutil

from config import *

stemmer = Stemmer('russian')
index = {}
dict_tokens = {} # Словарь токенов (bool - {token, token_id}; tfidf - {token,[token_id,numTokenInDoc]})
dict_articles = {}
num_tokens = 0
tfidf = False
max_file_for_merge = 200


# Декоратор для вывода времени работы построителя.
def timer(func):
    def wrapper(*args, **kwargs):
        before = time.clock()
        func()
        after = time.clock()
        print('Индекс построен за: {} секунд.'.format(after - before))
    return wrapper


def update_index(doc_id,tokens):
    global tfidf
    for token in tokens:
        if token in dict_tokens:
            token_id = dict_tokens[token]
        else:
            global num_tokens
            num_tokens += 1  # подсчет общего числа уникальных токенов для назначения token_id
            token_id = num_tokens
            dict_tokens[token] = token_id
        if tfidf:
            tmp = index[token_id] = index.get(token_id,{})
            tmp[doc_id] = tmp.get(doc_id,0) + 1/len(tokens) # запись tf
        else:
            tmp = index[token_id] = index.get(token_id, [])
            if doc_id not in tmp:
                tmp.append(doc_id)


def get_tokens(text):
    text = text.lower()
    text = text.replace(chr(769), '') #Правильное удаление ударения с вики
    text = text.replace('\n', '')
    tokens = split(r'[^а-я]', text.strip())
    tokens = stemmer.stemWords(tokens)
    return tokens


def pars(article):
    parsed_article = loads(article)
    tokens = get_tokens(parsed_article['text'])
    dict_articles[int(parsed_article['id'])] = parsed_article['title'].encode('utf-8')
    update_index(int(parsed_article['id']),tokens)


def create_index(file_name):
    with open(file_name,'r') as f:
        text = set(f.readlines())
        for line in text:
            pars(line)


# Запись временного индекса в файл.
def write_index(file_name):
    global tfidf
    f = open(file_name, 'wb')
    for key in sorted(index.keys()):
        f.write(pack('I', key)) # Запись token_id.
        f.write(pack('I', len(index[key])))  # Запись кол-ва doc_id.
        tmp = index[key]
        for key1 in tmp:
            f.write(pack('I', key1))  # Запись doc_id.
            if tfidf:
                f.write(pack('f', tmp[key1])) # Запись tf.
    f.close()

# Cоздание временных индексов и запись их в файлы.
# Возвращает кол-во полученных индексов.
def create_indexs(distr_damps_name,distrIndexName):
    contdir = []
    for i in os.walk(distr_damps_name):
        contdir.append(i)
    files = []
    for i in contdir:
        for j in i[2]:
            if '.' not in j:
                files.append(i[0] + '/' + j)
    del contdir
    print('Создание индексов:')
    with ProgressBar(max_value=len(files)) as p:
        numIndexs = 0
        for f in files:
            index.clear()
            create_index(f)
            write_index(distrIndexName + '/ind' + str(numIndexs) + '.ind')
            numIndexs += 1
            p.update(numIndexs)
            print('Кол-во токенов: ' + str(num_tokens))
    return numIndexs

# Запись словаря {token -> offset} в файл (кол-во токенов (len(token) -> token -> offset)).
def write_token_dict_to_file(file_name, dict):
    global tfidf
    f = open(file_name, 'wb')
    f.write(pack('I', len(dict)))  # Кол-во токенов.
    print('Запись словаря токенов: ')
    with ProgressBar(max_value=len(dict)) as p:
        i = 0
        for key in sorted(dict.keys()):
            f.write(pack('I', len(key) * 2))  # Длина токена.
            f.write(pack(str(len(key) * 2) + 's', key.encode('utf-8')))
            f.write(pack('L', dict[key]))  # Оффсет в файле индекса.
            i+=1
            p.update(i)
    f.close()

# Запись словаря {doc_id -> title} в файл (кол-во док-ов (doc_id -> len(title), title)).
def write_art_dict_to_file(file_name, dict):
    f = open(file_name, 'wb')
    f.write(pack('I', len(dict)))  # Кол-во токенов.
    print('Запись словаря статей: ')
    with ProgressBar(max_value=len(dict)) as p:
        i = 0
        for doc_id in dict:
            f.write(pack('I', doc_id))
            f.write(pack('I', len(dict[doc_id])))  # Длина title.
            f.write(pack(str(len(dict[doc_id])) + 's', dict[doc_id]))
            i+=1
            p.update(i)
    f.close()


# f - список [ открытый файл | int ].
def read_token_id_from_file(f):
    try:
        f[1] = unpack('I', f[0].read(4))[0]  # Пробуем считать слудующий token_id из файла.
    except:
        f[0].close()  # Если не вышло, значит файл закончился. Закрываем его и больше его не проверяем.
        f[1] = None


# files_indexs - список списков [ открытый файл | int ].
def read_coord_block_from_files(coord_block,files_indexs,token_id):
    coord_block.clear()
    global tfidf
    for f in files_indexs:
        if f[1] is None:
            continue
        if f[1] == token_id:  # сверяем token_id в файле с нужным
            f[1] = unpack('I', f[0].read(4))[0]  # считываем длину координатного блока
            if tfidf:
                for _ in range(f[1]):
                    coord_block.append((unpack('I', f[0].read(4))[0],unpack('f', f[0].read(4))[0]))
            else:
                for _ in range(f[1]):
                    coord_block.append(unpack('I', f[0].read(4))[0])
            read_token_id_from_file(f)

# Слияние индексов. Аргументы: имя директории с временными индексами и
# имена итоговых индекса и словарей {token -> offset}, {doc_id -> URL}.
def merge_indexs(distr_name, file_name_global_index, file_name_token_dict, file_name_art_dict):
    global tfidf
    contdir = []
    for i in os.walk(distr_name):
        contdir.append(i)
    files = []  # список имен всех файлов в директории и поддиректориях
    for i in contdir:
        for j in i[2]:
            if j[0] != '.':
                files.append(i[0] + '/' + j)
    contdir.clear()
    files_indexs = []#список списков [открытый файл индекса | token_id, перед коорд блоком которого, находится курсор в этом файле]
    dict_list = []#список кортежей (token_id | token)
    coord_block = []  # координатный блок, куда собирается информация по одному токену из всех файлов индекса,
    #  после чего записывается в итоговый файл
    for token in dict_tokens:
        dict_list.append((dict_tokens[token],token))
    dict_list.sort()
    num_iter = 0
    global max_file_for_merge
    while len(files) > max_file_for_merge:
        for i in range(max_file_for_merge):  # открываем первые 200 файлов сливаемых индексов
            files_indexs.append([open(files[i], 'rb'), -1])
        for f in files_indexs:
            read_token_id_from_file(f)
        file_global_index = open(distr_name + '/tmpind' + str(num_iter) + '.ind', 'wb')
        #print('Предварительное Слияние (еще: ' + str(int(len(files)/max_file_for_merge)) + '): ')
        with ProgressBar(max_value=len(dict_list)) as p:
            pb = 0
            for i in dict_list:  # перебор токенов
                read_coord_block_from_files(coord_block,files_indexs,i[0]) #Заполняем координатный блок этого токена
                file_global_index.write(pack('I', i[0]))  # записываем token_id
                file_global_index.write(pack('I', len(coord_block)))  # записываем длину координатного блока
                if tfidf:
                    for j in coord_block:
                        file_global_index.write(pack('If', j[0],j[1]))
                else:
                    for j in coord_block:
                        file_global_index.write(pack('I', j))
                pb += 1
                p.update(pb)
        file_global_index.close()
        files_indexs.clear()
        for i in range(max_file_for_merge):
            remove(files[i])
        files.clear()
        for i in os.walk(distr_name):
            contdir.append(i)
        for i in contdir:
            for j in i[2]:
                if j[0] != '.':
                    files.append(i[0] + '/' + j)
        contdir.clear()
        num_iter+=1
    for file_name in files:  # открываем файлы сливаемых индексов
        files_indexs.append([open(file_name, 'rb'), -1])
    for f in files_indexs:
        read_token_id_from_file(f)
    file_global_index = open(file_name_global_index, 'wb')
    print('Итоговое Слияние: ')
    with ProgressBar(max_value=len(dict_list)) as p:
        pb = 0
        for i in dict_list:# перебор токенов
            read_coord_block_from_files(coord_block,files_indexs,i[0])
            dict_tokens[i[1]] = file_global_index.tell()  # записываем 'оффсет токена в глобальном индексе' в словарь токенов вместо token_id
            file_global_index.write(pack('I', len(coord_block)))  # записываем длину координатного блока
            if tfidf:
                for j in coord_block:
                    file_global_index.write(pack('If',j[0],j[1]))
            else:
                for j in coord_block:
                    file_global_index.write(pack('I',j))
            pb+=1
            p.update(pb)
    file_global_index.close()
    for file_name in files:
        remove(file_name)
    del files_indexs
    write_token_dict_to_file(file_name_token_dict, dict_tokens)
    write_art_dict_to_file(file_name_art_dict, dict_articles)


def create_global_index(distr_damps_name):
    if not os.path.exists(distr_damps_name):
        print('Указанной директории с дампами не существует!')
        return
    if tfidf:
        bool_or_tfidf = 'tfidf'
    else:
        bool_or_tfidf = 'bool'
    try:
        os.mkdir(distr_damps_name + '/index')
    except OSError:
        print('Директория (' + distr_damps_name + '/index) уже существует!')
    try:
        os.mkdir(distr_damps_name + '/index/tmp')
    except OSError:
        print('Директория (' + distr_damps_name + '/index/tmp) удалена!')
        shutil.rmtree(distr_damps_name + '/index/tmp')
        os.mkdir(distr_damps_name + '/index/tmp')
    create_indexs(distr_damps_name,distr_damps_name + '/index/tmp')
    merge_indexs(distr_damps_name + '/index/tmp',distr_damps_name + '/index/index'+ bool_or_tfidf + '.ind',
                distr_damps_name + '/index/index' + bool_or_tfidf + '.tdict',distr_damps_name + '/index/index.adict')




###############################################################################
###############################################################################

############################# CREATE ARTICLE INDEX ############################

###############################################################################



def get_id(article):
    parsed_article = loads(article)
    return parsed_article['id']


def pars_file(file_name):
    ids = []
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            id_article = get_id(line)
            ids.append(id_article)
    return ids


# Записывваем ид статей isd из файла file_number в файл индекса f.
def write_data(ids, file_number, f):
    f.write(pack('II', file_number, len(ids)))
    for id_ in ids:
        f.write(pack('I', int(id_)))


#  Функция для обработки директории.
def pars_dir(directory, file_number, f):
    for x in directory.iterdir():
        if x.name[0] != '.' and x.is_file():
            ids = pars_file(x)
            write_data(ids, file_number, f)
            file_number = file_number + 1
    return file_number


# Главная функция. Идем по директориям и обрабатываем каждую отдельно.
# Тащим декскриптор файла f из основной функции до конечной, что ни есть хорошо.
# Как это можно исправить?
@timer
def _art_index():
    print('Строится индекс статей для показа сниппетов.')
    p = Path(NAME_DIR_WITH_DAMPS)
    with open(PATH + ARTICLE_INDEX,'wb') as f: # Создаем файл с индексом.
        # Сначала записываем общее кол-во файлов. Здесь оно подсчитано заранее.
        f.write(pack('H', 4570))
        file_number = 0 # Общее количество файлов.
        dirs = [x for x in p.iterdir() if x.is_dir()]
        # Если в исходной директории только файлы, то парсим ее и выходим.
        if len(dirs) == 0:
            pars_dir(p, file_number, f)
            return
        with ProgressBar(max_value=len(dirs)) as p:
            i = 0
            for d in dirs:
                file_number = pars_dir(d, file_number, f)
                i = i + 1
                p.update(i)


###############################################################################
###############################################################################

############################# CREATE ARTICLE INDEX ############################

###############################################################################
@timer
def _bool_index():
    print('Строится булев индекс.')
    global tfidf
    tfidf = False
    create_global_index(NAME_DIR_WITH_DAMPS)


@timer
def _tfidf_index():
    print('Строится тфидф индекс.')
    global tfidf
    tfidf = True
    create_global_index(NAME_DIR_WITH_DAMPS)


def _all():
    print('Строим индексы...')
    timeStart = time.clock()
    _art_index()
    _bool_index()
    _tfidf_index()
    print('Индексы построены за ' + str(time.clock() - timeStart) + ' секунд.')


def Build(type_):
    choise = {
    'tfidf' : _tfidf_index,
    'boolean' : _bool_index,
    'article' : _art_index,
    'all' : _all
    }
    choise.get(type_, lambda : print('Запуск приложения без перестроения индекса.'))()
