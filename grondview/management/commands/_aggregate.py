from objectquery.models import AstroSource
from imagequery.models import ImageHeader
from django.db.models import Q
from django.db.models import Count
import cPickle as pickle  
import datetime

def main(*args,**kwargs):
  context = {}
  context['aggData'] = {}
  context['aggData']['totalFields'] = ImageHeader.objects.distinct('TARGETID').count()
  t = AstroSource.objects.filter(user__username='pipeline').annotate(nbands=Count('photometry__BAND',distinct=True))
  context['aggData']['totalPipelineObjects'] = len([i for i in t if i.nbands>=2])
  t = AstroSource.objects.filter(~Q(user__username='pipeline')).annotate(nbands=Count('photometry__BAND',distinct=True))
  context['aggData']['totalUserObjects'] = len([i for i in t if i.nbands>=2])
  s = sum([(abs(i.TOPRIGHT_DEC-i.BOTTOMLEFT_DEC))*(abs(i.BOTTOMLEFT_RA-i.TOPRIGHT_RA)) for i in ImageHeader.objects.filter(FILTER='r').distinct('TARGETID')])
  context['aggData']['totalArea_r'] = round(s,3)
  s = sum([(abs(i.TOPRIGHT_DEC-i.BOTTOMLEFT_DEC))*(abs(i.BOTTOMLEFT_RA-i.TOPRIGHT_RA)) for i in ImageHeader.objects.filter(FILTER='J').distinct('TARGETID')])
  context['aggData']['totalArea_J'] = round(s,3)
  context['aggData']['totalOBs'] = ImageHeader.objects.distinct('TARGETID','OB').count()
  context['time'] = datetime.datetime.now()

  with open(kwargs['picklefile'],'w') as f:
    pickle.dump(context,f)

if __name__=="__main__":
  main(picklefile='test.pickle')
