from sqlalchemy.orm import declarative_base #salalchemyはpythonのDB捜査用ライブラリでORM (Object Relational Mapper)」が入ってる。　declarative_baseとはそのORMを使うための土対クラスを作る工場

# すべてのモデルが継承する“土台クラス　クラスとは ---　という種類のデータの統計図”
Base = declarative_base()#このように書くとBaseという親クラスが作られ、このbaseを継承してクラスを書くと自動でこれはテーブルだとaqlalchemyが理解してくれる

__all__ = ["Base"]