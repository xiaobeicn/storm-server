import logging
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

from app.core.config import settings


def set_storm_runner(user_name: str) -> STORMWikiRunner:
    current_working_dir = os.path.join(settings.OUTPUT_DIR, user_name)
    if not os.path.exists(current_working_dir):
        os.makedirs(current_working_dir)
    print(f"Successfully current_working_dir:{current_working_dir}")

    llm_configs = STORMWikiLMConfigs()
    llm_configs.init_openai_model(openai_api_key=settings.OPENAI_API_KEY, openai_type='openai')

    openai_kwargs = {'api_key': settings.OPENAI_API_KEY, 'api_provider': 'openai', 'temperature': 1.0, 'top_p': 0.9}

    llm_configs.set_conv_simulator_lm(OpenAIModel(model='gpt-3.5-turbo', max_tokens=500, **openai_kwargs))
    llm_configs.set_question_asker_lm(OpenAIModel(model='gpt-4-1106-preview', max_tokens=500, **openai_kwargs))
    llm_configs.set_outline_gen_lm(OpenAIModel(model='gpt-4-0125-preview', max_tokens=400, **openai_kwargs))
    llm_configs.set_article_gen_lm(OpenAIModel(model='gpt-4o-2024-05-13', max_tokens=700, **openai_kwargs))
    llm_configs.set_article_polish_lm(OpenAIModel(model='gpt-4o-2024-05-13', max_tokens=4000, **openai_kwargs))

    engine_args = STORMWikiRunnerArguments(output_dir=current_working_dir, max_conv_turn=3, max_perspective=3, search_top_k=3, retrieve_top_k=5)
    print("Successfully set up engine args")

    rm = YouRM(ydc_api_key=settings.YDC_API_KEY, k=engine_args.search_top_k)
    print("Successfully get rm from you.com")

    runner = STORMWikiRunner(engine_args, llm_configs, rm)
    print("Successfully get runner")

    return runner


def check_sensitive_info(text: str) -> bool:
    ai_model = OpenAIModel(model='gpt-3.5-turbo', max_tokens=10, api_key=settings.OPENAI_API_KEY, api_provider='openai', temperature=1.0, top_p=0.9)
    prompt = (
        "Based on China's situation, please determine whether the following content contains sensitive information, including but not limited to pornographic or adult content, current affairs and politics, drugs, gambling, drug abuse, violence, group incidents, etc. Please answer Yes or No\n"
        "===\n"
        f"{text}"
    )
    response = ai_model.request(prompt)
    print(response)
    if response['choices'][0]['message']['content'] == 'Yes':
        return False
    else:
        return True


class OpenAIModel(dspy.OpenAI):
    def __init__(
            self,
            model: str = "gpt-3.5-turbo-instruct",
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
                results = requests.get(
                    f"https://api.ydc-index.io/search?query={query}&country=CN",
                    headers=headers,
                ).json()

                authoritative_results = []
                for r in results['hits']:
                    if self.is_valid_source(r['url']) and r['url'] not in exclude_urls:
                        authoritative_results.append(r)
                if 'hits' in results:
                    collected_results.extend(authoritative_results[:self.k])
            except Exception as e:
                logging.error(f'Error occurs when searching query {query}: {e}')

        return collected_results
