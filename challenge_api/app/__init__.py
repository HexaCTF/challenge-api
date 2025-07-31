import sys
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from typing import Type

from challenge_api.app.config import Config
from challenge_api.app.external.database.database import init_db


class FastAPIApp:
    def __init__(self, config_class: Type[Config] = Config):
        self.config = config_class()
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            self._init_db()
            yield
        
        self.app = FastAPI(
            title="Challenge API",
            description="Challenge management API",
            version="2.0.0",
            lifespan=lifespan
        )
        
        self._setup_routers()
        self._setup_middleware()
        self._setup_exception_handlers()
    
    def _init_db(self):
        """DB 초기화"""
        init_db()
    
        
    def _setup_routers(self):
        """Router 등록 (Blueprint 대신)"""
        from challenge_api.app.api.userchallenge import router as userchallenge_router
        
        # API v2 prefix로 라우터 등록
        self.app.include_router(
            userchallenge_router,
            prefix="/api/v2"
        )
    
    def _setup_middleware(self):
        """미들웨어 설정"""
        from fastapi.middleware.cors import CORSMiddleware
        
        # CORS 설정 (필요한 경우)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_exception_handlers(self):
        """Exception handler 설정"""
        from challenge_api.app.api.errors import BaseHttpException
        from fastapi import Request
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        @self.app.exception_handler(BaseHttpException)
        async def handle_http_exception(request: Request, error: BaseHttpException):
            """
            Global error handler for all BaseHttpException instances
            
            Args:
                request (Request): The FastAPI request object
                error (BaseHttpException): The caught exception instance
                
            Returns:
                JSONResponse: Standardized error response
            """
            
            # Create log message with context information
            log_data = {
                'error_type': type(error).__name__,
                'status_code': error.status_code,
                'endpoint': request.url.path,
                'method': request.method,
                'url': str(request.url),
                'client_host': request.client.host if request.client else None,
            }
            
            if error.error_msg:
                log_data['error_msg'] = error.error_msg
            
            # Log the error
            print(f"Error: {error.message}")  # Simple logging for now
            
            response_data = {
                'error': {
                    'message': error.message,
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return JSONResponse(
                status_code=error.status_code,
                content=response_data
            )


def create_app(config_class: Type[Config] = Config) -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    fastapi_app = FastAPIApp(config_class)
    return fastapi_app.app
