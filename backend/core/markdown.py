from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML


class TelegramHtmlRenderer(RendererHTML):
    def paragraph_open(self, tokens, idx, options, env):
        return ""

    def paragraph_close(self, tokens, idx, options, env):
        return "\n\n"


def render_as_nothing(self, tokens, idx, options, env):
    return ""


rules_whitelist = {
    "strong_open",
    "strong_close",
    "em_open",
    "em_close",
    "s_open",
    "s_close",
    "fence",
    "code_inline",
    "text",
    "softbreak",
    "hardbreak",
    "paragraph_open",
    "paragraph_close",
}

default_renderer_rules = RendererHTML().rules.keys()

for rule_name in default_renderer_rules:
    if rule_name not in rules_whitelist:
        setattr(TelegramHtmlRenderer, rule_name, render_as_nothing)

md_converter = MarkdownIt(renderer_cls=TelegramHtmlRenderer)
md_converter.options["html"] = False


def convert_md_to_html_for_telegram(md_text: str) -> str:
    return md_converter.render(md_text).strip()
