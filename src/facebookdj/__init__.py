from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import facebook
import base64
from django.utils import simplejson

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local
    
_thread_locals = local()

def get_graph_client():
    """
    Get the current Facebook object for the calling thread.
    """
    try:
        return _thread_locals.graph
    except AttributeError:
        raise ImproperlyConfigured('Make sure you have the Facebook middleware installed.')
    

def require_login(next=None):
    def decorator(view):
        def newview(request, *args, **kwargs):
            next = newview.next
            
            try:
                graph = request.graph
                print "user.id", graph.uid
            except:
                raise ImproperlyConfigured('Make sure you have Facebook middleware installed')
            
            return view(request, *args, **kwargs)
        newview.next = next
        return newview
    return decorator

class Graph(facebook.GraphAPI):
    def __init__(self, access_token=None, user_id=None):
        super(Graph, self).__init__(access_token)
        self.uid = user_id


def base64_url_decode(input):
    input += '=' * (4 - (len(input) % 4))    
    return base64.urlsafe_b64decode(input.encode('ascii'))


class FacebookMiddleware(object):
    """
Middleware that attaches a Graph object to every incoming request.
The Graph object created can also be accessed from models for the
current thread by using get_graph_client().

"""

    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key or settings.FACEBOOK_API_KEY
        self.secret_key = secret_key or settings.FACEBOOK_SECRET_KEY
        

    def process_request(self, request):
        signed_request = request.GET.get('signed_request')
        if signed_request:            
            sig, payload = map(base64_url_decode, signed_request.split('.'))
            
            data = simplejson.loads(payload)
            access_token = data.get('oauth_token')
            user_id = data.get('user_id')
            
        else:
            cookie = facebook.get_user_from_cookie(request.COOKIES, self.api_key, self.secret_key)
            if cookie:
                access_token = cookie['access_token']
                user_id = cookie.get('uid')
            else:
                access_token = None
                user_id = None
        _thread_locals.graph = request.graph = Graph(access_token, user_id)
        
        

    def process_response(self, request, response):
        response['P3P'] = 'CP="NOI DSP COR NID ADMa OPTa OUR NOR"'
        return response
        