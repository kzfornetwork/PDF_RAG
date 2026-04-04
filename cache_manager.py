"""
캐시 관리 모듈 - PDF별 벡터 캐시 관리
파일 해시 기반으로 각 PDF의 벡터 캐시를 별도 폴더에 저장/관리
"""
import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

import config


class CacheManager:
    """PDF별 벡터 캐시 관리 클래스"""
    
    def __init__(self):
        self.cache_base = config.CACHE_DIR
        self.metadata_file = config.CACHE_METADATA_DIR / "pdf_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """메타데이터 파일 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 메타데이터 로드 실패: {e}")
        return {}
    
    def _save_metadata(self):
        """메타데이터 파일 저장"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 메타데이터 저장 실패: {e}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """파일의 SHA256 해시 계산"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise ValueError(f"파일 해시 계산 실패: {e}")
    
    def get_cache_dir(self, file_hash: str) -> Path:
        """해시에 해당하는 캐시 디렉토리 경로 반환"""
        return self.cache_base / file_hash
    
    def is_cached(self, file_hash: str) -> bool:
        """해당 파일이 캐시되어 있는지 확인"""
        cache_dir = self.get_cache_dir(file_hash)
        return cache_dir.exists() and (cache_dir / "chroma.sqlite3").exists()
    
    def get_pdf_info(self, file_path: str) -> Optional[Dict]:
        """PDF 파일 정보 조회 (해시, 파일명 등)"""
        file_hash = self.calculate_file_hash(file_path)
        if file_hash in self.metadata:
            return self.metadata[file_hash]
        return None
    
    def register_pdf(self, file_path: str, original_filename: str) -> str:
        """PDF 파일 등록 및 해시 반환"""
        file_hash = self.calculate_file_hash(file_path)
        
        # 메타데이터에 등록
        if file_hash not in self.metadata:
            self.metadata[file_hash] = {
                "filename": original_filename,
                "file_path": str(file_path),
                "hash": file_hash,
                "created_at": str(Path(file_path).stat().st_mtime)
            }
            self._save_metadata()
        
        return file_hash
    
    def create_vectorstore(
        self, 
        documents: List[Document], 
        file_hash: str
    ) -> Chroma:
        """벡터 스토어 생성 및 저장"""
        cache_dir = self.get_cache_dir(file_hash)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        embeddings = OllamaEmbeddings(model=config.OLLAMA_EMBEDDING_MODEL)
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=str(cache_dir)
        )
        vectorstore.persist()
        
        print(f"✅ 벡터 캐시 생성 완료: {cache_dir}")
        return vectorstore
    
    def load_vectorstore(self, file_hash: str) -> Optional[Chroma]:
        """기존 벡터 스토어 로드"""
        if not self.is_cached(file_hash):
            return None
        
        cache_dir = self.get_cache_dir(file_hash)
        embeddings = OllamaEmbeddings(model=config.OLLAMA_EMBEDDING_MODEL)
        
        try:
            vectorstore = Chroma(
                persist_directory=str(cache_dir),
                embedding_function=embeddings
            )
            print(f"✅ 기존 벡터 캐시 로드: {cache_dir}")
            return vectorstore
        except Exception as e:
            print(f"⚠️ 벡터 캐시 로드 실패: {e}")
            return None
    
    def get_or_create_vectorstore(
        self, 
        documents: List[Document], 
        file_path: str,
        original_filename: str
    ) -> Tuple[Chroma, str]:
        """벡터 스토어 가져오기 또는 생성하기"""
        file_hash = self.calculate_file_hash(file_path)
        
        # PDF 등록
        self.register_pdf(file_path, original_filename)
        
        # 캐시 확인
        vectorstore = self.load_vectorstore(file_hash)
        
        if vectorstore is None:
            # 새로 생성
            vectorstore = self.create_vectorstore(documents, file_hash)
        else:
            print(f"💾 캐시 재사용: {original_filename}")
        
        return vectorstore, file_hash
    
    def get_processed_pdfs(self) -> List[Dict]:
        """처리된 PDF 목록 반환"""
        pdfs = []
        for file_hash, info in self.metadata.items():
            if self.is_cached(file_hash):
                pdfs.append({
                    "hash": file_hash,
                    "filename": info.get("filename", "Unknown"),
                    "file_path": info.get("file_path", "")
                })
        return pdfs
    
    def delete_cache(self, file_hash: str) -> bool:
        """특정 PDF의 캐시 삭제"""
        cache_dir = self.get_cache_dir(file_hash)
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                if file_hash in self.metadata:
                    del self.metadata[file_hash]
                    self._save_metadata()
                print(f"🗑️ 캐시 삭제 완료: {file_hash}")
                return True
            except Exception as e:
                print(f"⚠️ 캐시 삭제 실패: {e}")
                return False
        return False

