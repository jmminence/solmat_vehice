from django.template import Library
from app.navigation import default_tree
from django.conf import settings
from utils import functions as fn
from django.utils.encoding import force_str
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

register = Library()

@register.filter(name='join_diagnostic')
def join_diagnostic(value):
    text = ''
    for i in value:
        text+= str(i.sample.index)+', '
    return text[:-2]

@register.filter(name='navigations')
def navigations(user):
    return default_tree(user)

@register.simple_tag
def settings_var(name):
    return getattr(settings, name, "")

@register.filter(name='get_item')
def get_item(list_or_dict, key):
    if isinstance(list_or_dict, dict):
        return list_or_dict.get(key)
    elif isinstance(list_or_dict, list):
        # Ensure the key is an integer and within the list's range
        if isinstance(key, int) and key < len(list_or_dict):
            return list_or_dict[key]
    return None  # Return None if conditions fail


@register.filter(name='highlight_grafico')
def highlight_grafico(text):
    import re
    # This regex matches the word 'Gráfico' followed by any number
    highlighted_text = re.sub(r'(Gráfico \d+)', r'<span class="highlight">\1</span>', text)
    return highlighted_text

@register.filter(name='get_item_table')
def get_item_table(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    else:
        # Handle the case where dictionary is not a dict, e.g., log an error or return a default value
        return 'Error: Expected a dictionary'


@register.simple_tag
def get_sample_value(sample_values, sample_id, result_name):
    # Ensure the strings are treated as Unicode
    sample_id = force_str(sample_id)
    result_name = force_str(result_name)
    key = f"{sample_id}-{result_name}"
    
    return sample_values.get(key, 0)  # Default to 0 if the key is not found


@register.simple_tag
def get_average(averages, sample_id, category):
    # Fetch the average value for the given sample_id and category
    result = averages.get(sample_id, {}).get(category, 0)  # Default to 0 if not found
    # Format the result to one decimal place if it's a float
    if isinstance(result, float):
        formatted_result = "{:.1f}".format(result)
        # Check if the formatted result ends with '.0', if so, convert to integer
        if formatted_result.endswith('.0'):
            return "{:.0f}".format(result)
        return formatted_result
    return result



@register.simple_tag
def get_cage_sum(cage_sums, key):
    return cage_sums.get(str(key), 0)  # Default to 0 if the key is not found

@register.simple_tag
def get_cage_total_sum(cage_sums):
    total = 0
    counter = 0
    
    for key, value in cage_sums.items():
        total += value
        counter += 1
        
    txt = str(total/counter)
    integer, decimal = txt.split('.')
    txt = f"{integer}.{decimal[0]}"
    
    return txt

@register.simple_tag
def get_identif_sum(identification_sums, key):
    try:
        key = int(key)
    except ValueError:
        return "0.00"  # Return "0.00" if the key is invalid
    value = identification_sums.get(key, 0)
    return "{:.1f}".format(value)  # Format the value to two decimal places

@register.simple_tag
def get_category_average(averages, category):
    value = averages.get(category, 0)
    return "{:.1f}".format(value)  # Format the value to one decimal place

@register.simple_tag
def get_dict_value(dictionary, key):
    """Retrieve value from a dictionary using a key and format it as an integer percentage."""
    value = dictionary.get(key, 0)
    return f"{int(value)}%"


# @register.translate
# def translate(value):
#     lang = fn.translation('en')
#     return getattr(settings, name, "")
