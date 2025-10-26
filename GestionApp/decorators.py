from django.shortcuts import redirect

def login_required(function):
    def wrapper(request, *args, **kwargs):
        if 'login_usuario_id' not in request.session:
            return redirect('login')
        return function(request, *args, **kwargs)
    return wrapper