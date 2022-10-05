from flask_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

# from mainUrls import app
# cache = Cache(config={'CACHE_TYPE': 'simple'})
# cache.init_app()
# cache = Cache(app)