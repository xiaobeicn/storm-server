import json
import os
import re

from app.core import log
from app.core.config import settings

logger = log.setup_logging()


def article_directory(account_id: int, title):
    return os.path.join(settings.OUTPUT_DIR, str(account_id), title.replace(' ', '_').replace('/', '_'))


def add_inline_citation_link(article_text, citation_dict):
    pattern = r'\[(\d+)\]'

    def replace_with_link(match):
        i = match.group(1)
        url = citation_dict.get(int(i), {}).get('url', '#')
        return f'[[{i}]]({url})'

    return re.sub(pattern, replace_with_link, article_text)


def construct_citation_dict(data):
    if data is None:
        return None
    citation_dict = {}
    try:
        url_info = json.loads(data) if isinstance(data, str) else data
        for url, index in url_info['url_to_unified_index'].items():
            citation_dict[index] = {'url': url,
                                    'title': url_info['url_to_info'][url]['title'],
                                    'snippets': url_info['url_to_info'][url]['snippets']}
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")

    return citation_dict
