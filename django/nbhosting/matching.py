import re

def matching_policy(name, patterns):
    """
    matching policy for course or students is as follows

    patterns is an iterable of patterns
    matching means a 'OR' of all patterns
    if patterns is empty, name is a match
    
    if one pattern is empty, name is a match
    if one pattern starts with a =, name matches 
        only if it is an exact match of what is after =
    if one pattern does not contain a '*', 
        all names that **contain** the filter match
    if one pattern contains a '*', name needs to match that pattern
        in the re sense, with:
        '*' replaced with '.*'
        '.' replaced by \.
    """
    
    if not patterns:
        return True
    for pattern in patterns:
        # an empty pattern like "" or None means a match
        if not pattern:
            return True
        # exact match
        if pattern[0] == '=':
            if name == pattern[1:]:
                return True
        # if '*' is 
        elif '*' in pattern:
            pattern = (pattern
                .replace('.', '\.')
                .replace('*', '.*'))
            pattern = f"^{pattern}$"
            if re.match(pattern, name):
                return True
        else:
            if pattern in name:
                return True
    return False
