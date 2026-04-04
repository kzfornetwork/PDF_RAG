# PDF RAG - 다중 PDF 처리 시스템

PDF 문서를 업로드하고 AI에게 질문할 수 있는 RAG(Retrieval-Augmented Generation) 시스템입니다. Ollama를 사용하여 로컬에서 실행되며, 다중 PDF를 효율적으로 관리하고 처리할 수 있습니다.

## ✨ 주요 기능

- 📄 **다중 PDF 처리**: 여러 PDF 파일을 각각 관리하고 재사용 가능
- 🔍 **스마트 캐시 관리**: 파일 해시 기반 캐시로 동일 파일 재처리 시간 97% 단축
- 📁 **자동 파일 관리**: 업로드된 PDF를 자동으로 `pdfs/` 폴더로 정리
- 🤖 **Ollama 통합**: 로컬 LLM을 사용하여 프라이버시 보장
- 💾 **벡터 검색**: ChromaDB를 사용한 효율적인 문서 검색
- 🎨 **사용자 친화적 UI**: Gradio 기반 웹 인터페이스

## 📋 요구사항

- Python 3.8 이상
- Ollama 설치 및 실행 중
- 필요한 모델:
  - LLM: `llama3` (또는 다른 모델)
  - Embedding: `mxbai-embed-large`

## 🚀 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd PDF_RAG
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. Ollama 모델 다운로드

```bash
# LLM 모델 다운로드
ollama pull llama3

# 임베딩 모델 다운로드
ollama pull mxbai-embed-large
```

## 📁 프로젝트 구조

```
PDF_RAG/
├── pdfs/                          # 모든 PDF 파일 저장
│   └── *.pdf
│
├── cache/                         # 벡터 캐시 저장 (PDF별 폴더)
│   └── {pdf_hash}/
│       └── chroma.sqlite3
│
├── cache_metadata/                # 캐시 메타데이터
│   └── pdf_metadata.json
│
├── Report/                        # 작업 리포트
│   ├── PDF_RAG_개선_작업_리포트.md
│   └── 작업_요약.md
│
├── Ollama_PDF_RAG.py              # 메인 코드
├── cache_manager.py               # 캐시 관리 모듈
├── config.py                      # 설정 파일
├── requirements.txt               # 의존성 패키지
└── README.md                      # 프로젝트 설명
```

## 🎯 사용 방법

### 프로그램 실행

```bash
python Ollama_PDF_RAG.py
```

웹 브라우저에서 자동으로 Gradio 인터페이스가 열립니다.

### 사용 시나리오

#### 1. 새 PDF 업로드 및 질문

1. **"새 PDF 업로드"** 탭 선택
2. PDF 파일 업로드
3. 질문 입력 (예: "이 문서의 주요 내용은 무엇인가요?")
4. **"업로드 및 질문하기"** 버튼 클릭
5. 답변 확인

#### 2. 처리된 PDF에서 질문

1. **"처리된 PDF 선택"** 탭 선택
2. 드롭다운에서 PDF 선택
3. 질문 입력
4. **"질문하기"** 버튼 클릭
5. 답변 확인

#### 3. PDF 목록 새로고침

- **"🔄 목록 새로고침"** 버튼을 클릭하여 최신 PDF 목록 업데이트

## ⚙️ 설정

`config.py` 파일에서 다음 설정을 변경할 수 있습니다:

```python
# Ollama 모델 설정
OLLAMA_LLM_MODEL = "llama3"
OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large"

# 텍스트 분할 설정
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# RAG 설정
TOP_K_RESULTS = 4  # 검색할 문서 개수
```

### 환경변수 지원

모든 설정값은 환경변수로 오버라이드 가능합니다:

```bash
# 예시
export OLLAMA_LLM_MODEL=llama3.2
export CHUNK_SIZE=1500
python Ollama_PDF_RAG.py
```

## 🔧 주요 모듈

### Ollama_PDF_RAG.py
메인 애플리케이션 파일. Gradio UI와 RAG 파이프라인을 포함합니다.

### cache_manager.py
PDF별 벡터 캐시를 관리하는 모듈:
- 파일 해시 계산 (SHA256)
- 벡터 스토어 생성/로드
- 캐시 메타데이터 관리
- 처리된 PDF 목록 조회

### config.py
프로젝트의 모든 설정을 중앙 관리하는 파일.

## 📊 성능 개선

| 항목 | 개선 전 | 개선 후 | 개선율 |
|------|---------|---------|--------|
| 동일 파일 재처리 시간 | ~30초 | ~1초 | **97% ↓** |
| 다중 PDF 지원 | ❌ | ✅ | - |
| 캐시 활용 | ❌ | ✅ | - |
| 파일 자동 관리 | ❌ | ✅ | - |

## 🛠️ 기술 스택

- **LLM**: Ollama (로컬 실행)
- **임베딩**: Ollama Embeddings (mxbai-embed-large)
- **벡터 DB**: ChromaDB
- **문서 처리**: LangChain, PyMuPDF
- **UI**: Gradio
- **언어**: Python 3.x

## 📝 작동 원리

1. **PDF 업로드**: 사용자가 PDF 파일을 업로드
2. **파일 이동**: PDF가 자동으로 `pdfs/` 폴더로 이동
3. **해시 계산**: 파일의 SHA256 해시 계산
4. **캐시 확인**: 기존 벡터 캐시 존재 여부 확인
5. **벡터화**: 캐시가 없으면 PDF를 로드하고 벡터화하여 저장
6. **문서 검색**: 질문과 관련된 문서 청크 검색
7. **답변 생성**: 검색된 문서를 컨텍스트로 LLM이 답변 생성

## 🔍 캐시 시스템

- **파일 해시 기반**: 각 PDF의 고유 해시를 기반으로 캐시 폴더 생성
- **자동 재사용**: 동일 파일은 기존 캐시를 재사용하여 빠르게 처리
- **변경 감지**: 파일이 변경되면 자동으로 재벡터화
- **독립 관리**: 각 PDF의 벡터 캐시를 별도 폴더에 저장

## 📌 주의사항

- Ollama가 실행 중이어야 합니다
- 필요한 모델이 다운로드되어 있어야 합니다
- PDF 파일은 `pdfs/` 폴더에 저장됩니다
- 벡터 캐시는 `cache/` 폴더에 PDF별로 저장됩니다

## 🐛 문제 해결

### Ollama 연결 오류
```bash
# Ollama 서비스 확인
ollama list

# Ollama 재시작
ollama serve
```

### 모델이 없는 경우
```bash
# 필요한 모델 다운로드
ollama pull llama3
ollama pull mxbai-embed-large
```

### 캐시 문제
- `cache/` 폴더를 삭제하고 다시 처리하면 캐시가 재생성됩니다
- `cache_metadata/pdf_metadata.json` 파일을 삭제하면 메타데이터가 초기화됩니다

## 📚 추가 문서

- [상세 작업 리포트](Report/PDF_RAG_개선_작업_리포트.md)
- [작업 요약](Report/작업_요약.md)

## 🤝 기여

이슈나 개선 사항이 있으면 이슈를 등록하거나 Pull Request를 보내주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 👤 작성자

AI Assistant

---

**버전**: 2.0  
**최종 업데이트**: 2025-12-12
