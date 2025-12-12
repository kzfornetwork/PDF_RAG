"""
설정 파일 - PDF RAG 시스템의 모든 설정을 중앙 관리
"""
import os
from pathlib import Path

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).parent
PDFS_DIR = BASE_DIR / "pdfs"  # 모든 PDF 파일 저장
CACHE_DIR = BASE_DIR / "cache"  # 벡터 캐시 저장 (PDF별 폴더)
CACHE_METADATA_DIR = BASE_DIR / "cache_metadata"  # 캐시 메타데이터

# 디렉토리 생성
PDFS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
CACHE_METADATA_DIR.mkdir(exist_ok=True)

# 하위 호환성을 위한 별칭 (기존 코드 지원)
VECTOR_CACHE_DIR = CACHE_DIR

# Ollama 모델 설정
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "mxbai-embed-large")

# 텍스트 분할 설정
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# RAG 설정
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "4"))  # 검색할 문서 개수

# 시스템 프롬프트
SYSTEM_PROMPT = """You are a helpful assistant. Read the PDF content and answer the question. 
Translate the answer in Korean with emoji. Be accurate and cite information from the context when possible."""

# Gradio 설정
GRADIO_TITLE = "PDF RAG - 다중 PDF 처리 버전"
GRADIO_DESCRIPTION = """
PDF 파일을 업로드하고 질문을 입력하면, 해당 내용을 기반으로 AI가 한국어로 답변해 줍니다.

**주요 기능:**
- 📄 다중 PDF 파일 관리 및 처리
- 📁 PDF별 독립적인 벡터 캐시 저장
- 🔍 스마트 문서 검색 (캐시 자동 재사용)
- 🤖 Ollama 로컬 LLM 기반 답변 생성
- 💾 파일 해시 기반 캐시 관리
- 📋 처리된 PDF 목록 관리
"""

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "False").lower() == "true"

