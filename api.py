from index import app

# WSGI handler for Vercel
def handler(request, context):
    return app
