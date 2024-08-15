import os

from knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from knowledge_storm.lm import OpenAIModel
from knowledge_storm.rm import YouRM

from app.core.config import settings


def set_storm_runner(user_name: str) -> STORMWikiRunner:
    current_working_dir = os.path.join(settings.OUTPUT_DIR, user_name)
    if not os.path.exists(current_working_dir):
        os.makedirs(current_working_dir)
    print(f"Successfully current_working_dir:{current_working_dir}")

    llm_configs = STORMWikiLMConfigs()
    llm_configs.init_openai_model(openai_api_key=settings.OPENAI_API_KEY, openai_type='openai')
    llm_configs.set_question_asker_lm(OpenAIModel(model='gpt-4-1106-preview', api_key=settings.OPENAI_API_KEY, api_provider='openai', max_tokens=500, temperature=1.0, top_p=0.9))
    engine_args = STORMWikiRunnerArguments(output_dir=current_working_dir, max_conv_turn=3, max_perspective=3, search_top_k=3, retrieve_top_k=5)
    print("Successfully set up engine args")

    rm = YouRM(ydc_api_key=settings.YDC_API_KEY, k=engine_args.search_top_k)
    print("Successfully get rm from you.com")

    runner = STORMWikiRunner(engine_args, llm_configs, rm)
    print("Successfully get runner")

    return runner

