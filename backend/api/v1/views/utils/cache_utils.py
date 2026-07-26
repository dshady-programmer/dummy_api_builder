from extensions import cache
import json
import pickle
import time
from redis.exceptions import WatchError
import functools


user_cache_namespace = lambda user_id: f"{{user:{user_id}}}" # {user:4}:api, using {} for consistent hashing across multiple nodes in the case of redis cluster
api_cache_namespace = lambda user_id, api_id: f"{{user:{user_id}}}:api:{api_id}"

# grabs the current version for the group space and grab the cache value

get_key_lua_script = """
    local version = redis.call("GET", KEYS[1])

    if not version then
        version = "0"
    end

    local data_key = ARGV[1] .. version
    local value = redis.call("GET", data_key)

    return {version, value} 
"""

set_key_lua_script = """
    redis.call("SET", KEYS[1], ARGV[1])
    redis.call("EXPIRE", KEYS[1], ARGV[2])
    return redis.status_reply("OK")
"""

redis_client = None
get_key_script = None
set_key_script = None


def update_redis_lua_script():
    global redis_client, get_key_script, set_key_script
    current_client = cache.cache._write_client
    if current_client is not redis_client or get_key_script is None or set_key_script is None:
        redis_client = current_client
        get_key_script = redis_client.register_script(get_key_lua_script)
        set_key_script = redis_client.register_script(set_key_lua_script)




def fail_safe_cache_operation(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Cache operation failed: {e}")
            return None
    return wrapper



@fail_safe_cache_operation
def get_cache(key):
    """Retrieve a value from the cache by its key."""
    data = cache.get(key)
    if data is not None:
        return json.loads(data)
    return None

@fail_safe_cache_operation
def set_cache(key, value, timeout=60*60*24):
    """Set a value in the cache with a specified key and timeout."""
    cache.set(key, json.dumps(value), timeout=timeout)


@fail_safe_cache_operation
def cached_api_list(user_id):
    namespace = user_cache_namespace(user_id)
    version_key = f"{namespace}:version" # {user:1}:version
    api_list_key = f"{namespace}:apis:v" # {user:1}:apis:v
    prefix = cache.cache._get_prefix()
    api_list_key = prefix+api_list_key
    version_key = prefix+version_key
    update_redis_lua_script()
    version, value = get_key_script(
        keys=[version_key],
        args=[api_list_key]
    )
    return version, value

@fail_safe_cache_operation
def set_api_list_cache(user_id, version, apis, timeout=60*60*24):

    namespace = user_cache_namespace(user_id)
    api_list_key = f"{namespace}:v{version}"
    prefix = cache.cache._get_prefix()
    api_list_key = prefix+api_list_key

    update_redis_lua_script()
    set_key_script(
        keys=[api_list_key],
        args=[json.dumps(apis), str(timeout)]
    )

@fail_safe_cache_operation
def get_api_detail_cache(user_id, api_id):
    namespace = api_cache_namespace
    version

@fail_safe_cache_operation
def set_api_detail_cache(user_id, version, detail, timeout=60*60*24):
    ...

@fail_safe_cache_operation
def set_hash_cache(key, field, value, timeout=60*60*24):
    """Set a value in the cache hash with a specified key, field, and timeout."""
    prefix = cache.cache._get_prefix()
    prefixed_key = prefix+key
    r = cache.cache._write_client
    r.hset(prefixed_key, field, json.dumps(value))
    r.expire(prefixed_key, timeout)

@fail_safe_cache_operation
def get_hash_cache(key, field):
    """Retrieve a value from the cache hash by its key and field."""
    prefix = cache.cache._get_prefix()
    prefixed_key = prefix+key
    r = cache.cache._read_client
    data = r.hget(prefixed_key, field)
    if data:
        return json.loads(data)
    return None

@fail_safe_cache_operation
def set_raw_cache(key, value, timeout=60*60*24):
    prefix = cache.cache._get_prefix()
    prefixed_key = prefix+key
    r = cache.cache._write_client
    r.set(prefixed_key, json.dumps(value), ex=timeout)

@fail_safe_cache_operation
def get_raw_cache(key):
    prefix = cache.cache._get_prefix()
    prefixed_key = prefix+key
    r = cache.cache._read_client
    data = r.get(prefixed_key)
    if data:
        return json.loads(data)
    return None

@fail_safe_cache_operation
def delete_cache(key):
    """Delete a value from the cache by its key."""
    
    cache.delete(key)

@fail_safe_cache_operation
def multiple_key_delete(keys):
    """Delete multiple keys from the cache."""
    cache.delete_many(*keys)




def set_cache_api_details(key, data, api_id):
    """Cache API details using a key, composed of api_id and user_id if not already cached."""
    
    try:
        """
        make this atomic
        """
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

        """
        make this atomic 
        """
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
        # print()
        # print("api_id_ky", api_id_key)
        # print("api_modl_ky", api_model_key)
        # print("modl kys", model_keys)
        # print("api kys", api_keys)
        # print()
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
        model_keys = set(get_cache(api_model_key) or [])
        
        api_keys = set(get_cache(api_id_key) or [])
        # print()
        # print("api_id_ky", api_id_key)
        # print("api_modl_ky", api_model_key)
        # print("modl kys", model_keys)
        # print("api kys", api_keys)
        # print()
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
            api_keys.difference_update(model_keys)
        set_cache(api_id_key, list(api_keys))
        return None
    except:
        pass



def set_user_api_cache(key, data, parent_api_id, parent_model_name, child_models):
    """
    Cache model key and let child models keep track of them, so when a parent model is updated 
    both the child and parent model data can be invalidated
    """

    set_cache_model_details(key, data, parent_api_id, parent_model_name)

    for child_model in child_models:
        child_model_api_id = child_model.api.id
        child_model_name = child_model.name
        set_cache_model_details(key, data, child_model_api_id, child_model_name, True)

def invalidate_user_cache_api(cache_key, parent_api_id, parent_model_name, child_models):
    """
    Invalidate model caches in the case of an update on model user entry data and let it ripple down to child models... 
    to prevent showing stale data.

    : note if parent model entry data is updated only the parent data would be deleted it won't affect the child 
            This is because child model only references the primary key 
    """
    invalidate_model_cache(parent_api_id, parent_model_name)
    for child_model in child_models:
        child_model_api_id = child_model.api.id
        child_model_name = child_model.name
        invalidate_model_cache(child_model_api_id, child_model_name, cache_key)



LUA_APPEND_ENTRYLIST =  """
    local raw = redis.call("GET", KEYS[1])
    if not raw then
        return nil
    end

    local entry_object = cjson.decode(raw)

    for i = 1, #ARGV do
        table.insert(entry_object.data, cjson.decode(ARGV[i]))
    end

    redis.call("SET", KEYS[1], cjson.encode(entry_object), "EX", 60*60*24*7)
    return #entry_object
"""


def update_entry_list_cache_on_add_new_entries(entrylists_key, new_entries):
    """ 
     Update cached entry list when a new entry is added
    """
    prefix = cache.cache._get_prefix()
    prefixed_key = prefix+entrylists_key
    r = cache.cache._write_client
    args = [json.dumps(e) for e in new_entries]
    r.eval(LUA_APPEND_ENTRYLIST, 1, prefixed_key, *args)



def set_entry_details(key, api_id, model_id):
    pass