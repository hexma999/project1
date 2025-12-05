📘 프로젝트 문서: 경수오빠못해조 (Pet Shop & Community)
1. 프로젝트 개요
프로젝트명: 경수오빠못해조

설명: 반려동물(강아지, 고양이, 조류, 기타 동물) 용품을 판매하는 이커머스 기능과 사용자 간 소통을 위한 자유 게시판(메모) 기능을 결합한 웹 애플리케이션입니다.

주요 기능: 회원가입/로그인, 카테고리별 상품 조회, 상품 상세 및 리뷰 작성, 자유 게시판(CRUD)

2. 활용 기술 (Tech Stack)
Backend
Language: Python 3.12+

Framework: FastAPI (REST API 구축 및 웹 서버 기능)

ORM: SQLAlchemy (데이터베이스 상호작용 추상화)

Security: passlib[bcrypt], python-jose (비밀번호 해싱 및 인증 처리)

Database
RDBMS: MySQL (실제 데이터 저장소)

Hosting: Amazon RDS (AWS 클라우드 데이터베이스 서비스)

Driver: pymysql (Python-MySQL 커넥터)

Frontend
Language: HTML5, CSS3, JavaScript

Templating Engine: Jinja2 (서버 사이드 렌더링)

Framework: Bootstrap 4.3.1 (반응형 디자인 및 UI 컴포넌트)

Library: jQuery, FontAwesome (아이콘)

Infrastructure & Tools
Environment: .env (환경 변수 관리 - python-dotenv)

Server: Uvicorn (ASGI 서버)

3. 파일 구조 (File Structure)
프로젝트는 MVC(Model-View-Controller) 패턴과 유사하게 데이터(Data), 라우터(Router), 템플릿(Templates)으로 구조화되어 있습니다.

Plaintext

project1/
├── main.py                  # [진입점] 앱 초기화, 미들웨어 설정, 메인/상품 라우팅
├── database.py              # DB 연결 설정 (Engine, SessionLocal 생성)
├── dependencies.py          # 의존성 주입 (DB 세션 생성, 비밀번호 해시/검증)
├── schemas.py               # Pydantic 모델 (요청/응답 데이터 검증)
├── .env                     # 환경 변수 (DB URL, Secret Key)
│
├── routers/                 # [Controller] URL 라우팅 및 비즈니스 로직 처리
│   ├── auth.py              # 인증 관련 라우터 (회원가입, 로그인, 로그아웃)
│   └── memos.py             # 게시판 관련 라우터 (CRUD)
│
├── data/                    # [Model/DAO] 데이터베이스 쿼리 함수 집합
│   ├── auth.py              # 사용자(User) 테이블 쿼리
│   ├── memos.py             # 메모(Memo) 테이블 쿼리
│   └── products.py          # 상품(PetItem), 리뷰(Reviews) 테이블 쿼리
│
└── templates/               # [View] 사용자 인터페이스 (HTML)
    ├── home.html            # 로그인/회원가입 페이지
    ├── main.html            # 메인 페이지 (상품 추천, 네비게이션)
    ├── products.html        # 카테고리별 상품 목록 페이지
    ├── product_detail.html  # 상품 상세 및 리뷰 페이지
    └── memos.html           # 자유 게시판 페이지
4. 데이터베이스 설계 (ERD)
Amazon RDS(MySQL)에 구축된 테이블 구조입니다.

1) Users (사용자)
회원 정보를 저장합니다.

Columns: id (PK), username (Unique), email, hashed_password

2) Pet_Item (상품)
판매 물품 정보를 저장합니다.

Columns: id (PK), category (대분류: dog, cat...), sub_category (소분류), name, price, description, detail (HTML), image_url

3) Memo (게시판)
사용자가 작성한 게시글입니다. User와 1:N 관계입니다.

Columns: id (PK), user_id (FK -> Users.id), title, content

4) Reviews (리뷰)
상품에 대한 후기입니다. Product, User와 각각 N:1 관계입니다.

Columns: id (PK), product_id (FK -> Pet_Item.id), user_id (FK -> Users.id), content, created_at

5. 시스템 아키텍처 및 코드 흐름도 (Code Flow)
사용자의 요청이 들어왔을 때 서버 내부에서 처리되는 흐름입니다. **계층형 아키텍처(Layered Architecture)**를 따르고 있습니다.

흐름도 (Flowchart)
코드 스니펫

graph TD
    User((사용자))
    
    subgraph Frontend [Templates (View)]
        HTML[HTML 페이지/JS]
    end

    subgraph Backend [FastAPI Server]
        Main[main.py (App Entry)]
        
        subgraph Routers [API Routes]
            AuthRouter[routers/auth.py]
            MemoRouter[routers/memos.py]
            ProductRoutes[main.py 내 정의]
        end
        
        subgraph DataLayer [Data Access Object]
            DataAuth[data/auth.py]
            DataMemo[data/memos.py]
            DataProd[data/products.py]
        end
        
        Schemas[schemas.py (Validation)]
        DB_Conn[database.py / dependencies.py]
    end

    subgraph Database [Amazon RDS]
        MySQL[(MySQL DB)]
    end

    User -->|HTTP Request| Main
    Main -->|Mount| AuthRouter
    Main -->|Mount| MemoRouter
    
    %% 회원가입/로그인 흐름
    AuthRouter -->|Validate| Schemas
    AuthRouter -->|Call| DataAuth
    DataAuth -->|Query| DB_Conn
    DB_Conn -->|SQL| MySQL
    
    %% 게시판 흐름
    MemoRouter -->|Call| DataMemo
    DataMemo -->|Query| DB_Conn
    
    %% 상품 흐름
    ProductRoutes -->|Call| DataProd
    DataProd -->|Query| DB_Conn

    %% 응답
    MySQL -->|Result| DB_Conn
    DB_Conn -->|Data| Backend
    Backend -->|Render| HTML
    HTML -->|Display| User
주요 로직 상세
초기화 (main.py):

.env 로드 및 DB 엔진/세션 설정.

auth, memos 라우터 등록 (include_router).

정적 템플릿(Jinja2Templates) 설정.

상품 조회 흐름:

요청: GET /products?category=dog&sub=food

처리: main.py의 product_list 함수 실행 -> data/products.py의 get_products_by_category 호출 -> SQL 실행.

응답: 조회된 데이터를 products.html 템플릿에 담아 렌더링.

게시글 작성 흐름:

요청: POST /memos/ (JSON body: title, content)

처리: routers/memos.py -> 세션에서 username 확인 (로그인 체크) -> data/memos.py의 create_memo 호출 -> DB Insert.

응답: 성공 메시지 JSON 반환 (프론트엔드에서 JS로 새로고침 처리).

데이터베이스 연결:

database.py에서 create_engine으로 RDS에 연결.

dependencies.py의 get_db 함수가 요청(Request)마다 DB 세션을 생성하고, 처리가 끝나면 자동으로 닫음(yield 패턴).
