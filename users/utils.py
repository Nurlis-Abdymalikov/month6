import random
import string
from django.core.cache import cache

CODE_EXPIRATION = 300

def generate_confirmation_code():
    return ''.join(random.choices(string.digits, k=6))

def set_confirmation_code(user_id):
    cache_key = f"confirmation_code_{user_id}"
    cache.delete(cache_key)

    code = generate_confirmation_code()
    cache.set(cache_key, code, timeout=CODE_EXPIRATION)
    return code

def get_confirmation_code(user_id):
    cache_key = f"confirmation_code_{user_id}"
    return cache.get(cache_key)

def delete_confirmation_code(user_id):
    cache_key = f"confirmation_code_{user_id}"
    cache.delete(cache_key)
