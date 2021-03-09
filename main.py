import pandas as pd
from functools import partial


def get_input(message, type='str'):
    if type == 'str':
        return input('{}\n'.format(message))


class Menu:
    def __init__(self, items, infinite=True, on_each_iteration=None):
        self.items = items
        self.infinite = infinite
        self.on_each_iteration = on_each_iteration

    def start(self):
        while True:
            if self.on_each_iteration:
                self.on_each_iteration()
            for i, c in enumerate(self.items):
                print('{} - {}'.format(i+1, c['name']))
            if self.infinite:
                print('{} - Exit'.format(len(self.items)+1))

            while True:
                try:
                    choice = int(input())
                except:
                    print('Wrong index')
                    continue
                if choice < 1 or choice > len(self.items)+1:
                    print('Wrong index')
                    continue
                else:
                    break

            if choice == len(self.items)+1:
                break
            elif 'submenu' in self.items[choice-1]:
                submenu = Menu(self.items[choice-1], False)
                submenu.start()
            else:
                self.items[choice-1]['on_select']()
            print()
            if not self.infinite:
                break


class Data:
    def __init__(self, file_name):
        self.df = pd.read_csv(file_name, error_bad_lines=True)
        self.df[['director', 'cast', 'country']] = self.df[['director', 'cast', 'country']].fillna(value='')


    def find(self, title):
        return self.df[self.df['title'].str.contains('(?i){}'.format(title))]

    def columns(self):
        return [i for i in self.df.columns]

    def get_df(self):
        return self.df


class Filters:
    def __init__(self, get_uniques_in_field):
        self.filters = {
            'title': None,
            'release_year': None
        }

        self.get_uniques_in_field = get_uniques_in_field

    def _add_uniques_filter(self, field):
        def _select(value):
            self.filters[field] = [value]

        menu_items = []
        for i in self.get_uniques_in_field(field):
            menu_items.append({
                'name': i,
                'on_select': partial(_select, i)
            })

        Menu(menu_items, infinite=False).start()


    def _add_string_filter(self, field, message):
        s = input('{}\n'.format(message))
        self.filters[field] = s

    def _add_num_filter(self, field):
        eq = ''
        def set_eq(v):
            nonlocal eq
            eq = v

        Menu([
            {
                'name': '<',
                'on_select': partial(set_eq, '<')
            }, {
                'name': '=',
                'on_select': partial(set_eq, '=')
            }, {
                'name': '>',
                'on_select': partial(set_eq, '>')
            }
        ], infinite=False).start()

        value = int(input('Enter number to compare\n'))

        self.filters[field] = (eq, value)

    def add_filter(self):
        Menu([
            {
                'name': 'Show id',
                'on_select': partial(self._add_string_filter, 'show_id', 'Enter id of the show')
            }, {
                'name': 'Title',
                'on_select': partial(self._add_string_filter, 'title', 'Enter title')
            }, {
                'name': 'Director',
                'on_select': partial(self._add_string_filter, 'director', 'Enter director\'s name')
            }, {
                'name': 'Cast',
                'on_select': partial(self._add_string_filter, 'cast', 'Enter actor\'s name')
            }, {
                'name': 'Country',
                'on_select': partial(self._add_string_filter, 'country', 'Enter country')
            }, {
                'name': 'Rating',
                'on_select': partial(self._add_uniques_filter, 'rating')
            }, {
                'name': 'Release year',
                'on_select': partial(self._add_num_filter, 'release_year')
            }
        ], infinite=False).start()

    def remove_filter(self):
        if len(self.get_filters().keys()) == 0:
            print('No filters applied')
            return

        menu_items = []
        def _remove(field):
            self.filters = {k: v for k, v in self.filters.items() if v is not None and k != field}

        for k in self.get_filters().keys():
            menu_items.append({
                'name': k,
                'on_select': partial(_remove, k)
            })

        Menu(menu_items, infinite=False).start()

    def get_filters(self):
        return {k: v for k, v in self.filters.items() if v is not None}

    def apply_to_dataframe(self, df):
        cpy = df.copy()
        for k, v in self.get_filters().items():
            if type(v) is str:
                cpy = cpy[cpy[k].str.contains('(?i){}'.format(v))]
            elif type(v) is tuple:
                if v[0] == '<':
                    cpy = cpy[k] < v[1]
                elif v[0] == '=':
                    cpy = cpy[cpy[k] == v[1]]
                elif v[0] == '>':
                    cpy = cpy[k] > v[1]
            elif type(v) is list:
                cpy = cpy[k] == v[0]
        return cpy


class App:
    def __init__(self):
        def get_uniques(field):
            return self.data.get_df()[field].unique()

        self.data = Data('netflix_titles.csv')
        self.filters = Filters(get_uniques_in_field=get_uniques)

        self.menu = Menu([
            {
                'name': 'Add filter',
                'on_select': self.filters.add_filter
            }, {
                'name': 'Remove filter',
                'on_select': self.filters.remove_filter
            }, {
                'name': 'Find movie by title',
                'on_select': App.handle(self.data.find, ['show_id', 'title'], 'Enter title of the movie')
            }, {
                'name': 'Show filtered list',
                'on_select': self.show
            }, {
                'name': 'Save to csv file',
                'on_select': self.save_to_csv
            }
        ], on_each_iteration=self.show_filters)

    @staticmethod
    def handle(func, columns, *inputs):
        def inner():
            args = []
            for i in inputs:
                args.append(str(input('{}\n'.format(i))))
            print()
            result = func(*args)
            print(result[columns].to_string(index=False), end='\n\n')
        return inner

    def save_to_csv(self):
        name = input('Enter address for csv file\n')
        if name[-4:] != '.csv':
            name += '.csv'
        self.filters.apply_to_dataframe(self.data.get_df()).to_csv(name, index=False, header=True)

    def show_filters(self):
        print('Current filters are:')
        if len(self.filters.get_filters()) == 0:
            print('\tNo filters applied')
        else:
            print(self.filters.get_filters())

    def show(self):
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None, 'display.max_colwidth', -1):
            print(self.filters.apply_to_dataframe(self.data.get_df()))

    def run(self):
        print('Columns are: {}'.format(self.data.columns()))

        self.menu.start()


if __name__ == '__main__':
    app = App()
    app.run()
