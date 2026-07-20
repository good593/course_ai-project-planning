"""RF-3 AI상담을 위한 내부 지식베이스 RAG(벡터 검색).

week05 day03 "건강한하루 RAG 시스템 만들기" 노트북에서 검증한 방식을 그대로
백엔드 서비스로 옮긴다: SQLite 테이블(상품·영양소_기능성·영양소_섭취기준)을
행 단위 Chunk 문서로 만들고, 로컬 Ollama 임베딩으로 Chroma 벡터저장소에 저장한 뒤
질문과 유사한 문서를 검색한다.

week04에서 만든 `search_internal_product`/`search_internal_nutrient` 키워드(LIKE)
검색을 이 서비스로 대체한다.
"""
from langchain_core.documents import Document

from app.core.config import CHROMA_DIR, EMBEDDING_MODEL, RAG_COLLECTION_NAME
from app.core.database import SessionLocal
from app.models.nutrient import IntakeStandard, NutrientFunction
from app.models.product import Product


def _or_default(value: str | None) -> str:
    return value if value not in (None, "") else "정보 없음"


def _build_product_documents(rows: list[Product]) -> list[Document]:
    """상품마스터 한 행 = 상품 하나에 대한 Chunk (week05 day03과 동일한 설계)."""
    docs = []
    for row in rows:
        content = (
            f"[상품 정보] {row.상품명} ({row.카테고리})\n"
            f"- 업소명: {row.업소명}\n"
            f"- 주요 원료: {row.검색키워드}\n"
            f"- 관련 증상: {row.관련_증상}\n"
            f"- 섭취량 및 섭취방법: {_or_default(row.섭취량_섭취방법)}\n"
            f"- 섭취 시 주의사항: {_or_default(row.섭취시주의사항)}\n"
            f"- 기능성 내용: {_or_default(row.기능성_내용)}"
        )
        metadata = {"source": "상품마스터", "label": row.상품명, "상품ID": row.상품ID}
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def _build_function_documents(rows: list[NutrientFunction]) -> list[Document]:
    """영양소_기능성 한 행 = 영양소 하나의 기능성 근거에 대한 Chunk."""
    docs = []
    for row in rows:
        content = (
            f"[영양소 기능성 정보] {row.영양소} ({_or_default(row.분류)})\n"
            f"- 기능성: {row.기능성}\n"
            f"- 관련 증상: {_or_default(row.관련_증상)}\n"
            f"- 근거 수준: {_or_default(row.근거_수준)} (신뢰도: {_or_default(row.신뢰도)})\n"
            f"- 근거 설명: {_or_default(row.근거_설명)}\n"
            f"- 출처: {_or_default(row.출처)}"
        )
        metadata = {"source": "영양소_기능성_추천DB", "label": row.영양소}
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def _build_intake_documents(rows: list[IntakeStandard]) -> list[Document]:
    """영양소_섭취기준 한 행 = 영양소·연령대·성별 조건 하나에 대한 Chunk."""
    docs = []
    for row in rows:
        content = (
            f"[섭취기준 정보] {row.영양소} - {_or_default(row.연령대)} {_or_default(row.성별)} "
            f"(임신여부: {_or_default(row.임신여부)}, 수유여부: {_or_default(row.수유여부)})\n"
            f"- 권장섭취량: {_or_default(row.권장섭취량)} {_or_default(row.단위)}\n"
            f"- 충분섭취량: {_or_default(row.충분섭취량)} {_or_default(row.단위)}\n"
            f"- 상한섭취량: {_or_default(row.상한섭취량)} {_or_default(row.단위)}\n"
            f"- 출처: {_or_default(row.출처)} ({_or_default(row.기관)})"
        )
        metadata = {"source": "영양소별_권장섭취량", "label": row.영양소, "연령대": row.연령대, "성별": row.성별}
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def _load_all_documents() -> list[Document]:
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        functions = db.query(NutrientFunction).all()
        intakes = db.query(IntakeStandard).all()
    finally:
        db.close()
    return (
        _build_product_documents(products)
        + _build_function_documents(functions)
        + _build_intake_documents(intakes)
    )


class RagNotReadyError(Exception):
    """로컬 Ollama 서버/임베딩 모델이 준비되지 않아 벡터 검색을 할 수 없는 상태."""


_vectorstore = None


def _get_vectorstore():
    """Chroma 벡터저장소는 최초 1회만 만들어 재사용한다(day03 노트북과 동일한 패턴)."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    store = Chroma(
        collection_name=RAG_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    if store._collection.count() == 0:
        store.add_documents(_load_all_documents())

    _vectorstore = store
    return _vectorstore


def search(query: str, k: int) -> list[Document]:
    """질문과 유사한 내부 문서 top-k를 반환한다."""
    try:
        store = _get_vectorstore()
        return store.similarity_search(query, k=k)
    except Exception as exc:  # Ollama 서버 미실행 등
        raise RagNotReadyError(
            "내부 지식베이스 벡터 검색을 사용할 수 없습니다. 로컬 Ollama 서버(ollama serve)와 "
            f"임베딩 모델({EMBEDDING_MODEL})이 준비되었는지 확인해주세요. (원인: {exc})"
        ) from exc
