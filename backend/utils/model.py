from utils.base import BaseModelWrapper, TextRequest, SpeechRequest
from transformers import MBart50Tokenizer, MBartForConditionalGeneration, AutoModelForSeq2SeqLM, AutoTokenizer
from transformers import pipeline
import tempfile
class BaseModelWrapper:
    """
    Base class for all models.
    """

    def __load_model__(self):
        raise NotImplementedError("load_model method not implemented.")
        
    def generate(self, request: TextRequest):
        
        raise NotImplementedError("Generate method not implemented.")

class TextRequest(BaseModel):
    text: str
    src_lang: str
    tgt_lang: str
    model: str
class TextModel(BaseModelWrapper):
    """
    Text model class that inherits from BaseModelWrapper.
    This class is used to load and manage text models.
    """
    def __init__(self):  
        super().__init__()
        self.model_name = "facebook/mbart-large-50-one-to-many-mmt"

    def __str__(self):
        return f"Text Model Name: {self.model_name}"
    
    def __load_model__(self):

        model = MBartForConditionalGeneration.from_pretrained(self.model_name)
        tokenizer = MBart50Tokenizer.from_pretrained(self.model_name)

        print(f"✅ Model loaded.")
        return model.to("cuda"), tokenizer
    
    def generate(self, request: TextRequest):
        """
        Generate text based on the input request.
        :param request: TextRequest object containing the input text and languages.
        :return: Generated text.
        """
        model, tokenizer = self.__load_model__()
        if not model or not tokenizer:
            raise ValueError("❌ Model or tokenizer not loaded.")
       
        if request.src_lang not in tokenizer.lang_code_to_id or request.tgt_lang not in tokenizer.lang_code_to_id:
            return {"error": "Unsupported language code."}
    
        try:
            tokenizer.src_lang = request.src_lang
            inputs = tokenizer(request.text, return_tensors="pt").to("cuda")
            outputs = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id[request.tgt_lang])
            generated_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            return {"translation": generated_text}
        except Exception as e:
            return {"error": str(e)}

class SpeechModel(BaseModelWrapper):
    """
    Speech model class that inherits from BaseModelWrapper.
    This class is used to load and manage speech models.
    """
    def __init__(self):
        super().__init__()
        self.model_name = "openai/whisper-large-v3-turbo"  

    def __str__(self):
        return f"Speech Model Name: {self.model_name}"
    
    def __load_model__(self, task, language):
        pipeline_whisper = pipeline("automatic-speech-recognition",
                            model=self.model_name,
                            processor = self.model_name,
                            feature_extractor = self.model_name,
                            torch_dtype="auto",
                            generate_kwargs={"language": language,
                                             "task": task,},
                            device=0)

        print(f"✅ Model loaded.")
        return pipeline_whisper
    
    def generate(self, request: SpeechRequest):
        """
        Generate speech based on the input request.
        :param request: SpeechRequest object containing the input audio and languages.
        :return: Generated speech.
        """
        pipe = self.__load_model__(request.task, request.tgt_lang)
        if not pipe:
            raise ValueError("❌ Model not loaded.")
        
        try:
            with tempfile.NamedTemporaryFile(delete=True) as temp_audio_file:
                temp_audio_file.write(request.audio)
                temp_audio_file.flush()
                result = pipe(temp_audio_file.name)
                return {"translation": result["text"]}
        except Exception as e:
            return {"error": str(e)}


