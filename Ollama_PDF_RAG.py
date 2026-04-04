"""
PDF RAG 시스템 - 다중 PDF 처리 지원
각 PDF별로 별도 폴더에 벡터 캐시를 저장하고 관리
"""
import gradio as gr
import ollama
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.retrievers import BaseRetriever

import config
from cache_manager import CacheManager

# 캐시 관리자 초기화
cache_manager = CacheManager()


def move_pdf_to_pdfs_folder(file_path: str) -> str:
    """업로드된 PDF 파일을 pdfs/ 폴더로 이동"""
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # pdfs 폴더로 이동
    dest_path = config.PDFS_DIR / source_path.name
    
    # 동일한 파일명이 있으면 덮어쓰기
    if dest_path.exists():
        dest_path.unlink()
    
    shutil.move(str(source_path), str(dest_path))
    print(f"📁 PDF 파일 이동 완료: {dest_path}")
    return str(dest_path)


def load_and_process_pdf(file_path: str) -> Tuple[BaseRetriever, str]:
    """PDF 문서 로드, 벡터화 및 Retriever 반환"""
    # PDF 파일을 pdfs 폴더로 이동
    moved_path = move_pdf_to_pdfs_folder(file_path)
    original_filename = Path(moved_path).name
    
    # PDF 로드
    loader = PyMuPDFLoader(moved_path)
    docs = loader.load()
    
    if not docs:
        raise ValueError("❗ PDF에서 텍스트를 추출할 수 없습니다. 다른 파일을 시도해 보세요.")
    
    print(f"📄 PDF 문서 로드 완료: {original_filename}")
    print(f"   페이지 수: {len(docs)}")
    print(f"   첫 페이지 미리보기:\n{docs[0].page_content[:200]}...\n")
    
    # 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    splits = text_splitter.split_documents(docs)
    print(f"📝 텍스트 청크 생성: {len(splits)}개")
    
    # 벡터 스토어 가져오기 또는 생성
    vectorstore, file_hash = cache_manager.get_or_create_vectorstore(
        documents=splits,
        file_path=moved_path,
        original_filename=original_filename
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": config.TOP_K_RESULTS}
    )
    
    return retriever, file_hash


def format_docs(docs) -> str:
    """검색된 문서들을 포맷팅"""
    if not docs:
        return ""
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        content = doc.page_content.strip()
        if content:
            formatted.append(f"[문서 {i}]\n{content}")
    
    return "\n\n".join(formatted)


def get_processed_pdf_list() -> List[str]:
    """처리된 PDF 목록을 Gradio 드롭다운 형식으로 반환"""
    pdfs = cache_manager.get_processed_pdfs()
    if not pdfs:
        return ["처리된 PDF가 없습니다"]
    
    # 파일명으로 정렬
    pdfs.sort(key=lambda x: x["filename"])
    return [f"{pdf['filename']} ({pdf['hash'][:8]}...)" for pdf in pdfs]


def get_pdf_hash_from_selection(selection: str) -> Optional[str]:
    """선택된 PDF의 해시 추출"""
    if not selection or "처리된 PDF가 없습니다" in selection:
        return None
    
    # 선택 문자열에서 해시 추출 (예: "filename.pdf (abc12345...)")
    try:
        hash_part = selection.split("(")[1].split("...")[0]
        # 전체 해시 찾기
        pdfs = cache_manager.get_processed_pdfs()
        for pdf in pdfs:
            if pdf["hash"].startswith(hash_part):
                return pdf["hash"]
    except Exception as e:
        print(f"⚠️ 해시 추출 실패: {e}")
    
    return None


def rag_chain_from_selection(selected_pdf: str, question: str) -> str:
    """선택된 PDF에 대해 RAG 체인 실행"""
    try:
        if not question or not question.strip():
            return "❌ 질문을 입력해주세요."
        
        # PDF 해시 추출
        file_hash = get_pdf_hash_from_selection(selected_pdf)
        if not file_hash:
            return "❌ 유효한 PDF를 선택해주세요."
        
        # 벡터 스토어 로드
        vectorstore = cache_manager.load_vectorstore(file_hash)
        if not vectorstore:
            return "❌ 선택한 PDF의 벡터 캐시를 찾을 수 없습니다. 다시 처리해주세요."
        
        # 문서 검색
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": config.TOP_K_RESULTS}
        )
        retrieved_docs = retriever.invoke(question)
        
        if not retrieved_docs:
            return "❌ 관련 문서를 찾을 수 없습니다. 질문을 더 구체적으로 작성해 보세요."
        
        # 컨텍스트 포맷팅
        context = format_docs(retrieved_docs)
        print(f"🔍 검색된 문서 개수: {len(retrieved_docs)}")
        print(f"📄 검색된 문맥 미리보기:\n{context[:300]}...\n")
        
        # 프롬프트 구성
        prompt = f"""다음 문서 내용을 바탕으로 질문에 답변해주세요.

질문: {question}

문서 내용:
{context}

답변:"""
        
        # Ollama LLM 호출
        response = ollama.chat(
            model=config.OLLAMA_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": config.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response['message']['content']
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 오류 발생: {error_msg}")
        return f"❌ 오류 발생: {error_msg}\n\n자세한 내용은 콘솔을 확인해주세요."


def rag_chain_from_upload(file, question: str) -> str:
    """업로드된 PDF에 대해 RAG 체인 실행"""
    try:
        if not file:
            return "❌ PDF 파일을 업로드해주세요."
        
        if not question or not question.strip():
            return "❌ 질문을 입력해주세요."
        
        # PDF 처리
        retriever, file_hash = load_and_process_pdf(file.name)
        
        # 문서 검색
        retrieved_docs = retriever.invoke(question)
        
        if not retrieved_docs:
            return "❌ 관련 문서를 찾을 수 없습니다. 질문을 더 구체적으로 작성해 보세요."
        
        # 컨텍스트 포맷팅
        context = format_docs(retrieved_docs)
        print(f"🔍 검색된 문서 개수: {len(retrieved_docs)}")
        print(f"📄 검색된 문맥 미리보기:\n{context[:300]}...\n")
        
        # 프롬프트 구성
        prompt = f"""다음 문서 내용을 바탕으로 질문에 답변해주세요.

질문: {question}

문서 내용:
{context}

답변:"""
        
        # Ollama LLM 호출
        response = ollama.chat(
            model=config.OLLAMA_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": config.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response['message']['content']
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 오류 발생: {error_msg}")
        return f"❌ 오류 발생: {error_msg}\n\n자세한 내용은 콘솔을 확인해주세요."


def update_pdf_dropdown():
    """PDF 드롭다운 목록 업데이트"""
    return gr.Dropdown.update(choices=get_processed_pdf_list())


# Gradio 인터페이스 구성
with gr.Blocks(title=config.GRADIO_TITLE) as iface:
    gr.Markdown(f"# {config.GRADIO_TITLE}")
    gr.Markdown(config.GRADIO_DESCRIPTION)
    
    with gr.Tabs():
        # 탭 1: 기존 PDF 선택
        with gr.Tab("📋 처리된 PDF 선택"):
            gr.Markdown("### 이미 처리된 PDF에서 질문하기")
            pdf_dropdown = gr.Dropdown(
                choices=get_processed_pdf_list(),
                label="PDF 선택",
                interactive=True
            )
            question_existing = gr.Textbox(
                label="질문을 입력하세요",
                placeholder="예: 이 문서의 주요 내용은 무엇인가요?",
                lines=3
            )
            btn_existing = gr.Button("질문하기", variant="primary")
            output_existing = gr.Textbox(
                label="답변",
                lines=10,
                interactive=False
            )
            
            btn_existing.click(
                fn=rag_chain_from_selection,
                inputs=[pdf_dropdown, question_existing],
                outputs=output_existing
            )
            
            refresh_btn = gr.Button("🔄 목록 새로고침")
            refresh_btn.click(
                fn=update_pdf_dropdown,
                outputs=pdf_dropdown
            )
        
        # 탭 2: 새 PDF 업로드
        with gr.Tab("📤 새 PDF 업로드"):
            gr.Markdown("### 새로운 PDF 파일 업로드 및 처리")
            file_upload = gr.File(
                label="PDF 파일 업로드",
                file_types=[".pdf"],
                type="filepath"
            )
            question_new = gr.Textbox(
                label="질문을 입력하세요",
                placeholder="예: 이 문서의 주요 내용은 무엇인가요?",
                lines=3
            )
            btn_new = gr.Button("업로드 및 질문하기", variant="primary")
            output_new = gr.Textbox(
                label="답변",
                lines=10,
                interactive=False
            )
            
            btn_new.click(
                fn=rag_chain_from_upload,
                inputs=[file_upload, question_new],
                outputs=output_new
            )
            
            gr.Markdown("""
            **참고:**
            - 업로드된 PDF는 자동으로 `pdfs/` 폴더로 이동됩니다.
            - 처리된 PDF는 다음에 재사용할 수 있습니다.
            - 동일한 파일은 캐시를 재사용하여 빠르게 처리됩니다.
            """)


if __name__ == "__main__":
    print("🚀 PDF RAG 시스템 시작...")
    print(f"📁 PDF 저장 폴더: {config.PDFS_DIR}")
    print(f"💾 캐시 폴더: {config.CACHE_DIR}")
    print(f"🤖 LLM 모델: {config.OLLAMA_LLM_MODEL}")
    print(f"🔤 임베딩 모델: {config.OLLAMA_EMBEDDING_MODEL}")
    print()
    
    iface.launch(share=False)
