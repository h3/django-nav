import re

from django import template
from django_nav.base import nav_groups, NavOption

register = template.Library()

@register.assignment_tag(takes_context=True)
def get_nav(context, nav_group, *args, **kwargs):

    def check_conditional(of):
        conditional = of.conditional.get('function')
        return conditional and not conditional(context,
                                           *of.conditional['args'],
                                           **of.conditional['kwargs'])

    def build_dynamic_options(nav, path, *args, **kwargs):
        out = []
        if callable(nav.queryset):
            queryset = nav.queryset()
        else:
            queryset = nav.queryset

        for obj in queryset:
            option = type('SubNavOption',(NavOption,), nav.dehydrate_option(obj))()
            option.active = option.active_if(option.get_absolute_url(), path)
            out.append(option)
        return out

    def build_options(nav_options, path, *args, **kwargs):
        out = []
        for option in nav_options:
            option = option()

            if check_conditional(option): continue

            option.is_child = True
            option.active = False
            option.active = option.active_if(option.get_absolute_url(), path)
            option.option_list = build_options(option.options, path, *args, **kwargs)
            out.append(option)

        return out

    out = []
    for nav in nav_groups[nav_group]:
        if check_conditional(nav): continue

        request = context.get('request', None)
        if request:
            path = context.get('request').path
        else:
            path = "/"

        if nav.queryset:
            if callable(nav.queryset):
                queryset = nav.queryset()
            else:
                queryset = nav.queryset

            if len(queryset) > 0:
                nav.option_list = build_dynamic_options(nav, path)
            else:
                nav.option_list = build_options(nav.options, path)

        else:
            nav.option_list = build_options(nav.options, path)

        nav.active = False
        nav.is_root = True
        url = nav.get_absolute_url()
        nav.active = nav.active_if(url, path)

        out.append(nav)
    return out

@register.assignment_tag(takes_context=True)
def render_nav(context, nav_group, *args, **kwargs):
    tpl = kwargs.get('using', 'django_nav/nav.html')
    return template.loader.render_to_string(tpl, {
        'nav_group': nav_group,
        'classname': kwargs.get('classname', 'nav'),
        'nav_list': get_nav(context, nav_group, *args, **kwargs)})
