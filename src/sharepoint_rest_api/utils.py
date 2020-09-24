import collections


def to_camel(snake_str):
    """function to convert snake case string to caml case"""
    return ''.join(x.title() for x in snake_str.split('_'))


def get_cache_key(args, **kwargs):
    "creates hash string to be used as key"
    joint_args = ''.join(args)
    order_dict = collections.OrderedDict(kwargs)
    return hash(joint_args) + hash(frozenset(order_dict.items()))


def first_upper(string):
    """returns string with only first letter uppercase"""
    return string[:1].upper() + string[1:] if string else ''
