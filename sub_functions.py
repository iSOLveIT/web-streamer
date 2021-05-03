from random import sample
from string import ascii_letters


# Cover seconds to hours and minutes
def sec_to_time_format(total_secs=0):
    total_secs = total_secs
    # Separate seconds into hours, and minutes
    hours = (total_secs % 86400) // 3600
    minutes = ((total_secs % 86400) % 3600) // 60

    return hours, minutes


# Random string generator
def random_str_generator(str_length):
    alphanum = ascii_letters + '0123456789'
    output = ''.join(sample(alphanum, str_length))
    return output
