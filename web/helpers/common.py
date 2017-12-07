import inspect

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be database.QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]