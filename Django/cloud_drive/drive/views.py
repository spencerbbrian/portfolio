from django.template import loader
from django.http import HttpResponse

# Create your views here.
def main(request):
    template = loader.get_template('drive/main.html')
    return HttpResponse(template.render())