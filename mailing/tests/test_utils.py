# -*- coding: utf-8 -*-
from django.test import TestCase

from mailing.utils import html_to_text


class HtmlToTextTestCase(TestCase):

    def test_no_html(self):
        html = "Ceci est du HTML sans balises"
        text = "Ceci est du HTML sans balises"
        self.assertEqual(html_to_text(html), text)

    def test_simple_html(self):
        html = "<p>Ceci est du <b>HTML</b> simple</p>"
        text = "Ceci est du HTML simple"
        self.assertEqual(html_to_text(html), text)

    def test_html_with_attributes(self):
        html = (
            '<p style="line-height:20px;color:blue">Ceci est du '
            '<a href="http://example.com/" target=_blank>HTML</a>.</p>'
        )
        text = (
            "Ceci est du HTML (http://example.com/)."
        )
        self.assertMultiLineEqual(html_to_text(html), text)

    def test_linefeed(self):
        html = (
            "<p>Ceci\n"
            "est un paragraphe</p>\n\n"
            "<p>Ceci est un autre paragraphe</p>\n"
            "<p>Un autre paragraphe</p>\n\n\n"
            "<p>Et encore un autre paragraphe</p>"
        )
        text = (
            "Ceci\n"
            "est un paragraphe\n\n"
            "Ceci est un autre paragraphe\n"
            "Un autre paragraphe\n\n\n"
            "Et encore un autre paragraphe"
        )
        self.assertMultiLineEqual(html_to_text(html), text)

    def test_script_tag(self):
        html = (
            "<p>Ceci est un paragraphe</p>\n\n"
            "<script>Et ceci est un script</script>"
        )
        text = (
            "Ceci est un paragraphe\n\n"
        )
        self.assertMultiLineEqual(html_to_text(html), text)

    def test_script_tag_with_atributes(self):
        html = (
            "<p>Ceci est un paragraphe</p>\n\n"
            "<script type='text/javascript'>console.log('Et ceci est un "
            "<script>script</script>');</script>\n\n"
            "<p>Un autre paragraphe</p>"
        )
        text = (
            "Ceci est un paragraphe\n\n\n\n"
            "Un autre paragraphe"
        )
        self.assertMultiLineEqual(html_to_text(html), text)

    def test_picture(self):
        html = (
            '<p>Une image : <img src="https://example.com/example.jpg" '
            'alt="Example"></p>\n\n'
            '<p>Une autre image : <img '
            'src="https://example.com/example.png"/></p>\n\n'
            '<a href="https://example.com/my-ads"><img alt="Voir mes '
            'annonces" src="https://example.com/view-ads.png"></a>\n\n'
            '<img alt="Toto" />'
        )
        text = (
            "Une image : Example\n\n"
            "Une autre image : \n\n"
            "Voir mes annonces (https://example.com/my-ads)\n\n"
            "Toto"
        )
        self.assertMultiLineEqual(html_to_text(html), text)

    def test_wrong_html(self):
        html = "<p>Coucou <b>ça <i>va</b> ?</i>"
        text = "Coucou ça va ?"
        self.assertEqual(html_to_text(html), text)

    def test_link_without_anchor(self):
        html = "<a>Je suis un faux lien</a>"
        text = "Je suis un faux lien"
        self.assertEqual(html_to_text(html), text)

    def test_link_equal_text(self):
        html = "<a href='https://github.com/'>https://github.com/</a>"
        text = "https://github.com/"
        self.assertEqual(html_to_text(html), text)
