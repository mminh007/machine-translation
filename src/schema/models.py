from enum import StrEnum
from typing import TypeAlias
import os
from schema.base import BaseModelWrapper, SpeechRequest
import whisper

class SpeechModel(BaseModelWrapper):
    """
    Speech model class that inherits from BaseModelWrapper.
    This class is used to load and manage speech models.
    """
    def __init__(self):
        super().__init__()
        self.model_name = "base"#"openai/whisper-large-v3-turbo" 
        self.model = whisper.load_model(self.model_name) 

    def __str__(self):
        return f"Speech Model Name: {self.model_name}"
    
    def __load_model__(self):
        # pipeline_whisper = pipeline("automatic-speech-recognition",
        #                     model=self.model_name,
        #                     processor = self.model_name,
        #                     feature_extractor = self.model_name,
        #                     torch_dtype="auto",
        #                     generate_kwargs={"language": language,
        #                                      "task": task,},
        #                     device=0)
        pipeline_whisper = whisper.load_model(self.model_name)

        print(f"✅ Model loaded.")
        return pipeline_whisper
    
    def generate(self, request: SpeechRequest):
        """
        Generate speech based on the input request.
        :param request: SpeechRequest object containing the input audio and languages.
        :return: Generated speech.
        """
        
        if not self.model:
            raise ValueError("❌ Model not loaded.")
        
        try:    
            with open("temp.wav", "wb") as f:
                f.write(request.audio)
            result = self.model.transcribe("temp.wav")
            os.remove("temp.wav")
            return {"text": result["text"]}
        except Exception as e:
            return {"error": str(e)}
        

class LocalvLLMModelName(StrEnum):
    """Local vLLM model names"""

    LLAMA_32_3B_INSTRUCT = "llama-32-3B-instruct"
    LLAMA_32_1B_INSTRUCT = "llama-32-1B-instruct"
    MISTRAL_7B = "mistral-7b"
    LLAMA_3_8B = "llama-3-8b"
    LLAMA_3_34B = "llama-3-34b"

class HuggingFaceModelName(StrEnum):
    """HuggingFace model names"""

    LLAMA_3_8B_INSTRUCT = "meta-llama/Meta-Llama-3-8B-Instruct"
    LLAMA_3_70B_INSTRUCT = "meta-llama/Meta-Llama-3-70B-Instruct"
    LLAMA_3_34B_INSTRUCT = "meta-llama/Meta-Llama-3-34B-Instruct"
    LLAMA_70B_VISION_INSTRUCT = "meta-llama/Meta-Llama-3-70B-Vision-Instruct"
    ZEPHYR_7B = "HuggingFaceH4/zephyr-7b-beta"


class OpenAIModelName(StrEnum):
    """https://platform.openai.com/docs/models/gpt-4o"""
    
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4O = "gpt-4o"


class AzureOpenAIModelName(StrEnum):
    """Azure OpenAI model names"""

    AZURE_GPT_4O = "azure-gpt-4o"
    AZURE_GPT_4O_MINI = "azure-gpt-4o-mini"


class DeepseekModelName(StrEnum):
    """https://api-docs.deepseek.com/quick_start/pricing"""

    DEEPSEEK_CHAT = "deepseek-chat"


AllModelEnum: TypeAlias = (
    OpenAIModelName
    | AzureOpenAIModelName
    | DeepseekModelName
    | HuggingFaceModelName
    | LocalvLLMModelName)




# class TextModel(BaseModelWrapper):
#     """
#     Text model class that inherits from BaseModelWrapper.
#     This class is used to load and manage text models.
#     """
#     def __init__(self):  
#         super().__init__()
#         self.model_name = "facebook/mbart-large-50-one-to-many-mmt"
#         self.model = None
#         self.tokenizer = None

#     def __str__(self):
#         return f"Text Model Name: {self.model_name}"
    
#     def __load_model__(self):
#         if self.model is None or self.tokenizer is None:
#             self.model = MBartForConditionalGeneration.from_pretrained(self.model_name)
#             self.tokenizer = MBart50Tokenizer.from_pretrained(self.model_name)

#         print(f"✅ Model loaded.")
#         return self.model.to("cuda"), self.tokenizer
    
#     def generate(self, request: TextRequest):
#         """
#         Generate text based on the input request.
#         :param request: TextRequest object containing the input text and languages.
#         :return: Generated text.
#         """
#         model, tokenizer = self.__load_model__()
#         if not model or not tokenizer:
#             raise ValueError("❌ Model or tokenizer not loaded.")
       
#         if request.src_lang not in tokenizer.lang_code_to_id or request.tgt_lang not in tokenizer.lang_code_to_id:
#             return {"error": "Unsupported language code."}
    
#         try:
#             tokenizer.src_lang = request.src_lang
#             inputs = tokenizer(request.text, return_tensors="pt").to("cuda")
#             outputs = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id[request.tgt_lang])
#             generated_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
#             return {"translation": generated_text}
#         except Exception as e:
#             return {"error": str(e)}
