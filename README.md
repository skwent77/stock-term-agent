# stock-term-agent

한국어 주식 용어를 의미 기반으로 검색하고, 검색된 문서를 근거로 AI가 설명하는
투자교육용 RAG 서비스입니다. 답변 화면에 사용한 용어, 유사도, 출처와 데이터
버전을 함께 표시합니다.

## 로컬 웹 실행

Chroma와 웹 애플리케이션을 함께 실행합니다.

```bash
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력
docker compose up --build
```

브라우저에서 `http://localhost:8080`에 접속합니다. 첫 질문에서는 다국어 임베딩
모델 다운로드와 47개 용어 인덱싱 때문에 시간이 더 걸릴 수 있습니다.

## Railway 배포

Railway에서는 Compose 파일을 직접 실행하지 않고 두 서비스를 따로 만듭니다.

1. 이 저장소를 GitHub에 올리고 Railway에서 빈 프로젝트를 만듭니다.
2. Docker Image 서비스 `chroma`를 만들고 이미지에 `chromadb/chroma:1.5.9`를 지정합니다.
3. `chroma` 서비스에 Railway Volume을 `/data` 경로로 연결합니다.
4. 같은 프로젝트에 GitHub 저장소 기반 서비스 `web`을 추가합니다. 루트의
   `Dockerfile`과 `railway.toml`이 자동으로 사용됩니다.
5. `web` 서비스 Variables에 아래 값을 설정합니다.

```text
ANTHROPIC_API_KEY=발급받은_키
CHROMA_HOST=chroma.railway.internal
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_COLLECTION=stock-terms
```

6. `web` 서비스의 Networking에서 공개 도메인을 생성합니다. Chroma에는 공개
   도메인을 만들지 않습니다.
7. `https://생성된주소/health`가 `{"status":"ok"}`를 반환하는지 확인한 뒤 웹에서
   질문을 전송합니다.

Railway의 서비스 이름을 `chroma`가 아닌 다른 이름으로 만들었다면
`CHROMA_HOST`도 `<서비스이름>.railway.internal`로 바꿔야 합니다. 이 서비스의
답변은 투자 권유가 아니라 교육 목적입니다.
