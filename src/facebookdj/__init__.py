from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from facebook.graph import GraphAPI, get_user_from_cookie
from facebook.rest import Facebook
import base64, re
from django.utils import simplejson
from django.http import HttpResponse


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

def get_rest_client():
    try:
        return _thread_locals.rest
    except AttributeError:
        raise ImproperlyConfigured('Make sure you have the Facebook middleware installed.')    

def require_login(next=None):
    def decorator(view):
        def newview(request, *args, **kwargs):
            next = newview.next
            
            try:
                graph = request.graph                
            except:
                raise ImproperlyConfigured('Make sure you have Facebook middleware installed')
            
            return view(request, *args, **kwargs)
        newview.next = next
        return newview
    return decorator

class Graph(GraphAPI):
    def __init__(self, access_token=None, user_id=None):
        super(Graph, self).__init__(access_token)
        self.uid = user_id
        
    def redirect(self, url):
        """
        Helper for Django which redirects to another page. If inside a
        canvas page, writes a <fb:redirect> instead to achieve the same effect.

        """
        if re.search("^https?:\/\/([^\/]*\.)?facebook\.com(:\d+)?", url.lower()):
            return HttpResponse('<script type="text/javascript">\ntop.location.href = "%s";\n</script>' % url)
        else:
            return HttpResponseRedirect(url)


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
            cookie = get_user_from_cookie(request.COOKIES, self.api_key, self.secret_key)
            if cookie:
                access_token = cookie['access_token']
                user_id = cookie.get('uid')
            else:
                access_token = None
                user_id = None
        
        _thread_locals.graph = request.graph = Graph(access_token, user_id)
        _thread_locals.rest = request.rest = Facebook(self.api_key, self.secret_key, access_token)
        
        

    def process_response(self, request, response):
        response['P3P'] = 'CP="NOI DSP COR NID ADMa OPTa OUR NOR"'
        return response
        