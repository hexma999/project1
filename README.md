1. 👋 프로젝트 소개 (Overview)
**'경수오빠못해조'**는 반려동물(강아지, 고양이, 새, 햄스터 등)을 위한 용품을 판매하고, 반려인들이 소통할 수 있는 공간을 제공합니다.
🛒 쇼핑몰: 카테고리별 상품 조회, 장바구니, 재고 관리 및 결제 시스템
📝 커뮤니티: 사용자 간 자유로운 소통을 위한 게시판 (CRUD)
🤖 AI 챗봇: OpenAI GPT-4.1-mini 기반 CS 자동 응답 챗봇
🔮 상품 추천: 사용자 정보(성별/연령) 기반 머신러닝(Random Forest) 맞춤 상품 추천
🎨 반응형 UI: Glassmorphism 디자인이 적용된 깔끔한 프론트엔드2.

구분,기술 (Technology),설명
Backend,고성능 비동기 웹 프레임워크
Database,관계형 데이터베이스 및 클라우드 스토리지
ORM,Python 객체와 DB 매핑
AI / ML,CS 챗봇 및 상품 추천 알고리즘
Frontend,반응형 디자인 및 템플릿 엔진

📂 디렉토리 구조 (Directory Structure)MVC(Model-View-Controller) 패턴을 기반으로 기능별로 깔끔하게 구조화되어 있습니다.Bashproject1/
├── main.py                  # [Entry] 앱 실행 및 설정 진입점
├── database.py              # DB 연결 엔진 설정
├── dependencies.py          # DB 세션 관리 및 인증 의존성
├── schemas.py               # Pydantic 데이터 검증 모델
│
├── routers/                 # [Controller] URL 라우팅 및 비즈니스 로직
│   ├── auth.py              # 회원가입, 로그인, 정보수정
│   ├── cart.py              # 장바구니 로직
│   ├── orders.py            # 주문 및 결제 처리
│   ├── memos.py             # 게시판 CRUD
│   └── chatbot.py           # AI 챗봇 연결
│
├── data/                    # [Model/DAO] DB 쿼리 집합
│   ├── products.py          # 상품/재고 관리 쿼리
│   ├── orders.py            # 주문 트랜잭션 쿼리
│   └── ...                  # (auth, cart, memos 등)
│
└── templates/               # [View] 사용자 인터페이스 (HTML)
    ├── main.html            # 메인 페이지
    ├── product_detail.html  # 상품 상세 및 리뷰
    ├── mypage.html          # 마이페이지
    └── ...
4. 🚀 핵심 기능 및 로직 (Key Features)
🛒 1. 쇼핑 및 주문 (Shopping & Order)재고 관리: 주문 시 product_data를 통해 실시간 재고를 확인합니다.트랜잭션(Transaction): create_order 함수 내에서 결제 금액 계산, 주문서 생성, 상세 품목 기록, 재고 차감이 하나의 트랜잭션으로 안전하게 처리됩니다.장바구니: 세션 기반이 아닌 DB(carts 테이블)를 사용하여 로그아웃 후에도 장바구니가 유지됩니다.
📝 2. 커뮤니티 게시판 (Community Board)접근 제어: 글 작성/수정/삭제 시 세션 검증을 통해 로그인한 사용자만 접근 가능합니다.CRUD 구현: 본인이 작성한 글인지(user_id 대조) 확인 후 수정/삭제 권한을 부여합니다.편의 기능: '내 글만 보기' 필터 및 제목/내용/작성자 검색 기능을 제공합니다.
🤖 3. AI 챗봇 (AI Chatbot)Role-Playing: 챗봇에게 "쇼핑몰 고객센터 직원"이라는 페르소나를 부여합니다.Context Injection: faq.json에 정의된 배송, 환불 규정 데이터를 프롬프트에 주입하여 쇼핑몰 정책에 맞는 정확한 답변을 제공합니다. (Powered by gpt-4.1-mini)
🔮 4. 상품 추천 시스템 (Recommendation)Machine Learning: Scikit-learn의 RandomForestClassifier를 사용합니다.알고리즘: 사용자의 '성별'과 '연령대' 데이터를 학습하여 가장 선호할 확률이 높은 상품 10개를 예측하여 추천합니다.자동화: schedule 라이브러리를 통해 추천 로직(batch.py)이 주기적으로 실행됩니다. 
💾 5. 데이터베이스 설계 (ERD Summary)
테이블명,역할,주요 관계
Users,회원 정보 저장,-
Products,상품 정보 및 재고,Categories와 N:1
Orders,주문 내역 (영수증),Users와 N:1
Order_Items,주문 상세 품목,"Orders, Products와 연결"
Carts,사용자 장바구니,Users와 1:1
Memo,게시판 게시글,Users와 N:1
Reviews,상품 리뷰,"Products, Users와 N:1"
