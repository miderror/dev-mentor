import html

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML


class TelegramHtmlRenderer(RendererHTML):
    def paragraph_open(self, tokens, idx, options, env):
        return ""

    def paragraph_close(self, tokens, idx, options, env):
        return "\n\n"

    def hr(self, tokens, idx, options, env):
        return ""

    def heading_open(self, tokens, idx, options, env):
        return ""

    def heading_close(self, tokens, idx, options, env):
        return ""

    def blockquote_open(self, tokens, idx, options, env):
        return ""

    def blockquote_close(self, tokens, idx, options, env):
        return ""

    def link_open(self, tokens, idx, options, env):
        token = tokens[idx]
        href = token.attrGet("href")
        if href:
            return f'<a href="{html.escape(href)}">'
        return "<a>"

    def link_close(self, tokens, idx, options, env):
        return "</a>"

    def image(self, tokens, idx, options, env):
        return ""

    def bullet_list_open(self, tokens, idx, options, env):
        return ""

    def bullet_list_close(self, tokens, idx, options, env):
        return "\n"

    def ordered_list_open(self, tokens, idx, options, env):
        return ""

    def ordered_list_close(self, tokens, idx, options, env):
        return "\n"

    def list_item_open(self, tokens, idx, options, env):
        return "• "

    def list_item_close(self, tokens, idx, options, env):
        return "\n"


def render_as_nothing(self, *args, **kwargs):
    """
    Заглушка для правил рендеринга, которые мы хотим полностью проигнорировать.
    Принимает любые аргументы, чтобы соответствовать сигнатуре методов рендерера.
    """
    return ""


rules_whitelist = {
    "text",
    "softbreak",
    "hardbreak",
    "strong_open",
    "strong_close",
    "em_open",
    "em_close",
    "s_open",
    "s_close",
    "code_inline",
    "fence",
    "paragraph_open",
    "paragraph_close",
    "link_open",
    "link_close",
    "bullet_list_open",
    "bullet_list_close",
    "ordered_list_open",
    "ordered_list_close",
    "list_item_open",
    "list_item_close",
}

all_possible_rules = set(RendererHTML().rules.keys())
for attr_name in dir(RendererHTML):
    if not attr_name.startswith("_") and callable(getattr(RendererHTML, attr_name)):
        if attr_name not in all_possible_rules:
            all_possible_rules.add(attr_name)

for rule_name in all_possible_rules:
    if rule_name not in rules_whitelist and not hasattr(
        TelegramHtmlRenderer, rule_name
    ):
        setattr(TelegramHtmlRenderer, rule_name, render_as_nothing)


md_converter = MarkdownIt(renderer_cls=TelegramHtmlRenderer)
md_converter.options["html"] = False


def convert_md_to_html_for_telegram(md_text: str) -> str:
    cleaned_md = md_text.replace("---", "").strip()
    return md_converter.render(cleaned_md).strip()
