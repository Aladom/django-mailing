# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.template import Library, Node, Context, Template
from django.template.defaulttags import token_kwargs
from django.template.exceptions import (
    TemplateDoesNotExist, TemplateSyntaxError,
)
from django.template.loader import get_template


register = Library()


class TagNode(Node):

    def __init__(self, nodelist, tag_name, extra_context=None):
        self.nodelist = nodelist
        self.tag_name = tag_name
        self.extra_context = extra_context or {}

    def get_template(self):
        template_name = 'mailing/html_tags/{}.html'.format(self.tag_name)
        try:
            template = get_template(template_name)
        except TemplateDoesNotExist:
            template = Template(
                "<{{ tag_name }}>{{ content }}</{{ tag_name }}>")
        return template

    def render(self, context):
        content = self.nodelist.render(context)
        template = self.get_template()
        template_context = Context({
            'tag_name': self.tag_name,
            'content': content,
        })
        values = dict((key, val.resolve(context)) for key, val in
                      self.extra_context.items())
        with template_context.push(**values):
            return template.render(template_context)


@register.tag(name="tag")
def make_tag(parser, token):
    nodelist = parser.parse(('endtag',))
    parser.delete_first_token()
    tokens = token.split_contents()

    try:
        tag_name = tokens[1]
    except IndexError:
        raise TemplateSyntaxError(
            "'{}' tag requires at least 1 argument.".format(tokens[0]))

    if tag_name[0] != tag_name[-1] or tag_name[0] not in ['"', "'"]:
        raise TemplateSyntaxError(
            "'{}' tag's first argument should be in quotes.".format(tokens[0]))
    tag_name = tag_name[1:-1]

    options = {}
    remaining_bits = tokens[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError(
                "The '{}' option was specified more than once.".format(option))
        if option == 'with':
            value = token_kwargs(remaining_bits, parser)
            if not value:
                raise TemplateSyntaxError(
                    "'with' in '{}' tag needs at least one "
                    "keyword argument.".format(tokens[0]))
        else:
            raise TemplateSyntaxError(
                "Unknown argument for '{}' tag: {}".format(tokens[0], option))
        options[option] = value

    extra_context = options.get('with', {})

    return TagNode(nodelist, tag_name, extra_context)
