import json

from urllib import urlencode
from copy import deepcopy

from django.db.models import Count
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView

from core.models import Student


client = settings.ES_CLIENT


class HomePageView(TemplateView):

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        if self.request.GET.get('sql'):
            return self.get_sql_context()
        body = {
            'aggs': {
                'course_names': {
                    'terms': {
                        'field': 'course_names', 'size': 0
                    }
                },
                'university__name': {
                    'terms': {
                        'field': 'university.name'
                    }
                },
                'year_in_school': {
                    'terms': {
                        'field': 'year_in_school'
                    }
                },
                'age': {
                    'histogram': {
                        'field': 'age',
                        'interval': 2
                    }
                }
            },
            # 'query': {'match_all': {}}
        }
        es_query = self.gen_es_query(self.request)
        body.update({'query': es_query})
        search_result = client.search(index='django', doc_type='student', body=body)

        context = super(HomePageView, self).get_context_data(**kwargs)
        context['hits'] = [
            self.convert_hit_to_template(c) for c in search_result['hits']['hits']
        ]
        context['aggregations'] = self.prepare_facet_data(
            search_result['aggregations'],
            self.request.GET
        )
        return context

    def convert_hit_to_template(self, hit1):
        hit = deepcopy(hit1)
        almost_ready = hit['_source']
        almost_ready['pk'] = hit['_id']
        return almost_ready

    def facet_url_args(self, url_args, field_name, field_value):
        is_active = False
        if url_args.get(field_name):
            base_list = url_args[field_name].split(',')
            if field_value in base_list:
                del base_list[base_list.index(field_value)]
                is_active = True
            else:
                base_list.append(field_value)
            url_args[field_name] = ','.join(base_list)
        else:
            url_args[field_name] = field_value
        return url_args, is_active

    def prepare_facet_data(self, aggregations_dict, get_args):
        resp = {}
        for area in aggregations_dict.keys():
            resp[area] = []
            if area == 'age':
                resp[area] = aggregations_dict[area]['buckets']
                continue
            for item in aggregations_dict[area]['buckets']:
                url_args, is_active = self.facet_url_args(
                    url_args=deepcopy(get_args.dict()),
                    field_name=area,
                    field_value=item['key']
                )
                resp[area].append({
                    'url_args': urlencode(url_args),
                    'name': item['key'],
                    'count': item['doc_count'],
                    'is_active': is_active
                })
        return resp

    def gen_es_query(self, request):
        req_dict = deepcopy(request.GET.dict())
        if not req_dict:
            return {'match_all': {}}
        filters = []
        for field_name in req_dict.keys():
            if '__' in field_name:
                filter_field_name = field_name.replace('__', '.')
            else:
                filter_field_name = field_name
            for field_value in req_dict[field_name].split(','):
                if not field_value:
                    continue
                filters.append(
                    {
                        'term': {filter_field_name: field_value},
                    }
                )
        return {
            'filtered': {
                'query': {'match_all': {}},
                'filter': {
                    'bool': {
                        'must': filters
                    }
                }
            }
        }

    def get_sql_context(self):
        context = super(HomePageView, self).get_context_data()
        # create a query
        req_dict = deepcopy(self.request.GET.dict())
        query = Student.objects
        for key, value in  req_dict.iteritems():
            if key == 'course_names':
                field_name = 'courses__name'
            else:
                field_name = key
            if not value:
                continue
            if ',' in value:
                values = value.split(',')
                for value in values:
                    query = query.filter(**{field_name: value})
        # List of hitted students
        context['hits'] = query.all()[:20]
        # Aggregation list
        context['aggregations'] = {
            'year_in_school': [],
            'course_names': [],
            'age': [],
            'university__name': [],
        }

        for facet_area in context['aggregations'].keys():
            if facet_area == 'course_names':
                field_name = 'courses__name'
            else:
                field_name = facet_area

            data = query.values(field_name).annotate(count=Count(field_name))
            for item in data:
                option = item[field_name]
                count = item['count']
                url_args, is_active = self.facet_url_args(
                    url_args=deepcopy(self.request.GET.dict()),
                    field_name=facet_area,
                    field_value=option
                )
                context['aggregations'][facet_area].append(
                    {
                        'name': option,
                        'count': count,
                        'is_active': is_active,
                        'url_args': urlencode(url_args)
                    }
                )
        return context


def autocomplete_view(request):
    query = request.GET.get('term', '')
    resp = client.suggest(
        index='django',
        body={
            'name_complete': {
                "text": query,
                "completion": {
                    "field": 'name_complete',
                }
            }
        }
    )
    options = resp['name_complete'][0]['options']
    data = json.dumps(
        [{'id': i['payload']['pk'], 'value': i['text']} for i in options]
    )
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def student_detail(request):
    student_id = request.GET.get('student_id')
    student = Student.objects.get(pk=student_id)
    return render(request, 'student-details.html', context={'student': student})

