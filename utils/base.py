from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str
    src_lang: str
    tgt_lang: str

class SpeechRequest(BaseModel):
    
    audio: bytes
    task: str
    tgt_lang: str

    
class BaseModelWrapper:
    """
    Base class for all models.
    """

    def load_model(self):
        raise NotImplementedError("load_model method not implemented.")
        
    def generate(self, request: TextRequest):
        
        raise NotImplementedError("Predict method not implemented.")

