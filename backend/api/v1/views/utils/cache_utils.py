from extensions import cache
import json

def get_cache(key):
    """Retrieve a value from the cache by its key."""

    data = cache.get(key)
    if data is not None:
        return json.loads(data)
    return None

def set_cache(key, value, timeout=60*60*24*7):
    """Set a value in the cache with a specified key and timeout."""
    cache.set(key, json.dumps(value), timeout=timeout)


def delete_cache(key):
    """Delete a value from the cache by its key."""
    if cache.get(key):
        cache.delete(key)   



def set_cache_api_details(key, data, api_id):
    """Cache API details using a key, composed of api_id and user_id if not already cached."""
    
    try:
        set_cache(key, data)
        api_id_key = f"api:{api_id}"
        api_keys = set(get_cache(api_id_key) or [])
        api_keys.add(key)
        set_cache(api_id_key, list(api_keys))
        return None
    except:
        pass


def invalidate_api_detail_cache(list_key, detail_key, api_id):
    try:
        if list_key:
            delete_cache(list_key)
        delete_cache(detail_key)
        api_id_key = f"api:{api_id}"
        api_keys = set(get_cache(api_id_key) or [])
        if detail_key in api_keys:
            api_keys.remove(detail_key)
        set_cache(api_id_key, list(api_keys))
    except:
        pass

# def invalidate_api_cache(list_key, api_id):
#     """
#     Invalidate cache api for all stored keys pertaining to the api
#     """
#     try:
#         delete_cache(list_key)
#         api_id_key = f"api:{api_id}"
#         api_keys = get_cache(api_id_key) or []
#         for key in api_keys:
#             delete_cache(key)
#         delete_cache(api_id_key)
#     except:
#         pass


def set_cache_model_details(key, data, api_id, model_name, stored=False):
    """Cache model details using a key, composed of api_id, user_id and model_name if not already cached."""
    
    try:
        if not stored:
            set_cache(key, data)
        api_id_key = f"api:{api_id}"
        api_model_key = f"model:{api_id}:{model_name}"
        api_keys = set(get_cache(api_id_key) or [])
        model_keys = set(get_cache(api_model_key) or [])
        model_keys.add(key)
        api_keys.add(key)
        set_cache(api_id_key, list(api_keys))
        set_cache(api_model_key, list(model_keys))
        return None
    except:
        pass

def invalidate_model_cache(api_id, model_name, cache_key = None):
    """Invalidate cached model details for a specific api_id and model_name."""
    try:

        api_id_key = f"api:{api_id}"
        api_model_key = f"model:{api_id}:{model_name}"
        model_keys = get_cache(api_model_key) or []
        api_keys = set(get_cache(api_id_key) or [])
        if cache_key is not None:
            if cache_key in model_keys:
                model_keys.remove(cache_key)
            if cache_key in api_keys:
                api_keys.remove(cache_key)
            set_cache(api_model_key, list(model_keys))
        else:
            for key in model_keys:
                delete_cache(key)
            delete_cache(api_model_key)
            api_keys.difference_update(set(model_keys))
        set_cache(api_id_key, list(api_keys))
        return None
    except:
        pass



def set_user_api_cache(key, data, parent_api_id, parent_model_name, child_models):
    set_cache_model_details(key, data, parent_api_id, parent_model_name)
    for child_model in child_models:
        child_model_api_id, child_model_name = child_model
        set_cache_model_details(key, data, child_model_api_id, child_model_name, True)

def invalidate_user_cache_api(cache_key, parent_api_id, parent_model_name, child_models):
    delete_cache(cache_key)
    invalidate_model_cache(parent_api_id, parent_model_name, cache_key)
    for child_model in child_models:
        child_model_api_id, child_model_name = child_model
        invalidate_model_cache(child_model_api_id, child_model_name, cache_key)