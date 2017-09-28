from argparse import ArgumentParser
from Search import app

def pars_args():
    """Settings for argparse"""
    parser = ArgumentParser(prog='Поиск по дампам Википедии',
            usage='Перед первым запуском приложения нужно построить индекс.',
            description='Для построения запустите приложение с ключом -i.')

    parser.add_argument('-i', help='Тип индекса на выбор, all - построить все.',
                        type=str, choices=('all', 'boolean', 'article', 'tfidf'))

    return parser.parse_args()


if __name__ == '__main__':
    args = pars_args()
    if args.i:
        from Search.index import Build
        Build(args.i)
    else:
        app.run(debug=True)
