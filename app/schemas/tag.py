#schamesはapiとクライアントの間の取り決めを描く場所って感じ
from pydantic import BaseModel#バリデーションを自動でやってくれる　jsonにじどうでpythoから変えてくれるやつ
from typing import Optional#値がなくてもおkを表す方ヒント
from datetime import datetime
from pydantic import ConfigDict

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)#ConfigDict(from_attributes=True) = SQLAlchemyモデルを直接レスポンスに変換するための設定。


    id: int
    name: str
    created_at: Optional[datetime] = None