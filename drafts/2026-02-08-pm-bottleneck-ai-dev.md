# 코드 생성은 빨라졌는데 왜 출시 속도는 그대로일까: 2025 데이터로 본 ‘PM 병목’ 재설계

> 한 줄 요약: AI는 개발자의 **작성 속도**를 끌어올렸고, 이제 팀의 병목은 점점 **의사결정 설계(우선순위/정의/승인 루프)**로 이동하고 있다.

---

## 1) Problem / Context

AI 코딩 도구 확산으로 ‘코드 작성’ 구간은 확실히 빨라졌다. 문제는 제품 출시 리드타임이 같은 비율로 줄지 않는다는 점이다.

- GitHub Octoverse 2025에 따르면, GitHub는 2025년에 역대 최대 수준의 활동량을 기록했다. 월 평균 PR 병합 4,320만(+23% YoY), 연간 커밋 약 10억(+25.1% YoY), 신규 리포지토리 분당 230개 수준이다.
- 같은 보고서에서 AI 관련 오픈소스 활동도 급증했다(LLM SDK 사용 공개 리포지토리 110만+).
- Stack Overflow 2024에서도 AI 도구 사용/사용 계획 응답이 76%로 증가해(전년 70%), 도구 채택은 이미 주류가 됐다.

즉, **입력(코드 생산량)은 증가**했지만, 많은 조직에서 **출력(고객가치 전달 속도)**은 기대치만큼 개선되지 않는다. 여기서 병목은 보통 다음 세 가지로 이동한다.

1. 문제 정의 병목: 무엇을 만들지 늦게 확정됨
2. 우선순위 병목: 스프린트 중간 재정렬 비용 급증
3. 승인/정합성 병목: 보안/컴플라이언스/운영 정렬 대기

---

## 2) Approach / Framework

내가 제안하는 실무 프레임은 간단하다.

## **Flow Triad: Build Speed × Decision Latency × Quality Guardrail**

AI 시대 성과는 ‘개발 속도’ 하나로 결정되지 않는다. 아래 3축을 같이 봐야 한다.

- **Build Speed (개발 속도):** 코드 생성/수정/테스트 자동화 속도
- **Decision Latency (의사결정 지연):** PR 이전/이후의 대기 시간(스펙 확정, 리뷰 승인, 릴리즈 승인)
- **Quality Guardrail (품질 가드레일):** 장애율, 롤백율, 보안 이슈 유입률

핵심은 이것이다: **AI 도입으로 Build Speed가 올라갈수록, Decision Latency를 설계하지 않으면 전체 리드타임은 평평해진다.**

SPACE 프레임워크가 말하듯 생산성은 다차원 측정이 필요하다(활동량 하나만 보면 왜곡된다). 2025 DORA의 AI 보고서도 ‘도구 도입’보다 ‘시스템적 운영 역량’이 성과를 가른다는 점을 강조한다.

---

## 3) Technical / Strategic Depth (Concrete Examples)

### A. 메트릭 설계: “코드량” 대신 “결정-전달 시간” 추적

최소 대시보드(주간):

- Lead Time to Production (commit→prod)
- Spec Freeze to First Merge (요구 확정→첫 병합)
- PR Ready to PR Approved (리뷰 대기시간)
- Change Failure Rate / Rollback Rate

권장 해석:

- 커밋 수↑, PR 수↑인데 Lead Time 변화 없음 → 결정/승인 병목
- Copilot 사용률↑인데 CFR↑ → 가드레일 부재

### B. PM 운영 리디자인: 의사결정 SLA 도입

AI로 개발 처리량이 늘어난 팀에서는 PM·리더 의사결정을 ‘회의’가 아니라 ‘운영 시스템’으로 바꿔야 한다.

예시 SLA:

- P1 이슈 우선순위 결정: 4시간 이내
- 스코프 변경 승인/반려: 1영업일 이내
- 릴리즈 Go/No-Go 기준: 체크리스트 기반 자동 게이팅 + 예외 승인 2시간 이내

효과:

- 개발자 대기시간 감소
- 재작업률 감소
- “빠르게 만들고 늦게 결정” 패턴 제거

### C. 타입 안정성과 에이전트 신뢰성

Octoverse 2025에서 TypeScript가 1위로 올라선 변화는 단순 유행이 아니라 신호다. 팀들은 에이전트/AI-assisted 코딩에서 **타입 안정성 있는 코드베이스가 운영 리스크를 줄인다**는 경험치를 축적 중이다.

실무 적용:

- 신규 서비스: TS/정적 타입 기본
- 레거시 C++ 연동부: 계약(Contract) 우선 정의 (입출력 스키마, 오류코드 정책)
- AI 생성 코드: 린트/타입체크/테스트 통과 시에만 자동 병합 후보

---

## 4) Hiring-manager Takeaway

이 글의 메시지는 “AI를 썼다”가 아니다. **AI 이후의 병목을 제품·조직 관점에서 재설계할 수 있는가**다.

채용 관점에서 강한 신호는 아래다.

- 개발 생산성 지표와 제품 전달 지표를 분리해 측정함
- PM/개발/품질 운영을 SLA로 묶어 리드타임을 줄임
- 도구 도입 성과를 “코드량”이 아닌 “출시 신뢰성”으로 증명함

즉, ‘손 빠른 개발자’보다 **시스템 단위로 throughput을 올리는 PM 성향 엔지니어**가 희소해진다.

---

## 5) Next Experiment (2주 파일럿)

2주만에 검증 가능한 실험:

1. 한 스쿼드 선정 (5~8명)
2. AI 코딩 도구 사용은 유지
3. 의사결정 SLA 3개만 도입 (우선순위/스코프변경/릴리즈예외)
4. 위 4개 지표 주간 측정
5. 회고에서 “가장 오래 기다린 결정” 3개를 제거

성공 기준(예시):

- Lead Time 15%+ 단축
- PR 대기시간 20%+ 단축
- Change Failure Rate 악화 없음

---

## Source pack

1. GitHub Octoverse 2025 (요약 허브)  
   https://octoverse.github.com/
2. GitHub Blog — Octoverse 2025 상세 수치  
   https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/
3. Google Cloud — 2025 DORA State of AI-Assisted Software Development  
   https://cloud.google.com/devops/state-of-devops
4. Microsoft Work Trend Index 2025  
   https://www.microsoft.com/en-us/worklab/work-trend-index/2025-the-year-the-frontier-firm-is-born
5. Stack Overflow Developer Survey 2024 (AI 도구 채택 추세)  
   https://survey.stackoverflow.co/2024/

---

## Fact checks needed (publish 전 확인)

- Octoverse 수치(PR/commit/repo 증가율) 최신 버전과 정확히 일치하는지 재검증
- “TypeScript 1위” 기준 월(2025년 8월)과 지표 정의(사용량/활동량) 확인
- DORA 2025 보고서의 ‘7 capabilities’ 명칭/정의 원문 인용 정밀 확인
- Microsoft WTI 수치(82%, 81%, 53/80, 275 interruptions)가 보고서 본문/주석과 일치하는지 교차검토
- Stack Overflow 2024 수치를 2025/2026 업데이트 데이터로 대체 가능한지 확인

---

## Draft note

- 이 초안은 자동 게시용이 아니다.
- Rocky의 명시적 승인 후에만 문장 톤/사례를 확정하고 퍼블리시 단계로 넘긴다.
