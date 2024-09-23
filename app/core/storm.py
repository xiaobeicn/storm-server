import json
import os
import threading
from typing import Literal, Any, Callable, Union, List

import dspy
import requests
from knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from knowledge_storm.rm import SerperRM
from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler

from app.core.config import settings
from app.core.log import logger
from app.constants import LLMModel


def set_storm_runner(user_id: int) -> STORMWikiRunner:
    current_working_dir = os.path.join(settings.OUTPUT_DIR, str(user_id))
    if not os.path.exists(current_working_dir):
        os.makedirs(current_working_dir)
    logger.info(f"Successfully current_working_dir:{current_working_dir}")

    llm_configs = STORMWikiLMConfigs()
    llm_configs.init_openai_model(openai_api_key=settings.OPENAI_API_KEY, openai_type='openai')

    openai_kwargs = {'api_key': settings.OPENAI_API_KEY, 'api_provider': 'openai', 'temperature': 1.0, 'top_p': 0.9}

    llm_configs.set_conv_simulator_lm(OpenAIModel(model=LLMModel.GPT_4O_MINI, max_tokens=500, **openai_kwargs))
    llm_configs.set_question_asker_lm(OpenAIModel(model=LLMModel.GPT_4O_MINI, max_tokens=500, **openai_kwargs))
    llm_configs.set_outline_gen_lm(OpenAIModel(model=LLMModel.GPT_4O, max_tokens=400, **openai_kwargs))
    llm_configs.set_article_gen_lm(OpenAIModel(model=LLMModel.GPT_4O, max_tokens=700, **openai_kwargs))
    llm_configs.set_article_polish_lm(OpenAIModel(model=LLMModel.GPT_4O, max_tokens=4000, **openai_kwargs))

    engine_args = STORMWikiRunnerArguments(output_dir=current_working_dir, max_conv_turn=3, max_perspective=3, search_top_k=3, retrieve_top_k=5)
    logger.info("Successfully set up engine args")

    if LLMModel.RM == 'YouRM':
        rm = YouRM(ydc_api_key=settings.YDC_API_KEY, k=engine_args.search_top_k)
    else:
        data = {"autocorrect": True, "location": "China", "gl": "cn", "hl": "zh-cn", "num": 10, "page": 1}
        rm = SerperRM(serper_search_api_key=settings.SERPER_API_KEY, query_params=data)
    logger.info("Successfully get rm")

    runner = STORMWikiRunner(engine_args, llm_configs, rm)
    logger.info("Successfully get runner")

    return runner


def check_sensitive_info(text: str):
    ai_model = OpenAIModel(model='gpt-4o-mini-2024-07-18', max_tokens=10, api_key=settings.OPENAI_API_KEY, api_provider='openai', temperature=1.0, top_p=0.9)
    prompt = (
        "Please determine if the following topic complies with regulations:\n"
        "1. The topic must be meaningful and specific. Vague or irrelevant content (e.g., random numbers, single words without context) is not acceptable. tag '1'\n"
        "2. According to regulations in China, it must not contain sensitive information, including but not limited to pornography or adult content, current affairs and politics, drugs, gambling, drug abuse, violence, group events, etc. tag '2'\n"
        "Return '0' if it complies, return tag if it does not comply\n"
        "===\n"
        f"[{text}]"
    )
    response = ai_model.request(prompt)

    return response


class OpenAIModel(dspy.OpenAI):
    def __init__(
            self,
            model: str = "gpt-4o-mini",
            api_key: str | None = None,
            model_type: Literal["chat", "text"] = None,
            **kwargs
    ):
        super().__init__(model=model, api_key=api_key, model_type=model_type, **kwargs)
        self._token_usage_lock = threading.Lock()
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def log_usage(self, response):
        usage_data = response.get('usage')
        if usage_data:
            with self._token_usage_lock:
                self.prompt_tokens += usage_data.get('prompt_tokens', 0)
                self.completion_tokens += usage_data.get('completion_tokens', 0)

    def get_usage_and_reset(self):
        usage = {
            self.kwargs.get('model') or self.kwargs.get('engine'):
                {'prompt_tokens': self.prompt_tokens, 'completion_tokens': self.completion_tokens}
        }
        self.prompt_tokens = 0
        self.completion_tokens = 0

        return usage

    def __call__(
            self,
            prompt: str,
            only_completed: bool = True,
            return_sorted: bool = False,
            **kwargs,
    ) -> list[dict[str, Any]]:

        assert only_completed, "for now"
        assert return_sorted is False, "for now"

        prompt_modified = (
            f"{prompt}\n"
            "Please answer in Chinese"
        )
        response = self.request(prompt_modified, **kwargs)

        self.log_usage(response)

        choices = response["choices"]

        completed_choices = [c for c in choices if c["finish_reason"] != "length"]

        if only_completed and len(completed_choices):
            choices = completed_choices

        completions = [self._get_choice_text(c) for c in choices]
        if return_sorted and kwargs.get("n", 1) > 1:
            scored_completions = []

            for c in choices:
                tokens, logprobs = (
                    c["logprobs"]["tokens"],
                    c["logprobs"]["token_logprobs"],
                )

                if "<|endoftext|>" in tokens:
                    index = tokens.index("<|endoftext|>") + 1
                    tokens, logprobs = tokens[:index], logprobs[:index]

                avglog = sum(logprobs) / len(logprobs)
                scored_completions.append((avglog, self._get_choice_text(c)))

            scored_completions = sorted(scored_completions, reverse=True)
            completions = [c for _, c in scored_completions]

        return completions


class YouRM(dspy.Retrieve):
    def __init__(self, ydc_api_key=None, k=3, is_valid_source: Callable = None):
        super().__init__(k=k)
        if not ydc_api_key and not os.environ.get("YDC_API_KEY"):
            raise RuntimeError("You must supply ydc_api_key or set environment variable YDC_API_KEY")
        elif ydc_api_key:
            self.ydc_api_key = ydc_api_key
        else:
            self.ydc_api_key = os.environ["YDC_API_KEY"]
        self.usage = 0

        if is_valid_source:
            self.is_valid_source = is_valid_source
        else:
            self.is_valid_source = lambda x: True

    def get_usage_and_reset(self):
        usage = self.usage
        self.usage = 0

        return {'YouRM': usage}

    def forward(self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = []):
        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        self.usage += len(queries)
        collected_results = []
        for query in queries:
            try:
                headers = {"X-API-Key": self.ydc_api_key}
                response = requests.get(
                    f"https://api.ydc-index.io/search?query={query}&country=CN",
                    headers=headers,
                )
                results = response.json()
                if 'error_code' in results:
                    raise Exception(f"{results}")

                authoritative_results = []
                for r in results['hits']:
                    if self.is_valid_source(r['url']) and r['url'] not in exclude_urls:
                        authoritative_results.append(r)
                if 'hits' in results:
                    collected_results.extend(authoritative_results[:self.k])
            except Exception as e:
                logger.error(f'Error occurs when searching query {query}: {e}')

        return collected_results


class CallbackHandler(BaseCallbackHandler):
    def __init__(self, redis_client, redis_key):
        self.redis_client = redis_client
        self.redis_key = redis_key

    def on_identify_perspective_start(self, **kwargs):
        logger.info('on_identify_perspective_start')

        v = json.dumps({"state": "identify_perspective_start", "message": "Start identifying different perspectives for researching the topic. (Step 1 / 4)", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_identify_perspective_end(self, perspectives: list[str], **kwargs):
        logger.info('on_identify_perspective_end')

        perspective_list = "\n- ".join(perspectives)
        v = json.dumps({"state": "identify_perspective_end", "message": f"Finish identifying perspectives. Will now start gathering information from the following perspectives:\n- {perspective_list}", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_information_gathering_start(self, **kwargs):
        logger.info('on_information_gathering_start')

        v = json.dumps({"state": "information_gathering_start", "message": "Start browsing the Internet. (Step 2 /4)", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_dialogue_turn_end(self, dlg_turn, **kwargs):
        logger.info('on_dialogue_turn_end')
        urls = list(set([r.url for r in dlg_turn.search_results]))
        msg = ""
        for url in urls:
            msg += f'Finish browsing {url}\n'

        v = json.dumps({"state": "dialogue_turn_end", "message": msg, "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_information_gathering_end(self, **kwargs):
        logger.info('on_information_gathering_end')

        v = json.dumps({"state": "information_gathering_start", "message": "Finish collecting information.", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_information_organization_start(self, **kwargs):
        logger.info('on_information_organization_start')

        v = json.dumps({"state": "information_organization_start", "message": "Start organizing information into a hierarchical outline. (Step 3 / 4)", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_direct_outline_generation_end(self, outline: str, **kwargs):
        logger.info('on_direct_outline_generation_end')

        v = json.dumps({"state": "direct_outline_generation_end", "message": "Finish leveraging the internal knowledge of the large language model.", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)

    def on_outline_refinement_end(self, outline: str, **kwargs):
        logger.info('on_outline_refinement_end')

        v = json.dumps({"state": "outline_refinement_end", "message": "Finish leveraging the collected information.", "is_done": False, "code": 200})
        self.redis_client.rpush(self.redis_key, v)
